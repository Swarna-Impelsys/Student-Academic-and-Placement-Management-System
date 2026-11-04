
from django.contrib import admin
from .models import (
    Student, Course, Subject, AcademicRecord, Skill,
    Certification, Company, PlacementDrive, Job, EligibilityCheck,
    Application, Interview, Selection, Notification, AuditLog,
    CourseSubject, CourseSelectionRule,
    StudentSubjectSelection, SubjectSelectionAuditLog,
)

for model in [
    Student, Course, Subject, AcademicRecord, Skill,
    Certification, Company, PlacementDrive, Job, EligibilityCheck,
    Application, Interview, Selection, Notification, AuditLog,
    CourseSubject, CourseSelectionRule,
    StudentSubjectSelection, SubjectSelectionAuditLog,
]:
    admin.site.register(model)
