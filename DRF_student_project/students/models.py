
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models import Q


class Course(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class TeacherCourseAssignment(models.Model):
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="teacher_course_assignments"
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="teacher_assignments"
    )
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["teacher", "course"],
                name="unique_teacher_course_assignment"
            )
        ]

    def __str__(self):
        return f"{self.teacher.username} - {self.course.name}"


class Subject(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Student(models.Model):

    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("graduated", "Graduated"),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    Name = models.CharField(max_length=100)
    Age = models.IntegerField()
    Email = models.EmailField(unique=True)
    Phone = models.CharField(max_length=15)

    Course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="student"
    )

    Image = models.ImageField(
        upload_to="students/",
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="active"
    )

    subjects = models.ManyToManyField(
        Subject,
        related_name="students",
        blank=True
    )

    skills = models.ManyToManyField(
        "Skill",
        related_name="students",
        blank=True
    )

    address = models.CharField(
        max_length=200,
        null=True,
        blank=True
    )

    date_of_birth = models.DateField(
        null=True,
        blank=True
    )

    def __str__(self):
        return self.Name


class AcademicRecord(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="academic_records"
    )

    semester = models.IntegerField()

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="academic_records"
    )

    marks = models.FloatField()
    attendance = models.FloatField()
    backlog = models.BooleanField(default=False)

    def __str__(self):
        return (
            f"{self.student.Name} - Semester {self.semester} - "
            f"{self.subject.name}"
        )


class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Certification(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="certifications"
    )

    name = models.CharField(max_length=150)
    issuing_organization = models.CharField(max_length=150)
    issue_date = models.DateField()

    expiry_date = models.DateField(
        null=True,
        blank=True
    )

    certificate = models.FileField(
        upload_to="certifications/",
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.student.Name} - {self.name}"


class Company(models.Model):
    name = models.CharField(max_length=150, unique=True)

    description = models.TextField(
        blank=True,
        null=True
    )

    website = models.URLField(
        blank=True,
        null=True
    )

    location = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=15)

    logo = models.ImageField(
        upload_to="companies/",
        blank=True,
        null=True
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class PlacementDrive(models.Model):
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="placement_drives"
    )

    title = models.CharField(max_length=150)

    description = models.TextField(
        blank=True,
        null=True
    )

    drive_date = models.DateField()
    application_start_date = models.DateField()
    application_end_date = models.DateField()
    location = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Job(models.Model):
    placement_drive = models.ForeignKey(
        PlacementDrive,
        on_delete=models.CASCADE,
        related_name="jobs"
    )

    title = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)
    job_type = models.CharField(max_length=50)
    location = models.CharField(max_length=200)

    salary = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    vacancies = models.PositiveIntegerField(default=1)

    minimum_age = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    minimum_marks = models.FloatField(
        null=True,
        blank=True
    )

    minimum_attendance = models.FloatField(
        null=True,
        blank=True
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    required_course = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="jobs"
    )

    required_skills = models.ManyToManyField(
        Skill,
        blank=True,
        related_name="jobs"
    )

    maximum_backlogs = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.placement_drive.title} - {self.title}"


class EligibilityCheck(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="eligibility_checks"
    )

    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name="eligibility_checks"
    )

    # Teacher who performed the eligibility check.
    # Nullable so existing records remain compatible.
    checked_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="eligibility_checks_performed"
    )

    is_eligible = models.BooleanField()
    reason = models.TextField()

    # Fingerprint of the student/job data used during evaluation.
    # The view will calculate and update this value.
    source_fingerprint = models.CharField(
        max_length=64,
        blank=True,
        default=""
    )

    checked_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.Name} - {self.job.title}"


class Application(models.Model):

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("shortlisted", "Shortlisted"),
        ("rejected", "Rejected"),
        ("selected", "Selected"),
    ]

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="applications"
    )

    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name="applications"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "job"],
                name="unique_student_job_application"
            )
        ]

    def __str__(self):
        return f"{self.student.Name} - {self.job.title}"


class Interview(models.Model):

    INTERVIEW_TYPE_CHOICES = [
        ("online", "Online"),
        ("offline", "Offline"),
    ]

    STATUS_CHOICES = [
        ("scheduled", "Scheduled"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
        ("rescheduled", "Rescheduled"),
    ]

    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name="interviews"
    )

    interview_date = models.DateField()
    interview_time = models.TimeField()

    interview_type = models.CharField(
        max_length=20,
        choices=INTERVIEW_TYPE_CHOICES
    )

    location = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    meeting_link = models.URLField(
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="scheduled"
    )

    feedback = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (
            f"{self.application.student.Name} - "
            f"{self.application.job.title}"
        )


