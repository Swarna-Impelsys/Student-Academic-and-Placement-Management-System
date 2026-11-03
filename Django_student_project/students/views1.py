from django.shortcuts  import render,redirect,get_object_or_404

from .models import Student

#List of students
def student_list(request):
    student=Student.objects.all()

    context={
        'student':student
        }

    return render(request,'students/student_list.html',context)

#Add Student
def add_student(request):
    if request.method=='POST':
        Name=request.POST['name']
        Age=request.POST['Age']
        Email=request.POST['Email']
        Phone=request.POST['Phone']

        Student.objects.create(
        name=Name,
        Age=Age,
        Email=Email,
        Phone=Phone
    )

        return redirect('student_list')
    return render(request,'students/add_student.html')

#Update student
def update_student(request, id):
    student=get_object_or_404(Student, id=id)
    if request.method=='POST':
        student.name=request.POST['name']
        student.Age=request.POST['Age']
        student.Email=request.POST['Email']
        student.Phone=request.POST['Phone']

        student.save()
        return redirect('student_list')
    context={'student':student}
    return render(request,'students/update_student.html',context)

#delete student 
def delete_student(request,id):
    student=get_object_or_404(Student,id=id)
    if request.method=='POST':
        student.delete()
        return redirect('student_list')
    context={'student':student}
    return render(request,'students/delete_student.html',context)