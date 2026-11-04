from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    CourseSelectionRuleListCreateAPIView,
    StudentSubjectSelectionAPIView,
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
    StudentDashboardAPIView,
    CourseSubjectListCreateAPIView,
    ReopenStudentSubjectSelectionAPIView,
    AdminStudentSubjectSelectionListAPIView,
    UserListAPIView,
    SetPasswordAPIView,
    ForgotPasswordAPIView,
    ArchiveUserAPIView,
    RestoreUserAPIView,
    ArchivedUserListAPIView,
    TeacherCourseAssignmentAPIView,
    EligibleStudentsByJobAPIView,
    SendEligibleJobNotificationAPIView,
    MyStudentSkillsAPIView,
    MyStudentSkillDetailAPIView,
    ProfileCorrectionRequestListCreateAPIView,
    ProfileCorrectionRequestReviewAPIView,
    CorrectionDocumentUploadAPIView,
    ProfileCorrectionRequestEditAPIView,
    JobInterestResponseAPIView,
    InterviewShortlistUploadAPIView,
    InterviewShortlistExtractAPIView,
    SelectionResultUploadAPIView,
    InterviewShortlistSendNotificationsAPIView,
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

    # Profile correction requests
    path(
    "profile-corrections/",
    ProfileCorrectionRequestListCreateAPIView.as_view(),
    name="profile-correction-list-create"
    ),

    path(
    "profile-corrections/<int:id>/edit/",
    ProfileCorrectionRequestEditAPIView.as_view(),
    name="profile-correction-edit",
    ),
    
    path(
    "profile-corrections/<int:id>/review/",
    ProfileCorrectionRequestReviewAPIView.as_view(),
    name="profile-correction-review"
    ),

    path(
    "profile-corrections/<int:id>/documents/",
    CorrectionDocumentUploadAPIView.as_view(),
    name="profile-correction-document-upload",
),

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

    path(
    "student-dashboard/",
    StudentDashboardAPIView.as_view(),
    name="student-dashboard",
),
path(
    "course-subjects/",
    CourseSubjectListCreateAPIView.as_view(),
    name="course-subject-list-create"
),
path(
    "course-selection-rules/",
    CourseSelectionRuleListCreateAPIView.as_view(),
    name="course-selection-rule-list-create",
),
path(
    "student/subject-selection/",
    StudentSubjectSelectionAPIView.as_view(),
    name="student-subject-selection",
),
path(
    "admin/subject-selections/<int:selection_id>/reopen/",
    ReopenStudentSubjectSelectionAPIView.as_view(),
    name="reopen-student-subject-selection",
),

path(
    "courses/<int:course_id>/selection-rules/",
    CourseSelectionRuleListCreateAPIView.as_view(),
    name="course-selection-rule-detail"
),

path(
    "admin/subject-selections/",
    AdminStudentSubjectSelectionListAPIView.as_view(),
    name="admin-student-subject-selection-list"
),

path(
    "admin/users/",
    UserListAPIView.as_view(),
    name="admin-user-list",
),

path(
    "set-password/",
    SetPasswordAPIView.as_view(),
    name="set-password",
),

path(
    "forgot-password/",
    ForgotPasswordAPIView.as_view(),
    name="forgot-password",
),

path(
    "admin/users/<int:user_id>/archive/",
    ArchiveUserAPIView.as_view(),
    name="admin-user-archive",
),


path(
    "admin/users/<int:user_id>/restore/",
    RestoreUserAPIView.as_view(),
    name="admin-user-restore",
),


path(
    "admin/users/archived/",
    ArchivedUserListAPIView.as_view(),
    name="admin-archived-users",
),

path(
    "admin/teacher-course-assignments/",
    TeacherCourseAssignmentAPIView.as_view(),
    name="teacher-course-assignments",
),

path(
    "eligible-students/",
    EligibleStudentsByJobAPIView.as_view(),
    name="eligible-students-by-job",
),

path(
    "notifications/send-eligible-job/",
    SendEligibleJobNotificationAPIView.as_view(),
    name="send-eligible-job-notification",
),

path(
    "my-skills/",
    MyStudentSkillsAPIView.as_view(),
    name="my-student-skills"
),
path(
    "my-skills/<int:id>/",
    MyStudentSkillDetailAPIView.as_view(),
    name="my-student-skill-detail"
),

    # Student job interest response
    path(
        "job-interest-response/",
        JobInterestResponseAPIView.as_view(),
        name="job-interest-response",
    ),

    # Interview shortlist Excel upload
    path(
        "interviews/upload-shortlist/",
        InterviewShortlistUploadAPIView.as_view(),
        name="interview-shortlist-upload",
    ),

    path(
    "interviews/shortlist/<int:upload_id>/extract/",
    InterviewShortlistExtractAPIView.as_view(),
    name="interview-shortlist-extract",
),

    # Final selection Excel upload
    path(
        "selections/upload-results/",
        SelectionResultUploadAPIView.as_view(),
        name="selection-results-upload",
    ),

    path(
    "interviews/shortlist/<int:upload_id>/send-notifications/",
    InterviewShortlistSendNotificationsAPIView.as_view(),
    name="interview-shortlist-send-notifications",
    ),

]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )