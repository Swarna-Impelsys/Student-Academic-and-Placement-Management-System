from django.db import models


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

    name = models.CharField(max_length=100)
    Age = models.IntegerField()
    Email = models.EmailField(unique=True)
    Phone = models.CharField(max_length=15)

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

    def __str__(self):
        return self.name