class Selection(models.Model):

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("selected", "Selected"),
        ("rejected", "Rejected"),
    ]

    application = models.OneToOneField(
        Application,
        on_delete=models.CASCADE,
        related_name="selection"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    offer_date = models.DateField(null=True, blank=True)
    joining_date = models.DateField(null=True, blank=True)

    package = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    remarks = models.TextField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.application.student.Name} - {self.status}"


class Notification(models.Model):

    NOTIFICATION_TYPE_CHOICES = [
        ("interview", "Interview"),
        ("selection", "Selection"),
        ("application", "Application"),
        ("job", "Job Opportunity"),
        ("general", "General"),
        ("profile_correction", "Profile Correction"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications"
    )

    job = models.ForeignKey(
        Job,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications"
    )

    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPE_CHOICES
    )

    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    interview = models.ForeignKey(
        "Interview",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "interview"],
                condition=models.Q(
                    interview__isnull=False,
                    notification_type="interview"
                ),
                name="unique_interview_notification_per_user",
            )
        ]

    def __str__(self):
        return f"{self.user.username} - {self.notification_type}"

class JobInterestResponse(models.Model):

    RESPONSE_CHOICES = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("declined", "Declined"),
    ]

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="job_interest_responses"
    )

    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name="student_interest_responses"
    )

    # Registration Officer who sent the eligibility notification.
    sent_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="job_interest_notifications_sent"
    )

    # Notification associated with the latest sent notification.
    notification = models.ForeignKey(
        Notification,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="job_interest_responses"
    )

    response = models.CharField(
        max_length=20,
        choices=RESPONSE_CHOICES,
        default="pending"
    )

    decline_reason = models.TextField(
        blank=True,
        default=""
    )

    sent_at = models.DateTimeField(
        auto_now_add=True
    )

    responded_at = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "job"],
                name="unique_student_job_interest_response"
            )
        ]

    def __str__(self):
        return (
            f"{self.student.Name} - {self.job.title} - "
            f"{self.response}"
        )


class InterviewShortlistUpload(models.Model):

    STATUS_CHOICES = [
        ("uploaded", "Uploaded"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("completed_with_errors", "Completed With Errors"),
        ("failed", "Failed"),
    ]

    file = models.FileField(
        upload_to="placement_imports/interview_shortlists/"
    )

    job = models.ForeignKey(
    Job,
    on_delete=models.PROTECT,
    related_name="interview_shortlist_uploads",
    null=True,
    blank=True
    )

    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="interview_shortlist_uploads"
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="uploaded"
    )

    total_rows = models.PositiveIntegerField(default=0)
    matched_rows = models.PositiveIntegerField(default=0)
    failed_rows = models.PositiveIntegerField(default=0)

    # Stores row-level processing results and validation errors.
    processing_summary = models.JSONField(default=dict, blank=True)

    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Interview shortlist upload #{self.pk}"


class SelectionResultUpload(models.Model):

    STATUS_CHOICES = [
        ("uploaded", "Uploaded"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("completed_with_errors", "Completed With Errors"),
        ("failed", "Failed"),
    ]

    file = models.FileField(
        upload_to="placement_imports/selection_results/"
    )

    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="selection_result_uploads"
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="uploaded"
    )

    total_rows = models.PositiveIntegerField(default=0)
    matched_rows = models.PositiveIntegerField(default=0)
    failed_rows = models.PositiveIntegerField(default=0)

    # Admin must explicitly confirm this before non-listed
    # applications can be marked as not selected.
    is_complete_final_list = models.BooleanField(default=False)

    processing_summary = models.JSONField(default=dict, blank=True)

    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Selection result upload #{self.pk}"


class AuditLog(models.Model):

    ACTION_CHOICES = [
        ("CREATE", "Create"),
        ("UPDATE", "Update"),
        ("DELETE", "Delete"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs"
    )

    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)
    record_id = models.CharField(max_length=100)
    description = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.action} - {self.model_name}"


class CourseSubject(models.Model):

    CATEGORY_CHOICES = [
        ("compulsory", "Compulsory"),
        ("optional", "Optional"),
        ("elective", "Additional Elective"),
    ]

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="course_subjects"
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="course_assignments"
    )

    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["course", "subject"],
                name="unique_subject_per_course"
            )
        ]

    def __str__(self):
        return f"{self.course.name} - {self.subject.name} ({self.category})"


class CourseSelectionRule(models.Model):

    course = models.OneToOneField(
        Course,
        on_delete=models.CASCADE,
        related_name="selection_rule"
    )

    optional_subject_count = models.PositiveIntegerField(default=2)
    elective_subject_count = models.PositiveIntegerField(default=1)
    selection_deadline = models.DateTimeField()
    is_selection_open = models.BooleanField(default=True)

    def __str__(self):
        return f"Selection rules - {self.course.name}"


