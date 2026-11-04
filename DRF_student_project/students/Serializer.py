
from .models import (
    Application,
    Student,
    Course,
    Subject,
    AcademicRecord,
    Skill,
    Certification,
    Company,
    EligibilityCheck,
    Job,
    PlacementDrive,
    Interview,
    Selection,
    Notification,
    AuditLog,
    CourseSubject,
    CourseSelectionRule,
    StudentSubjectSelection,
    SubjectSelectionAuditLog,
    TeacherCourseAssignment,
    StudentSkill,
    ProfileCorrectionRequest,
    CorrectionDocument,
    JobInterestResponse,
    InterviewShortlistUpload,
    SelectionResultUpload,
)

from rest_framework import serializers
from django.utils import timezone


# ============================================================
# SUBJECT SERIALIZER
# ============================================================

class SubjectSerializer(serializers.ModelSerializer):

    class Meta:
        model = Subject
        fields = ["id", "name"]

    def validate_name(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Subject name cannot be empty."
            )

        existing_subjects = Subject.objects.filter(
            name__iexact=value
        )

        if self.instance:
            existing_subjects = existing_subjects.exclude(
                pk=self.instance.pk
            )

        if existing_subjects.exists():
            raise serializers.ValidationError(
                "A subject with this name already exists."
            )

        return value


# ============================================================
# SKILL SERIALIZER
# ============================================================

class SkillSerializer(serializers.ModelSerializer):

    class Meta:
        model = Skill
        fields = ["id", "name"]

    def validate_name(self, value):
        value = value.strip()

        if len(value) < 2:
            raise serializers.ValidationError(
                "Skill name must be at least 2 characters."
            )

        return value


# ============================================================
# CERTIFICATION SERIALIZER
# ============================================================

class CertificationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Certification
        fields = [
            "id",
            "student",
            "name",
            "issuing_organization",
            "issue_date",
            "expiry_date",
            "certificate",
        ]

        read_only_fields = ["id"]

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get("request")

        if request and request.user.is_authenticated:
            is_admin = (
                request.user.is_superuser
                or request.user.groups.filter(
                    name="Admin"
                ).exists()
            )

            if not is_admin:
                fields["student"].read_only = True

        return fields

    def validate_name(self, value):
        value = value.strip()

        if len(value) < 3:
            raise serializers.ValidationError(
                "Certification name must be at least 3 characters."
            )

        return value

    def validate_issuing_organization(self, value):
        value = value.strip()

        if len(value) < 2:
            raise serializers.ValidationError(
                "Issuing organization must be at least 2 characters."
            )

        return value

    def validate(self, attrs):
        issue_date = attrs.get(
            "issue_date",
            getattr(self.instance, "issue_date", None)
        )

        expiry_date = attrs.get(
            "expiry_date",
            getattr(self.instance, "expiry_date", None)
        )

        if issue_date and expiry_date and expiry_date < issue_date:
            raise serializers.ValidationError({
                "expiry_date": (
                    "Expiry date cannot be before issue date."
                )
            })

        return attrs


# ============================================================
# STUDENT SERIALIZER
# ============================================================

class StudentSerializer(serializers.ModelSerializer):

    status_display = serializers.CharField(
        source="get_status_display",
        read_only=True
    )

    course_name = serializers.CharField(
        source="Course.name",
        read_only=True
    )

    subjects = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Subject.objects.all(),
        required=False
    )

    subject_details = SubjectSerializer(
        source="subjects",
        many=True,
        read_only=True
    )

    skills = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Skill.objects.all(),
        required=False
    )

    skill_details = SkillSerializer(
        source="skills",
        many=True,
        read_only=True
    )

    certifications = CertificationSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        model = Student

        fields = [
            "id",
            "Name",
            "Age",
            "address",
            "date_of_birth",
            "Email",
            "Phone",
            "Course",
            "course_name",
            "Image",
            "status",
            "status_display",
            "subjects",
            "skills",
            "subject_details",
            "skill_details",
            "certifications",
        ]

    def validate_Name(self, value):
        value = value.strip()

        if len(value) < 3:
            raise serializers.ValidationError(
                "Name must be at least 3 characters."
            )

        return value

    def validate_Age(self, value):
        if value <= 18:
            raise serializers.ValidationError(
                "Age must be above 18."
            )

        return value

    def validate_Phone(self, value):
        value = str(value).strip()

        if len(value) != 10 or not value.isdigit():
            raise serializers.ValidationError(
                "Phone number must contain exactly 10 digits."
            )

        return value

    def validate(self, attrs):
        age = attrs.get(
            "Age",
            getattr(self.instance, "Age", None)
        )

        course = attrs.get(
            "Course",
            getattr(self.instance, "Course", None)
        )

        restricted_courses = ["CEBA", "HEBA"]

        if (
            age is not None
            and course is not None
            and age < 18
            and course.name in restricted_courses
        ):
            raise serializers.ValidationError(
                "Students below 18 cannot select this course."
            )

        return attrs


