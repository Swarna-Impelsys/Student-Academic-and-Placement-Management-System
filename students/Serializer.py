from .models import Student,Course,StudentProfile,Subject,AcademicRecord,Skill,Certification, Company,PlacementDrive,Job
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

    # custom validation(name field validation)
    def validate_Name(self,value):
        if len(value) < 3:
            raise serializers.ValidationError("Name must be at least 3 characters")
        return value

    # custom validation( age field validation)
    def validate_Age(self,value):
        if value <= 18:
            raise serializers.ValidationError("Age must be 18 or above")
        return value

    # custom validation(phone field validation)
    def validate_Phone(self,value):
        if len(str(value)) != 10:
            raise serializers.ValidationError("Phone number must be 10 characters")
        return value

    # custom validation( age and course object validation)
    def validate(self, attrs):
        age = attrs.get("Age")
        course = attrs.get("Course")

        restricted_courses = [
            "CEBA",
            "HEBA"
        ]

        if age < 18 and course.name in restricted_courses:
            raise serializers.ValidationError(
                "Students below 18 cannot select this course."
            )

        return attrs

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

    def validate_minimum_age(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError(
                "Minimum age must be greater than 0."
            )

        return value









