from django.urls import path
from . import views
urlpatterns = [
    path('', views.student_list_form, name='student_list_form'),
    path('students/add/',views.add_student_form, name='add_student_form'),
    path('students/update/<int:id>/',views.update_student_form, name='update_student_form'),
    path('students/delete/<int:id>/',views.delete_student_form, name='delete_student_form'),
    path('courses/<int:id>/students/',views.course_student,name='course_student'),
    path('courses/<int:id>/students/filter/',views.course_by_student,name='course_by_student'),
    path('students/active/',views.Active_student,name='Active_student'),
    path('students/<int:id>/profile/',views.Student_Profile,name='student_profile'),
    path('students/profile/add/',views.add_student_profile,name='student_add_profile'),
    path('students/<int:id>/profile/',views.update_student_profile,name='student_update_profile'),
    path( "students/<int:id>/subjects/",views.student_subjects,name="student_subjects" ) 
]