
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


def send_account_invitation(user):
    # Create a secure, time-limited password setup token.
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    # Build the React password setup URL.
    frontend_url = getattr(
        settings,
        "FRONTEND_URL",
        "http://localhost:5173",
    ).rstrip("/")

    setup_url = (
        f"{frontend_url}/set-password/"
        f"?uid={uid}&token={token}"
    )

    subject = "Set up your Student Management System account"

    message = (
        f"Hello {user.username},\n\n"
        "Your account has been created.\n"
        "Use the link below to set your password:\n\n"
        f"{setup_url}\n\n"
        "This link is time-limited. If you did not expect "
        "this invitation, please contact your administrator."
    )

    return send_mail(
        subject=subject,
        message=message,
        from_email=None,
        recipient_list=[user.email],
        fail_silently=False,
    )


def send_interview_notification_email(interview):
    application = interview.application
    student = application.student

    if not student.Email:
        raise ValueError("Student email address is missing.")

    subject = f"Interview Scheduled - {application.job.title}"

    interview_mode = interview.interview_type.title()

    if interview.interview_type == "online":
        interview_details = (
            f"Meeting Link: {interview.meeting_link}"
        )
    else:
        interview_details = (
            f"Location: {interview.location}"
        )

    message = (
        f"Hello {student.Name},\n\n"
        f"You have been shortlisted for an interview.\n\n"
        f"Company/Job: {application.job.title}\n"
        f"Interview Date: {interview.interview_date}\n"
        f"Interview Time: {interview.interview_time}\n"
        f"Interview Type: {interview_mode}\n"
        f"{interview_details}\n\n"
        "Please be available at the scheduled time.\n\n"
        "Regards,\n"
        "Placement Team"
    )

    return send_mail(
        subject=subject,
        message=message,
        from_email=None,
        recipient_list=[student.Email],
        fail_silently=False,
    )
