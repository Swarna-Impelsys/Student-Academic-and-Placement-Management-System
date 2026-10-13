from django.contrib import admin
from .models import (
    Student, Course, Subject, StudentProfile, AcademicRecord, Skill,
    Certification, Company, PlacementDrive, Job, EligibilityCheck,
    Application, Interview, Selection, Notification, AuditLog,
)

for model in [
    Student, Course, Subject, StudentProfile, AcademicRecord, Skill,
    Certification, Company, PlacementDrive, Job, EligibilityCheck,
    Application, Interview, Selection, Notification, AuditLog,
]:
    admin.site.register(model)
