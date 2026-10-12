from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView 
from .views import(
    PlacementDriveListCreateAPIView,
    loginAPIView,
    StudentListCreateAPIView,
    StudentDetailAPIView,
    logoutAPIView,
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
    PlacementDriveDetailAPIView

)
urlpatterns = [
    path("login/", loginAPIView.as_view(), name="api_login"),
    path("students/", StudentListCreateAPIView.as_view(), name="StudentListCreate"),
    path("students/<int:id>/", StudentDetailAPIView.as_view(), name="StudentDetail"),
    path("logout/", logoutAPIView.as_view(), name="api_logout"),
    path("students/<int:id>/image/",StudentImageDeleteAPIView.as_view(), name="delete_student_image"),
    path("courses/<int:id>/students/",CourseStudentAPIView.as_view(),name="course_students"),
    path("courses/<int:id>/students/filter/",StudentbyCourseAPIView.as_view(),name="course_by_students"),
    path("courses/<int:id>/",CourseDetailAPIView.as_view(),name="course_detail"),
    path("students/active/",ActiveStudentsAPIView.as_view(),name="active_student"),
    path("students/<int:id>/profile/update/",StudentProfileAPIView.as_view(),name="student_profile"),
    path("students/profile/",StudentProfileCreateAPIView.as_view(),name="student_profile_create"),
    path("students/<int:id>/profile/update/",StudentProfileUpdateAPIView.as_view(),name="student_profile_update"),
    path("students/<int:id>/profile/delete/",StudentProfileDeleteAPIView.as_view(),name="student_profile_delete"),
    path("students/subject/<int:id>/",StudentsBySubjectAPIView.as_view(),name="students_by_subject"), 
    path('students/courses/',CourseListCreateAPIView.as_view(),name='course-list-create'),
    path('students/subjects/', SubjectListCreateAPIView.as_view(),name='subject-list-create'),
    path( 'token/refresh/',TokenRefreshView.as_view(), name='token_refresh'), 
    path("academic-records/", AcademicRecordListCreateAPIView.as_view(),name="academic-record-list-create"),
    path("academic-records/<int:id>/",AcademicRecordDetailAPIView.as_view(),name="academic-record-detail"),
    path("skills/", SkillListCreateAPIView.as_view(),name="skill-list-create"),
    path("skills/<int:id>/", SkillDetailAPIView.as_view(),name="skill-detail"),
    path("certifications/", CertificationListCreateAPIView.as_view(),name="certification-list-create"),
    path("certifications/<int:id>/",CertificationDetailAPIView.as_view(),name="certification-detail"),
    path("companies/", CompanyListCreateAPIView.as_view(), name="company-list-create"),
    path("companies/<int:id>/", CompanyDetailAPIView.as_view(),name="company-detail"),
    path("placement-drives/",PlacementDriveListCreateAPIView.as_view(),name="placement-drive-list-create"),
    path("placement-drives/<int:id>/", PlacementDriveDetailAPIView.as_view(),name="placement-drive-detail"),



]


