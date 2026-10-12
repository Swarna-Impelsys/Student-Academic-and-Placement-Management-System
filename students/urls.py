

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    ApplicationDetailAPIView,
    ApplicationListCreateAPIView,
    DashboardAPIView,
    EligibilityCheckAPIView,
    EligibilityCheckListAPIView,
    JobDetailAPIView,
    JobListCreateAPIView,
    NotificationListCreateAPIView,
    NotificationMarkReadAPIView,
    PlacementDriveListCreateAPIView,
    PlacementDriveDetailAPIView,
    loginAPIView,
    StudentListCreateAPIView,
    StudentDetailAPIView,
    logoutAPIView,
    StudentImageDeleteAPIView,
    CourseStudentAPIView,
    StudentbyCourseAPIView,
    CourseDetailAPIView,
    ActiveStudentsAPIView,
    StudentProfileDetailAPIView,
    StudentProfileListAPIView,
    StudentProfileCreateAPIView,
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
    InterviewListCreateAPIView,
    InterviewDetailAPIView,
    SelectionListCreateAPIView,
    SelectionDetailAPIView,
)

urlpatterns = [
    path("login/", loginAPIView.as_view(), name="api_login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("logout/", logoutAPIView.as_view(), name="api_logout"),

    path("students/", StudentListCreateAPIView.as_view(), name="StudentListCreate"),
    path("students/<int:id>/", StudentDetailAPIView.as_view(), name="StudentDetail"),
    path(
        "students/<int:id>/image/",
        StudentImageDeleteAPIView.as_view(),
        name="delete_student_image",
    ),
    path(
        "courses/<int:id>/students/",
        CourseStudentAPIView.as_view(),
        name="course_students",
    ),
    path(
        "courses/<int:id>/students/filter/",
        StudentbyCourseAPIView.as_view(),
        name="course_by_students",
    ),
    path("courses/<int:id>/", CourseDetailAPIView.as_view(), name="course_detail"),
    path("students/active/", ActiveStudentsAPIView.as_view(), name="active_student"),
    
    path(
        "students/profile/",
        StudentProfileCreateAPIView.as_view(),
        name="student_profile_create",
    ),
    path(
        "students/<int:id>/profile/",
        StudentProfileDetailAPIView.as_view(),
        name="student_profile_Detail",
    ),
    path(
        "students/<int:id>/profile/list",
        StudentProfileListAPIView.as_view(),
        name="student_profile_list",
    ),
    path(
        "students/subject/<int:id>/",
        StudentsBySubjectAPIView.as_view(),
        name="students_by_subject",
    ),
    path(
        "students/courses/",
        CourseListCreateAPIView.as_view(),
        name="course-list-create",
    ),
    path(
        "students/subjects/",
        SubjectListCreateAPIView.as_view(),
        name="subject-list-create",
    ),

    path(
        "academic-records/",
        AcademicRecordListCreateAPIView.as_view(),
        name="academic-record-list-create",
    ),
    path(
        "academic-records/<int:id>/",
        AcademicRecordDetailAPIView.as_view(),
        name="academic-record-detail",
    ),

    path("skills/", SkillListCreateAPIView.as_view(), name="skill-list-create"),
    path("skills/<int:id>/", SkillDetailAPIView.as_view(), name="skill-detail"),

    path(
        "certifications/",
        CertificationListCreateAPIView.as_view(),
        name="certification-list-create",
    ),
    path(
        "certifications/<int:id>/",
        CertificationDetailAPIView.as_view(),
        name="certification-detail",
    ),

    path(
        "companies/",
        CompanyListCreateAPIView.as_view(),
        name="company-list-create",
    ),
    path(
        "companies/<int:id>/",
        CompanyDetailAPIView.as_view(),
        name="company-detail",
    ),

    path(
        "placement-drives/",
        PlacementDriveListCreateAPIView.as_view(),
        name="placement-drive-list-create",
    ),
    path(
        "placement-drives/<int:id>/",
        PlacementDriveDetailAPIView.as_view(),
        name="placement-drive-detail",
    ),

    path("jobs/", JobListCreateAPIView.as_view(), name="job-list-create"),
    path("jobs/<int:id>/", JobDetailAPIView.as_view(), name="job-detail"),

    path("eligibility/check/", EligibilityCheckAPIView.as_view(), name="eligibility-check"),
    path("eligibility/", EligibilityCheckListAPIView.as_view(), name="eligibility-list"),

    path(
        "applications/",
        ApplicationListCreateAPIView.as_view(),
        name="application-list-create",
    ),
    path(
        "applications/<int:id>/",
        ApplicationDetailAPIView.as_view(),
        name="application-detail",
    ),

    path(
        "interviews/",
        InterviewListCreateAPIView.as_view(),
        name="interview-list-create",
    ),
    path(
        "interviews/<int:id>/",
        InterviewDetailAPIView.as_view(),
        name="interview-detail",
    ),

    path(
        "selections/",
        SelectionListCreateAPIView.as_view(),
        name="selection-list-create",
    ),
    path(
        "selections/<int:id>/",
        SelectionDetailAPIView.as_view(),
        name="selection-detail",
    ),

    path(
        "notifications/",
        NotificationListCreateAPIView.as_view(),
        name="notification-list-create",
    ),
    path(
        "notifications/<int:id>/read/",
        NotificationMarkReadAPIView.as_view(),
        name="notification-mark-read",
    ),
    path(
        "dashboard/",
        DashboardAPIView.as_view(),
        name="dashboard",
    ),
]


  