# ============================================================
# COURSE SERIALIZER
# ============================================================

class CourseSerializer(serializers.ModelSerializer):

    student = StudentSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        model = Course
        fields = [
            "id",
            "name",
            "student",
        ]


# ============================================================
# TEACHER COURSE ASSIGNMENT SERIALIZER
# ============================================================

class TeacherCourseAssignmentSerializer(serializers.ModelSerializer):

    teacher_name = serializers.CharField(
        source="teacher.username",
        read_only=True
    )

    course_name = serializers.CharField(
        source="course.name",
        read_only=True
    )

    class Meta:
        model = TeacherCourseAssignment

        fields = [
            "id",
            "teacher",
            "teacher_name",
            "course",
            "course_name",
            "assigned_at",
        ]

        read_only_fields = [
            "id",
            "assigned_at",
        ]


# ============================================================
# ACADEMIC RECORD SERIALIZER
# ============================================================


class AcademicRecordSerializer(serializers.ModelSerializer):

    student_name = serializers.CharField(
        source="student.Name",
        read_only=True
    )

    course_name = serializers.CharField(
        source="student.Course.name",
        read_only=True
    )

    subject_name = serializers.CharField(
        source="subject.name",
        read_only=True
    )

    class Meta:
        model = AcademicRecord

        fields = [
            "id",
            "student",
            "student_name",
            "course_name",
            "semester",
            "subject",
            "subject_name",
            "marks",
            "attendance",
            "backlog",
        ]

    def get_fields(self):
        fields = super().get_fields()

        request = self.context.get("request")

        if request and request.user.groups.filter(
            name="Student"
        ).exists():
            fields.pop("student_name", None)
            fields.pop("course_name", None)

        return fields

    def validate(self, attrs):
        request = self.context.get("request")

        if (
            request
            and request.user.groups.filter(name="Teacher").exists()
        ):
            if set(request.data.keys()) != {"attendance"}:
                raise serializers.ValidationError(
                    "Teachers can update attendance only."
                )

        return attrs

    def validate_marks(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError(
                "Marks must be between 0 and 100."
            )

        return value

    def validate_attendance(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError(
                "Attendance must be between 0 and 100."
            )

        return value

    def validate_semester(self, value):
        if value < 1:
            raise serializers.ValidationError(
                "Semester must be at least 1."
            )

        return value


# ============================================================
# COMPANY SERIALIZER
# ============================================================

class CompanySerializer(serializers.ModelSerializer):

    class Meta:
        model = Company

        fields = [
            "id",
            "name",
            "description",
            "website",
            "location",
            "contact_person",
            "contact_email",
            "contact_phone",
            "logo",
            "is_active",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
        ]

    def validate_name(self, value):
        value = value.strip()

        if len(value) < 2:
            raise serializers.ValidationError(
                "Company name must be at least 2 characters."
            )

        return value

    def validate_contact_phone(self, value):
        value = str(value).strip()

        if not value.isdigit():
            raise serializers.ValidationError(
                "Phone number must contain only digits."
            )

        if len(value) < 10 or len(value) > 15:
            raise serializers.ValidationError(
                "Phone number must be between 10 and 15 digits."
            )

        return value

    def validate(self, attrs):
        website = attrs.get("website")

        if website and not str(website).startswith(
            ("http://", "https://")
        ):
            raise serializers.ValidationError(
                "Website must start with http:// or https://."
            )

        return attrs


# ============================================================
# ELIGIBILITY CHECK SERIALIZER
# ============================================================

class EligibilityCheckSerializer(serializers.ModelSerializer):

    checked_by_name = serializers.CharField(
        source="checked_by.username",
        read_only=True,
        allow_null=True
    )

    class Meta:
        model = EligibilityCheck

        fields = [
            "id",
            "student",
            "job",
            "checked_by",
            "checked_by_name",
            "is_eligible",
            "reason",
            "source_fingerprint",
            "checked_at",
        ]

        read_only_fields = [
            "id",
            "checked_by",
            "checked_by_name",
            "is_eligible",
            "reason",
            "source_fingerprint",
            "checked_at",
        ]


# ============================================================
# JOB SERIALIZER
# ============================================================


class JobSerializer(serializers.ModelSerializer):
    required_skills = serializers.ListField(
        child=serializers.CharField(max_length=100),
        write_only=True,
        required=False
    )

    required_skills_details = serializers.SerializerMethodField()

    class Meta:
        model = Job

        fields = [
            "id",
            "placement_drive",
            "title",
            "description",
            "job_type",
            "location",
            "salary",
            "vacancies",
            "minimum_age",
            "minimum_marks",
            "minimum_attendance",
            "required_course",
            "required_skills",
            "required_skills_details",
            "maximum_backlogs",
            "is_active",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
            "required_skills_details",
        ]

    def get_required_skills_details(self, obj):
        return [
            {"id": skill.id, "name": skill.name}
            for skill in obj.required_skills.all()
        ]

    def validate_required_skills(self, value):
        cleaned_skills = []
        seen = set()

        for skill_name in value:
            skill_name = skill_name.strip()

            if not skill_name:
                raise serializers.ValidationError(
                    "Skill names cannot be empty."
                )

            normalized_name = skill_name.casefold()

            if normalized_name not in seen:
                cleaned_skills.append(skill_name)
                seen.add(normalized_name)

        return cleaned_skills

    def create(self, validated_data):
        skill_names = validated_data.pop("required_skills", [])

        job = Job.objects.create(**validated_data)

        skill_objects = []

        for skill_name in skill_names:
            skill, created = Skill.objects.get_or_create(
                name__iexact=skill_name,
                defaults={"name": skill_name}
            )
            skill_objects.append(skill)

        job.required_skills.set(skill_objects)

        return job

    def update(self, instance, validated_data):
        skill_names = validated_data.pop("required_skills", None)

        for field, value in validated_data.items():
            setattr(instance, field, value)

        instance.save()

        if skill_names is not None:
            skill_objects = []

            for skill_name in skill_names:
                skill, created = Skill.objects.get_or_create(
                    name__iexact=skill_name,
                    defaults={"name": skill_name}
                )
                skill_objects.append(skill)

            instance.required_skills.set(skill_objects)

        return instance

    def validate_title(self, value):
        value = value.strip()

        if len(value) < 3:
            raise serializers.ValidationError(
                "Job title must be at least 3 characters."
            )

        return value

    def validate_salary(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Salary must be greater than 0."
            )

        return value

    def validate_vacancies(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Vacancies must be greater than 0."
            )

        return value

    def validate_minimum_age(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError(
                "Minimum age must be greater than 0."
            )

        return value

    def validate_minimum_marks(self, value):
        if value is not None and (value < 0 or value > 100):
            raise serializers.ValidationError(
                "Minimum marks must be between 0 and 100."
            )

        return value

    def validate_minimum_attendance(self, value):
        if value is not None and (
            value < 0 or value > 100
        ):
            raise serializers.ValidationError(
                "Minimum attendance must be between 0 and 100."
            )

        return value

    def validate_maximum_backlogs(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "Maximum backlogs cannot be negative."
            )

        return value



# ============================================================
# PLACEMENT DRIVE SERIALIZER
# ============================================================

class PlacementDriveSerializer(serializers.ModelSerializer):

    class Meta:
        model = PlacementDrive

        fields = [
            "id",
            "company",
            "title",
            "description",
            "drive_date",
            "application_start_date",
            "application_end_date",
            "location",
            "is_active",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
        ]

    def validate(self, attrs):
        start_date = attrs.get(
            "application_start_date",
            getattr(
                self.instance,
                "application_start_date",
                None
            )
        )

        end_date = attrs.get(
            "application_end_date",
            getattr(
                self.instance,
                "application_end_date",
                None
            )
        )

        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError({
                "application_end_date": (
                    "Application end date cannot be before "
                    "the start date."
                )
            })

        return attrs


# ============================================================
# APPLICATION SERIALIZER
# ============================================================

class ApplicationSerializer(serializers.ModelSerializer):

    student_name = serializers.CharField(
        source="student.Name",
        read_only=True
    )

    student_email = serializers.EmailField(
        source="student.Email",
        read_only=True
    )

    course_name = serializers.CharField(
        source="student.Course.name",
        read_only=True
    )

    class Meta:
        model = Application

        fields = [
            "id",
            "student",
            "student_name",
            "student_email",
            "course_name",
            "job",
            "status",
            "applied_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "status",
            "applied_at",
            "updated_at",
        ]

    def validate(self, data):
        student = data.get(
            "student",
            self.instance.student if self.instance else None
        )

        job = data.get(
            "job",
            self.instance.job if self.instance else None
        )

        if student and job:
            existing = Application.objects.filter(
                student=student,
                job=job
            )

            if self.instance:
                existing = existing.exclude(
                    pk=self.instance.pk
                )

            if existing.exists():
                raise serializers.ValidationError(
                    "Student has already applied for this job."
                )

        return data


# ============================================================
# INTERVIEW SERIALIZER
# ============================================================

class InterviewSerializer(serializers.ModelSerializer):

    class Meta:
        model = Interview

        fields = [
            "id",
            "application",
            "interview_date",
            "interview_time",
            "interview_type",
            "location",
            "meeting_link",
            "status",
            "feedback",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
        ]

    def validate(self, attrs):
        interview_type = attrs.get(
            "interview_type",
            getattr(
                self.instance,
                "interview_type",
                None
            )
        )

        location = attrs.get(
            "location",
            getattr(self.instance, "location", None)
        )

        meeting_link = attrs.get(
            "meeting_link",
            getattr(self.instance, "meeting_link", None)
        )

        if interview_type == "online" and not meeting_link:
            raise serializers.ValidationError({
                "meeting_link": (
                    "Meeting link is required for online interviews."
                )
            })

        if interview_type == "offline" and not location:
            raise serializers.ValidationError({
                "location": (
                    "Location is required for offline interviews."
                )
            })

        return attrs


# ============================================================
# SELECTION SERIALIZER
# ============================================================

class SelectionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Selection

        fields = [
            "id",
            "application",
            "status",
            "offer_date",
            "joining_date",
            "package",
            "remarks",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
        ]

    def validate(self, data):
        status_value = data.get(
            "status",
            getattr(self.instance, "status", "pending")
        )

        offer_date = data.get(
            "offer_date",
            getattr(self.instance, "offer_date", None)
        )

        joining_date = data.get(
            "joining_date",
            getattr(self.instance, "joining_date", None)
        )

        package = data.get(
            "package",
            getattr(self.instance, "package", None)
        )

        if status_value == "selected":
            if offer_date is None:
                raise serializers.ValidationError(
                    "Offer date is required for selected candidates."
                )

            if joining_date is None:
                raise serializers.ValidationError(
                    "Joining date is required for selected candidates."
                )

            if package is None:
                raise serializers.ValidationError(
                    "Package is required for selected candidates."
                )

        elif status_value == "rejected":
            if offer_date is not None or joining_date is not None or package is not None:
                raise serializers.ValidationError(
                    "Rejected candidates cannot have offer details."
                )

        elif status_value == "pending":
            if offer_date is not None or joining_date is not None or package is not None:
                raise serializers.ValidationError(
                    "Pending candidates cannot have offer details."
                )

        return data

    def validate_package(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError(
                "Package must be greater than 0."
            )

        return value


# ============================================================
# NOTIFICATION SERIALIZER
# ============================================================



class NotificationSerializer(serializers.ModelSerializer):
    job_title = serializers.SerializerMethodField()
    job_description = serializers.SerializerMethodField()

    company_name = serializers.SerializerMethodField()
    company_website = serializers.SerializerMethodField()

    drive_title = serializers.SerializerMethodField()

    job_type = serializers.SerializerMethodField()
    job_location = serializers.SerializerMethodField()
    job_salary = serializers.SerializerMethodField()
    job_vacancies = serializers.SerializerMethodField()

    required_skills = serializers.SerializerMethodField()
    application_end_date = serializers.SerializerMethodField()

    interview_date = serializers.SerializerMethodField()
    interview_time = serializers.SerializerMethodField()
    interview_type = serializers.SerializerMethodField()
    interview_location = serializers.SerializerMethodField()
    meeting_link = serializers.SerializerMethodField()
    interview_status = serializers.SerializerMethodField()

    
    def get_job_title(self, obj):
        return obj.job.title if obj.job else None

    def get_job_description(self, obj):
        return obj.job.description if obj.job else None

    def get_company_name(self, obj):
        if obj.job and obj.job.placement_drive:
            return obj.job.placement_drive.company.name
        return None

    def get_company_website(self, obj):
        if obj.job and obj.job.placement_drive:
            return obj.job.placement_drive.company.website
        return None

    def get_drive_title(self, obj):
        if obj.job and obj.job.placement_drive:
            return obj.job.placement_drive.title
        return None

    def get_job_type(self, obj):
        return obj.job.job_type if obj.job else None

    def get_job_location(self, obj):
        return obj.job.location if obj.job else None

    def get_job_salary(self, obj):
        return obj.job.salary if obj.job else None

    def get_job_vacancies(self, obj):
        return obj.job.vacancies if obj.job else None

    def get_required_skills(self, obj):
        if obj.job:
            return list(
                obj.job.required_skills.values_list("name", flat=True)
            )
        return []

    def get_application_end_date(self, obj):
        if obj.job and obj.job.placement_drive:
            return obj.job.placement_drive.application_end_date
        return None

    def get_interview_date(self, obj):
        return obj.interview.interview_date if obj.interview else None

    def get_interview_time(self, obj):
        return obj.interview.interview_time if obj.interview else None
    
    def get_interview_type(self, obj):
        return obj.interview.interview_type if obj.interview else None
    
    def get_interview_location(self, obj):
        return obj.interview.location if obj.interview else None
    
    def get_meeting_link(self, obj):
        return obj.interview.meeting_link if obj.interview else None
    
    def get_interview_status(self, obj):
        return obj.interview.status if obj.interview else None

    class Meta:
        model = Notification

        fields = [
            "id",
            "user",
            "job",
            "job_title",
            "job_description",
            "company_name",
            "company_website",
            "drive_title",
            "job_type",
            "job_location",
            "job_salary",
            "job_vacancies",
            "required_skills",
            "application_end_date",
            "interview_date",
            "interview_time",
            "interview_type",
            "interview_location",
            "meeting_link",
"interview_status",
            "notification_type",
            "message",
            "is_read",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "user",
            "job_title",
            "job_description",
            "company_name",
            "company_website",
            "drive_title",
            "job_type",
            "job_location",
            "job_salary",
            "job_vacancies",
            "required_skills",
            "application_end_date",
            "interview_date",
            "interview_time",
            "interview_type",
            "interview_location",
            "meeting_link",
            "interview_status",
            "created_at",
        ]


# ============================================================
# JOB INTEREST RESPONSE SERIALIZER
# ============================================================

class JobInterestResponseSerializer(serializers.ModelSerializer):

    student_name = serializers.CharField(
        source="student.Name",
        read_only=True
    )

    job_title = serializers.CharField(
        source="job.title",
        read_only=True
    )

    course_name = serializers.CharField(
        source="student.Course.name",
        read_only=True
    )

    sent_by_name = serializers.CharField(
        source="sent_by.username",
        read_only=True,
        allow_null=True
    )

    class Meta:
        model = JobInterestResponse

        fields = [
            "id",
            "student",
            "student_name",
            "course_name",
            "job",
            "job_title",
            "sent_by",
            "sent_by_name",
            "notification",
            "response",
            "decline_reason",
            "sent_at",
            "responded_at",
        ]

        read_only_fields = [
            "id",
            "student_name",
            "course_name",
            "job_title",
            "sent_by",
            "sent_by_name",
            "notification",
            "sent_at",
            "responded_at",
        ]

    def validate(self, attrs):
        response = attrs.get(
            "response",
            getattr(self.instance, "response", None)
        )

        decline_reason = attrs.get(
            "decline_reason",
            getattr(self.instance, "decline_reason", "") or ""
        )

        if response == "declined" and not decline_reason.strip():
            raise serializers.ValidationError({
                "decline_reason": (
                    "Please provide a reason for declining the job."
                )
            })

        return attrs


# ============================================================
# EXCEL UPLOAD VALIDATION
# ============================================================

class ExcelUploadValidationMixin:

    def validate_file(self, value):
        filename = value.name.lower()

        if not filename.endswith((".xlsx", ".xls")):
            raise serializers.ValidationError(
                "Only Excel files (.xlsx and .xls) are allowed."
            )

        return value


# ============================================================
# INTERVIEW SHORTLIST EXCEL UPLOAD SERIALIZER
# ============================================================

class InterviewShortlistUploadSerializer(
    ExcelUploadValidationMixin,
    serializers.ModelSerializer
):

    uploaded_by_name = serializers.CharField(
        source="uploaded_by.username",
        read_only=True,
        allow_null=True
    )

    class Meta:
        model = InterviewShortlistUpload

        fields = [
            "id",
            "file",
             "job",
            "uploaded_by",
            "uploaded_by_name",
            "status",
            "total_rows",
            "matched_rows",
            "failed_rows",
            "processing_summary",
            "uploaded_at",
            "processed_at",
        ]

        read_only_fields = [
            "id",
            "uploaded_by",
            "uploaded_by_name",
            "status",
            "total_rows",
            "matched_rows",
            "failed_rows",
            "processing_summary",
            "uploaded_at",
            "processed_at",
        ]


# ============================================================
# SELECTION RESULT EXCEL UPLOAD SERIALIZER
# ============================================================

class SelectionResultUploadSerializer(
    ExcelUploadValidationMixin,
    serializers.ModelSerializer
):

    uploaded_by_name = serializers.CharField(
        source="uploaded_by.username",
        read_only=True,
        allow_null=True
    )

    class Meta:
        model = SelectionResultUpload

        fields = [
            "id",
            "file",
            "uploaded_by",
            "uploaded_by_name",
            "status",
            "total_rows",
            "matched_rows",
            "failed_rows",
            "is_complete_final_list",
            "processing_summary",
            "uploaded_at",
            "processed_at",
        ]

        read_only_fields = [
            "id",
            "uploaded_by",
            "uploaded_by_name",
            "status",
            "total_rows",
            "matched_rows",
            "failed_rows",
            "processing_summary",
            "uploaded_at",
            "processed_at",
        ]


# ============================================================
# AUDIT LOG SERIALIZER
# ============================================================

class AuditLogSerializer(serializers.ModelSerializer):

    class Meta:
        model = AuditLog
        fields = "__all__"

        read_only_fields = [
            "user",
            "action",
            "model_name",
            "record_id",
            "description",
            "timestamp",
        ]


# ============================================================
# COURSE SUBJECT SERIALIZER
# ============================================================

class CourseSubjectSerializer(serializers.ModelSerializer):

    subject_name = serializers.CharField(
        source="subject.name",
        read_only=True
    )

    course_name = serializers.CharField(
        source="course.name",
        read_only=True
    )

    class Meta:
        model = CourseSubject

        fields = [
            "id",
            "course",
            "course_name",
            "subject",
            "subject_name",
            "category",
        ]

    def validate(self, attrs):
        course = attrs.get(
            "course",
            getattr(self.instance, "course", None)
        )

        subject = attrs.get(
            "subject",
            getattr(self.instance, "subject", None)
        )

        if course and subject:
            existing = CourseSubject.objects.filter(
                course=course,
                subject=subject
            )

            if self.instance:
                existing = existing.exclude(
                    pk=self.instance.pk
                )

            if existing.exists():
                raise serializers.ValidationError(
                    "This subject is already assigned to this course."
                )

        return attrs


# ============================================================
# COURSE SELECTION RULE SERIALIZER
# ============================================================

class CourseSelectionRuleSerializer(serializers.ModelSerializer):

    course_name = serializers.CharField(
        source="course.name",
        read_only=True
    )

    class Meta:
        model = CourseSelectionRule

        fields = [
            "id",
            "course",
            "course_name",
            "optional_subject_count",
            "elective_subject_count",
            "selection_deadline",
            "is_selection_open",
        ]

    def get_fields(self):
        fields = super().get_fields()

        if self.instance is not None and "course" in fields:
            fields["course"].read_only = True

        return fields

    def validate(self, attrs):
        deadline = attrs.get(
            "selection_deadline",
            getattr(
                self.instance,
                "selection_deadline",
                None
            )
        )

        if deadline and timezone.is_naive(deadline):
            raise serializers.ValidationError({
                "selection_deadline": (
                    "Provide a timezone-aware deadline."
                )
            })

        optional_count = attrs.get(
            "optional_subject_count",
            getattr(
                self.instance,
                "optional_subject_count",
                2
            )
        )

        elective_count = attrs.get(
            "elective_subject_count",
            getattr(
                self.instance,
                "elective_subject_count",
                1
            )
        )

        if optional_count < 0:
            raise serializers.ValidationError({
                "optional_subject_count": (
                    "The optional subject count cannot be negative."
                )
            })

        if optional_count > 100:
            raise serializers.ValidationError({
                "optional_subject_count": (
                    "The optional subject count cannot exceed 100."
                )
            })

        if elective_count < 0:
            raise serializers.ValidationError({
                "elective_subject_count": (
                    "The elective subject count cannot be negative."
                )
            })

        if elective_count > 100:
            raise serializers.ValidationError({
                "elective_subject_count": (
                    "The elective subject count cannot exceed 100."
                )
            })

        return attrs


# ============================================================
# STUDENT SUBJECT SELECTION SERIALIZER
# ============================================================

class StudentSubjectSelectionSerializer(serializers.ModelSerializer):

    student_name = serializers.CharField(
        source="student.Name",
        read_only=True
    )

    selected_subject_details = CourseSubjectSerializer(
        source="selected_subjects",
        many=True,
        read_only=True
    )

    class Meta:
        model = StudentSubjectSelection

        fields = [
            "id",
            "student",
            "student_name",
            "selected_subjects",
            "selected_subject_details",
            "submitted_at",
            "is_reopened",
        ]

        read_only_fields = [
            "submitted_at",
            "is_reopened",
        ]

    def validate_selected_subjects(self, value):
        student = self.initial_data.get("student")

        if not student and self.instance:
            student = self.instance.student_id

        if student:
            try:
                student_obj = Student.objects.get(pk=student)

            except (
                Student.DoesNotExist,
                TypeError,
                ValueError
            ):
                raise serializers.ValidationError(
                    "Invalid student."
                )

            invalid_subjects = [
                course_subject.id
                for course_subject in value
                if course_subject.course_id != student_obj.Course_id
            ]

            if invalid_subjects:
                raise serializers.ValidationError(
                    "All selected subjects must belong to "
                    "the student's course."
                )

        return value


# ============================================================
# SUBJECT SELECTION AUDIT LOG SERIALIZER
# ============================================================

class SubjectSelectionAuditLogSerializer(serializers.ModelSerializer):

    admin_username = serializers.CharField(
        source="admin_user.username",
        read_only=True
    )

    class Meta:
        model = SubjectSelectionAuditLog

        fields = [
            "id",
            "student_selection",
            "admin_user",
            "admin_username",
            "action",
            "reason",
            "timestamp",
        ]

        read_only_fields = [
            "admin_user",
            "timestamp",
        ]


# ============================================================
# STUDENT SKILL SERIALIZER
# ============================================================

class StudentSkillSerializer(serializers.ModelSerializer):

    class Meta:
        model = StudentSkill
        fields = [
            "id",
            "name",
        ]

        read_only_fields = ["id"]

    def validate_name(self, value):
        value = value.strip()

        if len(value) < 2:
            raise serializers.ValidationError(
                "Skill name must contain at least 2 characters."
            )

        return value


# ============================================================
# CORRECTION DOCUMENT SERIALIZER
# ============================================================

class CorrectionDocumentSerializer(serializers.ModelSerializer):

    uploaded_by_username = serializers.CharField(
        source="uploaded_by.username",
        read_only=True
    )

    class Meta:
        model = CorrectionDocument

        fields = [
            "id",
            "correction_request",
            "uploaded_by",
            "uploaded_by_username",
            "document_type",
            "file",
            "ocr_text",
            "ocr_result",
            "ocr_warning",
            "reviewer_note",
            "uploaded_at",
        ]

        read_only_fields = [
            "id",
            "correction_request",
            "uploaded_by",
            "uploaded_by_username",
            "ocr_text",
            "ocr_result",
            "ocr_warning",
            "reviewer_note",
            "uploaded_at",
        ]


# ============================================================
# PROFILE CORRECTION REQUEST SERIALIZER
# ============================================================

class ProfileCorrectionRequestSerializer(serializers.ModelSerializer):

    student_name = serializers.CharField(
        source="student.Name",
        read_only=True,
        allow_null=True
    )

    teacher_name = serializers.SerializerMethodField()

    documents = CorrectionDocumentSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        model = ProfileCorrectionRequest

        fields = [
            "id",
            "student",
            "student_name",
            "teacher",
            "teacher_name",
            "field_name",
            "old_value",
            "requested_value",
            "requested_photo",
            "reason",
            "requested_address",
            "requested_date_of_birth",
            "status",
            "reviewed_by",
            "submitted_at",
            "reviewed_at",
            "rejection_reason",
            "decision_note",
            "documents",
        ]

        read_only_fields = [
            "id",
            "student_name",
            "teacher_name",
            "old_value",
            "status",
            "reviewed_by",
            "submitted_at",
            "reviewed_at",
            "rejection_reason",
            "decision_note",
            "documents",
        ]

    def validate(self, attrs):
        student = attrs.get(
            "student",
            getattr(self.instance, "student", None)
        )

        teacher = attrs.get(
            "teacher",
            getattr(self.instance, "teacher", None)
        )

        if bool(student) == bool(teacher):
            raise serializers.ValidationError({
                "student": (
                    "A correction request must belong to either "
                    "a Student or a Teacher, not both."
                )
            })

        field_name = attrs.get(
            "field_name",
            getattr(self.instance, "field_name", None)
        )

        requested_value = attrs.get("requested_value") or ""
        requested_address = attrs.get("requested_address") or ""

        requested_date_of_birth = attrs.get(
            "requested_date_of_birth"
        )

        requested_photo = attrs.get("requested_photo")

        if field_name == "photo":

            if not requested_photo and not (
                self.instance
                and self.instance.requested_photo
            ):
                raise serializers.ValidationError({
                    "requested_photo": (
                        "Please upload the requested photo."
                    )
                })

        elif field_name == "address":

            if not (
                requested_address.strip()
                or requested_value.strip()
            ):
                raise serializers.ValidationError({
                    "requested_address": (
                        "Provide the requested address."
                    )
                })

        elif field_name == "date_of_birth":

            if not (
                requested_date_of_birth
                or requested_value.strip()
            ):
                raise serializers.ValidationError({
                    "requested_date_of_birth": (
                        "Provide the requested date of birth."
                    )
                })

        elif field_name in {
            "name",
            "first_name",
            "last_name",
            "phone",
            "email",
        }:

            if not requested_value.strip():
                raise serializers.ValidationError({
                    "requested_value": (
                        "Provide the requested value."
                    )
                })

        return attrs

    def get_teacher_name(self, obj):
        if obj.teacher:
            return (
                obj.teacher.get_full_name()
                or obj.teacher.username
            )

        return None