class StudentSubjectSelection(models.Model):

    student = models.OneToOneField(
        Student,
        on_delete=models.CASCADE,
        related_name="subject_selection"
    )

    selected_subjects = models.ManyToManyField(
        CourseSubject,
        blank=True,
        related_name="student_selections"
    )

    submitted_at = models.DateTimeField(null=True, blank=True)
    is_reopened = models.BooleanField(default=False)

    def __str__(self):
        return f"Subject selection - {self.student.Name}"


class SubjectSelectionAuditLog(models.Model):

    ACTION_CHOICES = [
        ("REOPEN", "Reopen Selection"),
        ("CLOSE", "Close Selection"),
        ("UPDATE", "Update Selection"),
    ]

    student_selection = models.ForeignKey(
        StudentSubjectSelection,
        on_delete=models.CASCADE,
        related_name="audit_logs"
    )

    admin_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="subject_selection_audit_logs"
    )

    action = models.CharField(
        max_length=10,
        choices=ACTION_CHOICES
    )

    reason = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (
            f"{self.student_selection.student.Name} - "
            f"{self.action} - {self.timestamp}"
        )


class AccountInvitation(models.Model):

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("sent", "Sent"),
        ("failed", "Failed"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="account_invitations",
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="pending",
    )

    attempts = models.PositiveIntegerField(default=0)
    last_error = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.status}"


class ArchivedUser(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="archive_record",
    )

    archived_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="archived_users",
    )

    reason = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )

    archived_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - Archived"


class StudentSkill(models.Model):

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="personal_skills"
    )

    name = models.CharField(max_length=100)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "name"],
                name="unique_student_personal_skill"
            )
        ]

    def __str__(self):
        return f"{self.student.Name} - {self.name}"


class ProfileCorrectionRequest(models.Model):

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("under_review", "Under Review"),
        ("more_evidence_required", "More Evidence Required"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    FIELD_CHOICES = [
        ("name", "Name"),
        ("first_name", "First Name"),
        ("last_name", "Last Name"),
        ("date_of_birth", "Date of Birth"),
        ("address", "Address"),
        ("phone", "Phone"),
        ("email", "Email"),
        ("photo", "Photo"),
    ]

    student = models.ForeignKey(
        "Student",
        on_delete=models.CASCADE,
        related_name="profile_correction_requests",
        null=True,
        blank=True,
    )

    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="teacher_profile_correction_requests",
        null=True,
        blank=True,
    )

    field_name = models.CharField(
        max_length=30,
        choices=FIELD_CHOICES,
        default="address",
    )

    old_value = models.TextField(blank=True, default="")
    requested_value = models.TextField(blank=True, default="")

    requested_photo = models.ImageField(
        upload_to="profile_corrections/photos/",
        null=True,
        blank=True,
    )

    reason = models.TextField(blank=True, default="")

    requested_address = models.CharField(
        max_length=200,
        blank=True,
        default="",
    )

    requested_date_of_birth = models.DateField(
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="pending",
    )

    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_profile_corrections",
    )

    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, default="")
    decision_note = models.TextField(blank=True, default="")

    def clean(self):
        super().clean()

        # Exactly one target must be selected:
        # either a Student or a Teacher.
        if bool(self.student_id) == bool(self.teacher_id):
            raise ValidationError(
                "A profile correction request must belong to "
                "either one Student or one Teacher, not both."
            )

    def __str__(self):
        target = self.student or self.teacher
        return f"{target} - Profile Correction ({self.status})"


class CorrectionDocument(models.Model):

    class OCRResult(models.TextChoices):
        PENDING = "pending", "Pending"
        MATCH = "match", "Match"
        MISMATCH = "mismatch", "Mismatch"
        UNABLE = "unable_to_verify", "Unable to Verify"

    correction_request = models.ForeignKey(
        ProfileCorrectionRequest,
        on_delete=models.CASCADE,
        related_name="documents",
    )

    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="uploaded_correction_documents",
    )

    document_type = models.CharField(max_length=100)

    file = models.FileField(
        upload_to="profile_corrections/evidence/"
    )

    ocr_text = models.TextField(blank=True, default="")

    ocr_result = models.CharField(
        max_length=30,
        choices=OCRResult.choices,
        default=OCRResult.PENDING,
    )

    ocr_warning = models.TextField(blank=True, default="")
    reviewer_note = models.TextField(blank=True, default="")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (
            f"Evidence for correction request "
            f"#{self.correction_request_id}"
        )
