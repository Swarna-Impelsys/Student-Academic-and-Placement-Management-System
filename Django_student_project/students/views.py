from django.shortcuts import render, redirect, get_object_or_404
from .models import Student,Course,StudentProfile
from .forms import StudentForm ,StudentProfileForm


# Student list
def student_list_form(request):
    student = Student.objects.all()

    context = {
        'student': student
    }

    return render(
        request,
        'students/student_list_form.html',
        context
    )


# Add student
def add_student_form(request):
    if request.method == 'POST':
        form = StudentForm(request.POST,request.FILES)

        if form.is_valid():
            form.save()
            return redirect('student_list_form')

    else:
        form = StudentForm()

    return render(
        request,
        'students/add_student_form.html',
        {'form': form}
    )


# Update student
def update_student_form(request, id):
    student = get_object_or_404(Student, id=id)

    if request.method == 'POST':
        form = StudentForm(request.POST,request.FILES, instance=student)

        if form.is_valid():
            form.save()
            return redirect('student_list_form')

    else:
        form = StudentForm(instance=student)

    return render(
        request,
        'students/update_student_form.html',
        {
            'form': form,
            'student': student
        }
    )


# Delete student
def delete_student_form(request, id):
    student = get_object_or_404(Student, id=id)

    if request.method == 'POST':
        student.delete()
        return redirect('student_list_form')

    return render(
        request,
        'students/delete_student_form.html',
        {
            'student': student
        }
    )

# get course with all students 
def course_student(request,id):
    course=get_object_or_404(Course,id=id)

    students=course.student.all()

    return render(request,'students/course_students.html',
                   {
            'course': course,
            'students': students
        }
        )

# get course by students using filter 
def course_by_student(request,id):
    course=get_object_or_404(Course,id=id)
    students=Student.objects.filter(Course=course)

    return render(
        request,'students/course_by_student.html',
        {
            'course':course,
            'students':students
        }
    )

# active student
def Active_student(request):
    students=Student.objects.filter(status='active')
    return render(
        request,
        'students/active_student.html',
        {
            'students':students
        }
    )

# Student Profile
def Student_Profile(request,id):
    students=get_object_or_404(Student,id=id)
    profile = students.profile

    return render(
        request,
        'students/student_profile.html',
           {
             'student':students,
               'profile':profile
            }
        )

#Add student profile 
def add_student_profile(request):
    if request.method == 'POST':
        form = StudentProfileForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect('student_list_form')
    else:
        form = StudentProfileForm()

    return render(
        request,
        'students/add_student_profile.html',
        {'form': form}
    )


# update student profile
def update_student_profile(request,id):
    profile=get_object_or_404(Student_Profile,id=id)
    if request.method == 'POST':
        form=StudentProfileForm(request.POST,instance=profile)
        if form.is_valid():
            form.save()
            return redirect('student_list_form')
    else:
        form=StudentProfileForm()

    return render(
            request,
            'students/update_student_profile.html',
            {'form': form}
        )

# student subjects 
def student_subjects(request, id): 
    student = get_object_or_404(Student, id=id) 
    subjects = student.subjects.all() 
 
    return render( 
        request, 
        "students/student_subjects.html", 
        { 
            "student": student, 
            "subjects": subjects 
        } 
    ) 

 

    



