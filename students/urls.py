from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    loginAPIView,
    logoutAPIView,
    StudentListCreateAPIView,
    StudentDetailAPIView,
    StudentImageDeleteAPIView,
    CourseStudentAPIView,
    StudentbyCourseAPIView,
    CourseDetailAPIView,
    ActiveStudentsAPIView,
    StudentProfileAPIView,
    StudentProfileCreateAPIView,
    StudentProfileUpdateAPIView,
    StudentProfileDeleteAPIView,
    StudentsBySubjectAPIView,
    CourseListCreateAPIView,
    SubjectListCreateAPIView,
    AcademicRecordListCreateAPIView,
    AcademicRecordDetailAPIView,
    SkillListCreateAPIView,
    SkillDetailAPIView,
    CertificationListCreateAPIView,
    CertificationDetailAPIView,
    CompanyListCreateAPIView,
    CompanyDetailAPIView,
    PlacementDriveListCreateAPIView,
    PlacementDriveDetailAPIView,
    JobListCreateAPIView,
    JobDetailAPIView,
    EligibilityCheckAPIView,
    EligibilityCheckListAPIView,
    ApplicationListCreateAPIView,
    ApplicationDetailAPIView,
    InterviewListCreateAPIView,
    InterviewDetailAPIView,
    SelectionListCreateAPIView,
    SelectionDetailAPIView,
    NotificationListCreateAPIView,
    NotificationMarkReadAPIView,
    DashboardAPIView,
    AuditLogListAPIView,
)

urlpatterns = [

    # Auth
    path("login/", loginAPIView.as_view(), name="api_login"),
    path("logout/", logoutAPIView.as_view(), name="api_logout"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # Students
    path("students/", StudentListCreateAPIView.as_view(), name="StudentListCreate"),
    path("students/active/", ActiveStudentsAPIView.as_view(), name="active_student"),
    path("students/<int:id>/", StudentDetailAPIView.as_view(), name="StudentDetail"),
    path("students/<int:id>/image/", StudentImageDeleteAPIView.as_view(), name="delete_student_image"),
    path("students/subject/<int:id>/", StudentsBySubjectAPIView.as_view(), name="students_by_subject"),

    # Student profile
    path("students/<int:id>/profile/", StudentProfileAPIView.as_view(), name="student_profile"),
    path("students/profile/", StudentProfileCreateAPIView.as_view(), name="student_profile_create"),
    path("students/<int:id>/profile/update/", StudentProfileUpdateAPIView.as_view(), name="student_profile_update"),
    path("students/<int:id>/profile/delete/", StudentProfileDeleteAPIView.as_view(), name="student_profile_delete"),

    # Courses and subjects
    path("students/courses/", CourseListCreateAPIView.as_view(), name="course-list-create"),
    path("students/subjects/", SubjectListCreateAPIView.as_view(), name="subject-list-create"),
    path("courses/<int:id>/", CourseDetailAPIView.as_view(), name="course_detail"),
    path("courses/<int:id>/students/", CourseStudentAPIView.as_view(), name="course_students"),
    path("courses/<int:id>/students/filter/", StudentbyCourseAPIView.as_view(), name="course_by_students"),

    # Academic records
    path("academic-records/", AcademicRecordListCreateAPIView.as_view(), name="academic-record-list-create"),
    path("academic-records/<int:id>/", AcademicRecordDetailAPIView.as_view(), name="academic-record-detail"),

    # Skills
    path("skills/", SkillListCreateAPIView.as_view(), name="skill-list-create"),
    path("skills/<int:id>/", SkillDetailAPIView.as_view(), name="skill-detail"),

    # Certifications
    path("certifications/", CertificationListCreateAPIView.as_view(), name="certification-list-create"),
    path("certifications/<int:id>/", CertificationDetailAPIView.as_view(), name="certification-detail"),

    # Companies
    path("companies/", CompanyListCreateAPIView.as_view(), name="company-list-create"),
    path("companies/<int:id>/", CompanyDetailAPIView.as_view(), name="company-detail"),

    # Placement drives
    path("placement-drives/", PlacementDriveListCreateAPIView.as_view(), name="placement-drive-list-create"),
    path("placement-drives/<int:id>/", PlacementDriveDetailAPIView.as_view(), name="placement-drive-detail"),

    # Jobs
    path("jobs/", JobListCreateAPIView.as_view(), name="job-list-create"),
    path("jobs/<int:id>/", JobDetailAPIView.as_view(), name="job-detail"),

    # Eligibility
    path("eligibility/", EligibilityCheckListAPIView.as_view(), name="eligibility-list"),
    path("eligibility/check/", EligibilityCheckAPIView.as_view(), name="eligibility-check"),

    # Applications
    path("applications/", ApplicationListCreateAPIView.as_view(), name="application-list-create"),
    path("applications/<int:id>/", ApplicationDetailAPIView.as_view(), name="application-detail"),

    # Interviews
    path("interviews/", InterviewListCreateAPIView.as_view(), name="interview-list-create"),
    path("interviews/<int:id>/", InterviewDetailAPIView.as_view(), name="interview-detail"),

    # Selections
    path("selections/", SelectionListCreateAPIView.as_view(), name="selection-list-create"),
    path("selections/<int:id>/", SelectionDetailAPIView.as_view(), name="selection-detail"),

    # Notifications
    path("notifications/", NotificationListCreateAPIView.as_view(), name="notification-list-create"),
    path("notifications/<int:id>/read/", NotificationMarkReadAPIView.as_view(), name="notification-mark-read"),

    # Dashboard and audit logs
    path("dashboard/", DashboardAPIView.as_view(), name="dashboard"),
    path("audit-logs/", AuditLogListAPIView.as_view(), name="audit-logs"),
]