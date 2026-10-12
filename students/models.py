from django.db import models
from django.contrib.auth.models import User


class Course(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Subject(models.Model):  
    name = models.CharField(max_length=100) 

    def __str__(self): 
        return self.name 


class Student(models.Model):

    STATUS_CHOICES=[
        ("active","Active"),
        ("inactive","InActive"),
        ("graduated","Graduated"),
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
    Phone = models.IntegerField()

    Course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='student'
    )

    Image = models.ImageField(
        upload_to='students/',
        null=True,
        blank=True
    )

    status=models.CharField(
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

class StudentProfile(models.Model):
    student = models.OneToOneField(
        Student,
        on_delete=models.CASCADE,
        related_name="profile"
    )
    address = models.CharField(max_length=200)
    date_of_birth = models.DateField()

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
        return f"{self.student.Name} - Semester {self.semester} - {self.subject.name}"


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

    location = models.CharField(
        max_length=200
    )

    contact_person = models.CharField(
        max_length=100
    )

    contact_email = models.EmailField()

    contact_phone = models.CharField(
        max_length=15
    )

    logo = models.ImageField(
        upload_to="companies/",
        blank=True,
        null=True
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

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
        return f"{self.company.name} - {self.title}"


class Job(models.Model):
    placement_drive = models.ForeignKey(
        PlacementDrive,
        on_delete=models.CASCADE,
        related_name="jobs"
    )
    title = models.CharField(max_length=150)
    description = models.TextField(
        blank=True,
        null=True
    )
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
    is_eligible = models.BooleanField()
    reason = models.TextField()
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
        return f"{self.application.student.Name} - {self.application.job.title}"


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

    offer_date = models.DateField(
        null=True,
        blank=True
    )

    joining_date = models.DateField(
        null=True,
        blank=True
    )

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
        ("general", "General"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications"
    )

    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPE_CHOICES
    )

    message = models.TextField()

    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.notification_type}"
