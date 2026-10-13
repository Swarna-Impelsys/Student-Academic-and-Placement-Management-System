from .models import (
    Application, Student, Course, StudentProfile, Subject, AcademicRecord,
    Skill, Certification, Company, EligibilityCheck, Job, PlacementDrive,
    Interview, Selection, Notification, AuditLog
)
from rest_framework import serializers

class SubjectSerializer(serializers.ModelSerializer): 
    class Meta: 
        model = Subject 
        fields = [ 
            "id", 
            "name" 
        ] 

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
            "certificate"
        ]

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
                "expiry_date": "Expiry date cannot be before issue date."
            })

        return attrs


class StudentSerializer(serializers.ModelSerializer):

    status_display = serializers.CharField(
        source="get_status_display",
        read_only=True
    )

    subjects = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Subject.objects.all()
    )

    subject_details = SubjectSerializer(
        source="subjects",
        many=True,
        read_only=True
    )

    skills = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Skill.objects.all()
    )

    skill_details = SkillSerializer(
        source="skills",
        many=True,
        read_only=True
    )

    certifications = CertificationSerializer(
        source="certifications",
        many=True,
        read_only=True
    )

    class Meta:
        model = Student
        fields = [
            "id",
            "Name",
            "Age",
            "Email",
            "Phone",
            "Course",
            "Image",
            "status",
            "status_display",
            "subjects",
            "skills",
            "subject_details",
            "skill_details",
            "certifications"
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



class CourseSerializer(serializers.ModelSerializer):
    student=StudentSerializer(many=True,read_only=True)
    class Meta:
        model=Course
        fields= [
            "id",
            "name",
            "student"
        ]

class StudentProfileSerializer(serializers.ModelSerializer):

    student = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.all(),
        write_only=True
    )

    student_details = StudentSerializer(
        source="student",
        read_only=True
    )

    class Meta:
        model = StudentProfile
        fields = [
            "id",
            "student",
            "student_details",
            "address",
            "date_of_birth"
        ]

class AcademicRecordSerializer(serializers.ModelSerializer):

    class Meta:
        model = AcademicRecord
        fields = [
            "id",
            "student",
            "semester",
            "subject",
            "marks",
            "attendance",
            "backlog"
        ]

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
            "created_at"
        ]
        read_only_fields = ["id", "created_at"]

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

        if website and not str(website).startswith(("http://", "https://")):
            raise serializers.ValidationError(
                "Website must start with http:// or https://."
            )

        return attrs

class EligibilityCheckSerializer(serializers.ModelSerializer):

    class Meta:
        model = EligibilityCheck

        fields = [
            "id",
            "student",
            "job",
            "is_eligible",
            "reason",
            "checked_at",
        ]

        read_only_fields = [
            "id",
            "is_eligible",
            "reason",
            "checked_at",
        ]

class JobSerializer(serializers.ModelSerializer):

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
            "maximum_backlogs",
            "is_active",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
        ]

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
        if value is not None and (value < 0 or value > 100):
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
        read_only_fields = ["id", "created_at"]

    def validate(self, attrs):
        start_date = attrs.get(
            "application_start_date",
            getattr(self.instance, "application_start_date", None)
        )
        end_date = attrs.get(
            "application_end_date",
            getattr(self.instance, "application_end_date", None)
        )

        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError({
                "application_end_date": (
                    "Application end date cannot be before the start date."
                )
            })

        return attrs


class ApplicationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Application
        fields = [
            "id",
            "student",
            "job",
            "status",
            "applied_at",
            "updated_at"
        ]
        read_only_fields = [
            "id",
            "status",
            "applied_at",
            "updated_at"
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
        read_only_fields = ["id", "created_at"]

    def validate(self, attrs):
        interview_type = attrs.get(
            "interview_type",
            getattr(self.instance, "interview_type", None),
        )
        location = attrs.get(
            "location",
            getattr(self.instance, "location", None),
        )
        meeting_link = attrs.get(
            "meeting_link",
            getattr(self.instance, "meeting_link", None),
        )

        if interview_type == "online" and not meeting_link:
            raise serializers.ValidationError({
                "meeting_link": "Meeting link is required for online interviews."
            })

        if interview_type == "offline" and not location:
            raise serializers.ValidationError({
                "location": "Location is required for offline interviews."
            })

        return attrs



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
        read_only_fields = ["id", "created_at"]

    def validate(self, data):

        status_value = data.get(
            "status", getattr(self.instance, "status", None)
        )
        package = data.get(
            "package", getattr(self.instance, "package", None)
        )
        joining_date = data.get(
            "joining_date", getattr(self.instance, "joining_date", None)
        )

        if status_value == "selected":
            if package is None:
                raise serializers.ValidationError(
                    "Package is required for selected candidates."
                )
            if joining_date is None:
                raise serializers.ValidationError(
                    "Joining date is required for selected candidates."
                )

        if status_value == "rejected":
            if package is not None:
                raise serializers.ValidationError(
                    "Rejected candidates cannot have a package."
                )
            if joining_date is not None:
                raise serializers.ValidationError(
                    "Rejected candidates cannot have a joining date."
                )

        return data

    def validate_package(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError(
                "Package must be greater than 0."
            )
        return value


class NotificationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Notification
        fields = [
            "id",
            "user",
            "notification_type",
            "message",
            "is_read",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "notification_type",
            "message",
            "created_at",
        ]



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