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

    