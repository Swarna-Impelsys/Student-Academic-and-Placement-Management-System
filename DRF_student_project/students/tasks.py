
from celery import shared_task
from django.contrib.auth import get_user_model


@shared_task
def add_numbers(a, b):
    return a + b


@shared_task(bind=True, max_retries=3)
def send_account_invitation_task(self, invitation_id):
    from students.models import AccountInvitation
    from students.email_utils import send_account_invitation

    invitation = AccountInvitation.objects.select_related("user").get(
        pk=invitation_id
    )

    invitation.attempts += 1
    invitation.save(update_fields=["attempts", "updated_at"])

    try:
        sent_count = send_account_invitation(invitation.user)

        if sent_count != 1:
            raise RuntimeError(
                "Email backend did not confirm sending the invitation."
            )

    except Exception as exc:
        invitation.last_error = str(exc)[:2000]

        if self.request.retries < self.max_retries:
            invitation.status = "pending"
            invitation.save(
                update_fields=["status", "last_error", "updated_at"]
            )
            raise self.retry(
                exc=exc,
                countdown=2 ** self.request.retries
            )

        invitation.status = "failed"
        invitation.save(
            update_fields=["status", "last_error", "updated_at"]
        )
        raise

    invitation.status = "sent"
    invitation.last_error = ""
    invitation.save(
        update_fields=["status", "last_error", "updated_at"]
    )

    return True


@shared_task(bind=True, max_retries=3)
def send_interview_notification_task(self, interview_id):
    from students.models import Interview
    from students.email_utils import send_interview_notification_email

    try:
        interview = Interview.objects.select_related(
            "application__student",
            "application__job",
        ).get(pk=interview_id)

        sent_count = send_interview_notification_email(interview)

        if sent_count != 1:
            raise RuntimeError(
                "Email backend did not confirm sending the interview email."
            )

        return True

    except Exception as exc:
        if self.request.retries < self.max_retries:
            raise self.retry(
                exc=exc,
                countdown=2 ** self.request.retries,
            )

        raise


@shared_task
def recover_pending_invitations():
    from students.models import AccountInvitation

    pending_ids = list(
        AccountInvitation.objects.filter(
            status="pending"
        ).values_list("id", flat=True)[:100]
    )

    queued_count = 0

    for invitation_id in pending_ids:
        try:
            send_account_invitation_task.delay(invitation_id)
            queued_count += 1
        except Exception:
            import logging
            logging.getLogger(__name__).exception(
                "Could not queue invitation ID %s for recovery",
                invitation_id,
            )

    return queued_count
