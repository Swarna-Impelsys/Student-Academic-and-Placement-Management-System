
from .models import (
    Application,
    Selection,
    Student,
    Course,
    StudentProfile,
    Subject,
    AcademicRecord,
    Skill,
    Certification,
    Company,
    EligibilityCheck,
    Job,
    PlacementDrive,
    Interview,
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
        issue_date = attrs.get("issue_date")
        expiry_date = attrs.get("expiry_date")

        if expiry_date and issue_date and expiry_date < issue_date:
            raise serializers.ValidationError(
                "Expiry date cannot be before issue date."
            )

        return attrs

class  StudentSerializer(serializers.ModelSerializer):

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
        model=Student
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
            "created_at"
        ]

        read_only_fields = [
            "id",
            "created_at"
        ]

    def validate_title(self, value):
        value = value.strip()

        if len(value) < 3:
            raise serializers.ValidationError(
                "Placement drive title must be at least 3 characters."
            )

        return value

    def validate(self, attrs):
        start_date = attrs.get("application_start_date")
        end_date = attrs.get("application_end_date")
        drive_date = attrs.get("drive_date")

        if start_date and end_date:
            if end_date < start_date:
                raise serializers.ValidationError(
                    "Application end date cannot be before application start date."
                )

        if end_date and drive_date:
            if drive_date < end_date:
                raise serializers.ValidationError(
                    "Drive date cannot be before application end date."
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
            getattr(self.instance, "student", None)
        )
        job = data.get(
            "job",
            getattr(self.instance, "job", None)
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

        read_only_fields = [
            "id",
            "created_at",
        ]

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
            getattr(self.instance, "status", None)
        )

        package = data.get(
            "package",
            getattr(self.instance, "package", None)
        )

        joining_date = data.get(
            "joining_date",
            getattr(self.instance, "joining_date", None)
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