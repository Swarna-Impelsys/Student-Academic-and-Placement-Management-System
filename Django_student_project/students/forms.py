from django import forms
from .models import Student,StudentProfile

class StudentForm(forms.ModelForm):
    class Meta:
        model=Student
        fields= [ 
            "name", 
            "Age",
            "Email", 
            "Phone", 
            "Course" ,
            "Image",
            "status",        
        ] 

class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = [
            "student",
            "address",
            "date_of_birth",
        ]