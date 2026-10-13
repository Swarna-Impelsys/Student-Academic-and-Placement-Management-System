from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate
from django.db.models import Q, Sum, Avg, Count
from django.utils import timezone

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import ListCreateAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (
    Student, Course, StudentProfile, Subject, AcademicRecord, Skill,
    Certification, Company, PlacementDrive, Job, EligibilityCheck,
    Application, Interview, Selection, Notification, AuditLog,
)
from .Serializer import (
    StudentSerializer, CourseSerializer, StudentProfileSerializer,
    SubjectSerializer, AcademicRecordSerializer, SkillSerializer,
    CertificationSerializer, CompanySerializer, PlacementDriveSerializer,
    JobSerializer, EligibilityCheckSerializer, ApplicationSerializer,
    InterviewSerializer, SelectionSerializer, NotificationSerializer,
    AuditLogSerializer,
)
from .permissions import (
    StudentManagementPermissions, StudentDetailPermission,
    StudentImageDeletePermission, AcademicRecordPermission,
    SkillPermission, CertificationPermission, CompanyPermission,
    PlacementDrivePermission, JobPermission, EligibilityPermission,
    ApplicationPermission, InterviewPermission, SelectionPermission,
    NotificationPermission, DashboardPermission,
)
from .services import check_student_eligibility


def create_audit_log(user, action, model_name, record_id, description):
    AuditLog.objects.create(
        user=user,
        action=action,
        model_name=model_name,
        record_id=str(record_id),
        description=description
    )


def paginate(queryset, request, serializer_class, view=None):
    paginator = PageNumberPagination()
    paginator.page_size = 10
    page = paginator.paginate_queryset(queryset, request, view=view)
    serializer = serializer_class(page, many=True)
    return paginator.get_paginated_response(serializer.data)

#login APIView
class loginAPIView(APIView):
    permission_classes=[]
    def post(self,request):
        username=request.data.get("username")
        password=request.data.get("password")

        user=authenticate(
            request,
            username=username,
            password=password 
            )
        if user is not None:
            refresh=RefreshToken.for_user(user)
            return Response(
                {
                    "refresh":str(refresh),
                    "access":str(refresh.access_token)
                },
                status=status.HTTP_200_OK
            )
        return Response(
            {
                "error":"Inavlid username and password"
            },
            status=status.HTTP_401_UNAUTHORIZED
        )

class logoutAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(
                {"message": "Successfully logged out"},
                status=status.HTTP_200_OK
            )

        except Exception:
            return Response(
                {"error": "Invalid refresh token"},
                status=status.HTTP_400_BAD_REQUEST
            )
# creating class for listcreateAPI
class StudentListCreateAPIView(APIView):

    permission_classes = [IsAuthenticated, StudentManagementPermissions]

    def get(self, request):
        students = Student.objects.all().order_by("id")

        search = request.query_params.get("search")
        if search:
            students = students.filter(
                Q(Name__icontains=search) | Q(Email__icontains=search)
            )

        student_status = request.query_params.get("status")
        if student_status:
            students = students.filter(status=student_status)

        course_id = request.query_params.get("course")
        if course_id:
            students = students.filter(Course_id=course_id)

        return paginate(students, request, StudentSerializer, self)

    def post(self, request):
        serializer = StudentSerializer(data=request.data)

        if serializer.is_valid():
            student = serializer.save()

            create_audit_log(
                user=request.user,
                action="CREATE",
                model_name="Student",
                record_id=student.id,
                description=f"Created student: {student.Name}"
            )

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StudentDetailAPIView(APIView):

    permission_classes = [IsAuthenticated, StudentDetailPermission]

    def get_student(self, request, id):
        student = get_object_or_404(Student, id=id)
        self.check_object_permissions(request, student)
        return student

    def get(self, request, id):
        student = self.get_student(request, id)
        return Response(
            StudentSerializer(student).data,
            status=status.HTTP_200_OK
        )

    def put(self, request, id):
        student = self.get_student(request, id)
        serializer = StudentSerializer(student, data=request.data)

        if serializer.is_valid():
            student = serializer.save()

            create_audit_log(
                request.user, "UPDATE", "Student", student.id,
                f"Updated student: {student.Name}"
            )
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, id):
        student = self.get_student(request, id)
        serializer = StudentSerializer(
            student, data=request.data, partial=True
        )

        if serializer.is_valid():
            student = serializer.save()

            create_audit_log(
                request.user, "UPDATE", "Student", student.id,
                f"Updated student: {student.Name}"
            )
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        student = self.get_student(request, id)

        student_name = student.Name
        student_id = student.id

        create_audit_log(
            request.user, "DELETE", "Student", student_id,
            f"Deleted student: {student_name}"
        )

        if student.Image:
            student.Image.delete(save=False)

        student.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

# delete only image 
class StudentImageDeleteAPIView(APIView):
    permission_classes = [IsAuthenticated, StudentImageDeletePermission]

    def delete(self, request, id):
        student = get_object_or_404(Student, id=id)
        self.check_object_permissions(request, student)

        if student.Image:
            student.Image.delete()
            student.Image = None
            student.save()

            return Response(
                {"message": "Image deleted successfully"},
                status=status.HTTP_200_OK
            )

        return Response(
            {"message": "Student has no image"},
            status=status.HTTP_404_NOT_FOUND
        ) 

# Course by student using relative name 
class CourseStudentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        course = get_object_or_404(Course, id=id)
        students = course.student.all()

        serializer = StudentSerializer(students, many=True)

        return Response({
            "course": course.name,
            "students": serializer.data
        })

# course by student using filter  
class StudentbyCourseAPIView(APIView):
    permission_classes=[IsAuthenticated]

    def get(self,request,id):
        course=get_object_or_404(Course,id=id)
        students=Student.objects.filter(Course=course)

        serializer=StudentSerializer(
            students,many=True
        )

        return Response(
            {
            'course':course.name,
            'students':serializer.data
            }
        )

# course by student using nestedserializer
class CourseDetailAPIView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request,id):
        course=get_object_or_404(Course,id=id)
        serializer=CourseSerializer(course)

        return Response(serializer.data)

#Active status 
class ActiveStudentsAPIView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        students=Student.objects.filter(status="active")

        serializer=StudentSerializer(students,many=True)

        return Response(serializer.data)

# get Student Profile
class StudentProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request,id):
        student=get_object_or_404(Student,id=id)
        Profile=student.profile

        serializer=StudentProfileSerializer(Profile)
        return Response(
            serializer.data
        )

#create student profile
class StudentProfileCreateAPIView(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request):
        serializer=StudentProfileSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,
                            status=status.HTTP_201_CREATED)
        return Response(serializer.errors,
                        status=status.HTTP_400_BAD_REQUEST)

# update student profile
class StudentProfileUpdateAPIView(APIView):
    permission_classes=[IsAuthenticated]
    def put(self,request,id):
        profile=get_object_or_404(StudentProfile,id=id)
        serializer=StudentProfileSerializer(profile,data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors,
                        status=status.HTTP_400_BAD_REQUEST)

    def patch(self,request,id):
        profile=get_object_or_404(StudentProfile,id=id)
        serializer=StudentProfileSerializer(profile,data=request.data,partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors,
                        status=status.HTTP_400_BAD_REQUEST)

# Delete Student Profile
class StudentProfileDeleteAPIView(APIView):
    permission_classes=[IsAuthenticated]
    def delete(self,request,id):
        profile=get_object_or_404(StudentProfile,id=id)
        profile.delete()
        return Response(
            {"message":"Student Profile deleted Successfully"},
            status=status.HTTP_204_NO_CONTENT
        )

# get students subject
class StudentsBySubjectAPIView(APIView): 
 
    permission_classes = [IsAuthenticated] 
 
    def get(self, request, id): 
 
        subject = get_object_or_404(Subject, id=id) 
 
        students = Student.objects.filter( 
            subjects=subject 
        ) 
 
        serializer = StudentSerializer( 
            students, 
            many=True 
        ) 
 
        return Response({ 
            "subject": subject.name, 
            "students": serializer.data 
        }) 
    
 #newly adding courses 
class CourseListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        courses = Course.objects.all()
        serializer = CourseSerializer(courses, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = CourseSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

# create and list the newly  subject
class SubjectListCreateAPIView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer

# create and list the newly academic record
class AcademicRecordListCreateAPIView(APIView):

    permission_classes = [IsAuthenticated, AcademicRecordPermission]

    def get(self, request):
        if request.user.groups.filter(name="Student").exists():
            records = AcademicRecord.objects.filter(
                student__user=request.user
            )
        else:
            records = AcademicRecord.objects.all()

        serializer = AcademicRecordSerializer(records, many=True)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    def post(self, request):
        serializer = AcademicRecordSerializer(
            data=request.data
        )

        if serializer.is_valid():
            serializer.save()

            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

# get ,update and delete academic record
class AcademicRecordDetailAPIView(APIView):

    permission_classes = [IsAuthenticated, AcademicRecordPermission]

    def get(self, request, id):
        record = get_object_or_404(
            AcademicRecord,
            id=id
        )
        self.check_object_permissions(request, record)

        serializer = AcademicRecordSerializer(record)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    def put(self, request, id):
        record = get_object_or_404(
            AcademicRecord,
            id=id
        )
        self.check_object_permissions(request, record)

        serializer = AcademicRecordSerializer(
            record,
            data=request.data
        )

        if serializer.is_valid():
            serializer.save()

            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def patch(self, request, id):
        record = get_object_or_404(
            AcademicRecord,
            id=id
        )
        self.check_object_permissions(request, record)

        serializer = AcademicRecordSerializer(
            record,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()

            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def delete(self, request, id):
        record = get_object_or_404(
            AcademicRecord,
            id=id
        )
        self.check_object_permissions(request, record)

        record.delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )

# create and list the newly skill
class SkillListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated, SkillPermission]

    def get(self, request):
        skills = Skill.objects.all()
        serializer = SkillSerializer(skills, many=True)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    def post(self, request):
        serializer = SkillSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()

            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

# get,update and delete skill
class SkillDetailAPIView(APIView):
    permission_classes = [IsAuthenticated, SkillPermission]

    def get(self, request, id):
        skill = get_object_or_404(Skill, id=id)
        serializer = SkillSerializer(skill)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    def put(self, request, id):
        skill = get_object_or_404(Skill, id=id)

        serializer = SkillSerializer(
            skill,
            data=request.data
        )

        if serializer.is_valid():
            serializer.save()

            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def patch(self, request, id):
        skill = get_object_or_404(Skill, id=id)

        serializer = SkillSerializer(
            skill,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()

            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def delete(self, request, id):
        skill = get_object_or_404(Skill, id=id)
        skill.delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )

# create and list the newly certification
class CertificationListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated, CertificationPermission]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get(self, request):
        if request.user.groups.filter(name="Student").exists():
            certifications = Certification.objects.filter(
                student__user=request.user
            )
        else:
            certifications = Certification.objects.all()

        serializer = CertificationSerializer(
            certifications,
            many=True
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    def post(self, request):
        serializer = CertificationSerializer(
            data=request.data
        )

        if serializer.is_valid():
            serializer.save()

            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

# get,update and delete certification
class CertificationDetailAPIView(APIView):
    permission_classes = [IsAuthenticated, CertificationPermission]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get(self, request, id):
        certification = get_object_or_404(
            Certification,
            id=id
        )
        self.check_object_permissions(request, certification)

        serializer = CertificationSerializer(
            certification
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    def put(self, request, id):
        certification = get_object_or_404(
            Certification,
            id=id
        )
        self.check_object_permissions(request, certification)

        serializer = CertificationSerializer(
            certification,
            data=request.data
        )

        if serializer.is_valid():
            serializer.save()

            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def patch(self, request, id):
        certification = get_object_or_404(
            Certification,
            id=id
        )
        self.check_object_permissions(request, certification)

        serializer = CertificationSerializer(
            certification,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()

            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def delete(self, request, id):
        certification = get_object_or_404(
            Certification,
            id=id
        )
        self.check_object_permissions(request, certification)

        certification.delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )

class CompanyListCreateAPIView(APIView):

    permission_classes = [ IsAuthenticated, CompanyPermission]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get(self, request):
        companies = Company.objects.all().order_by("id")

        search = request.query_params.get("search")
        if search:
            companies = companies.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(location__icontains=search)
            )

        is_active = request.query_params.get("is_active")
        if is_active is not None and is_active.lower() in ["true", "false"]:
            companies = companies.filter(is_active=is_active.lower() == "true")

        return paginate(companies, request, CompanySerializer, self)

    def post(self, request):

        serializer = CompanySerializer(
            data=request.data
        )

        if serializer.is_valid():

            serializer.save()

            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

class CompanyDetailAPIView(APIView):

    permission_classes = [IsAuthenticated,CompanyPermission]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get(self, request, id):

        company = get_object_or_404(
            Company,
            id=id
        )

        serializer = CompanySerializer(company)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    def put(self, request, id):

        company = get_object_or_404(
            Company,
            id=id
        )

        serializer = CompanySerializer(
            company,
            data=request.data
        )

        if serializer.is_valid():

            serializer.save()

            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def patch(self, request, id):

        company = get_object_or_404(
            Company,
            id=id
        )

        serializer = CompanySerializer(
            company,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():

            serializer.save()

            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def delete(self, request, id):

        company = get_object_or_404(
            Company,
            id=id
        )

        company.delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )

class PlacementDriveListCreateAPIView(APIView):

    permission_classes = [IsAuthenticated, PlacementDrivePermission]

    def get(self, request):
        drives = PlacementDrive.objects.all().order_by("id")

        search = request.query_params.get("search")
        if search:
            drives = drives.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(location__icontains=search)
            )

        is_active = request.query_params.get("is_active")
        if is_active is not None and is_active.lower() in ["true", "false"]:
            drives = drives.filter(is_active=is_active.lower() == "true")

        return paginate(drives, request, PlacementDriveSerializer, self)

    def post(self, request):
        serializer = PlacementDriveSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PlacementDriveDetailAPIView(APIView):

    permission_classes = [IsAuthenticated, PlacementDrivePermission]

    def get(self, request, id):
        drive = get_object_or_404(PlacementDrive, id=id)
        return Response(PlacementDriveSerializer(drive).data)

    def put(self, request, id):
        drive = get_object_or_404(PlacementDrive, id=id)
        serializer = PlacementDriveSerializer(drive, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, id):
        drive = get_object_or_404(PlacementDrive, id=id)
        serializer = PlacementDriveSerializer(
            drive, data=request.data, partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        drive = get_object_or_404(PlacementDrive, id=id)
        drive.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class JobListCreateAPIView(APIView):

    permission_classes = [IsAuthenticated, JobPermission]

    def get(self, request):
        jobs = Job.objects.all().order_by("id")

        search = request.query_params.get("search")
        if search:
            jobs = jobs.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(job_type__icontains=search) |
                Q(location__icontains=search)
            )

        job_type = request.query_params.get("job_type")
        if job_type:
            jobs = jobs.filter(job_type__iexact=job_type)

        location = request.query_params.get("location")
        if location:
            jobs = jobs.filter(location__icontains=location)

        is_active = request.query_params.get("is_active")
        if is_active is not None and is_active.lower() in ["true", "false"]:
            jobs = jobs.filter(is_active=is_active.lower() == "true")

        return paginate(jobs, request, JobSerializer, self)

    def post(self, request):
        serializer = JobSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class JobDetailAPIView(APIView):

    permission_classes = [IsAuthenticated, JobPermission]

    def get(self, request, id):
        job = get_object_or_404(Job, id=id)
        return Response(JobSerializer(job).data)

    def put(self, request, id):
        job = get_object_or_404(Job, id=id)
        serializer = JobSerializer(job, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, id):
        job = get_object_or_404(Job, id=id)
        serializer = JobSerializer(job, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        job = get_object_or_404(Job, id=id)
        job.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class EligibilityCheckAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):
        student_id = request.data.get("student")
        job_id = request.data.get("job")

        if not student_id or not job_id:
            return Response(
                {"error": "student and job are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        student = Student.objects.filter(id=student_id).first()
        if student is None:
            return Response(
                {"error": "Student not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        job = Job.objects.filter(id=job_id).first()
        if job is None:
            return Response(
                {"error": "Job not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        result = check_student_eligibility(student, job)

        check = EligibilityCheck.objects.create(
            student=student,
            job=job,
            is_eligible=result["is_eligible"],
            reason=result["reason"]
        )

        return Response(
            EligibilityCheckSerializer(check).data,
            status=status.HTTP_201_CREATED
        )


class EligibilityCheckListAPIView(APIView):

    permission_classes = [IsAuthenticated, EligibilityPermission]

    def get(self, request):
        checks = EligibilityCheck.objects.all().order_by("-checked_at")

        if request.user.groups.filter(name="Student").exists():
            try:
                student = request.user.student
            except Student.DoesNotExist:
                return Response(
                    {"error": "Student profile not found."},
                    status=status.HTTP_404_NOT_FOUND
                )
            checks = checks.filter(student=student)
        else:
            student_id = request.query_params.get("student")
            if student_id:
                checks = checks.filter(student_id=student_id)

        job_id = request.query_params.get("job")
        if job_id:
            checks = checks.filter(job_id=job_id)

        return Response(EligibilityCheckSerializer(checks, many=True).data)

class ApplicationListCreateAPIView(APIView):

    permission_classes = [IsAuthenticated, ApplicationPermission]

    def get(self, request):
        applications = Application.objects.all().order_by("id")

        # STUDENT → ONLY THEIR OWN APPLICATIONS
        if request.user.groups.filter(name="Student").exists():
            try:
                student = request.user.student
            except Student.DoesNotExist:
                return Response(
                    {"error": "Student profile not found."},
                    status=status.HTTP_404_NOT_FOUND
                )
            applications = applications.filter(student=student)

        search = request.query_params.get("search")
        if search:
            applications = applications.filter(job__title__icontains=search)

        application_status = request.query_params.get("status")
        if application_status:
            applications = applications.filter(
                status__iexact=application_status
            )

        return paginate(applications, request, ApplicationSerializer, self)

    def post(self, request):
        student_id = request.data.get("student")
        job_id = request.data.get("job")

        if not student_id or not job_id:
            return Response(
                {"error": "student and job are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # STUDENT CAN APPLY ONLY FOR THEMSELVES
        if request.user.groups.filter(name="Student").exists():
            try:
                logged_in_student = request.user.student
            except Student.DoesNotExist:
                return Response(
                    {"error": "Student profile not found."},
                    status=status.HTTP_404_NOT_FOUND
                )

            if str(student_id) != str(logged_in_student.id):
                return Response(
                    {"error": "You can only apply for yourself."},
                    status=status.HTTP_403_FORBIDDEN
                )

        student = Student.objects.filter(id=student_id).first()
        if student is None:
            return Response(
                {"error": "Student not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        job = Job.objects.filter(id=job_id).first()
        if job is None:
            return Response(
                {"error": "Job not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        eligibility = check_student_eligibility(student, job)

        if not eligibility["is_eligible"]:
            return Response(
                {
                    "error": "Student is not eligible for this job.",
                    "reason": eligibility["reason"]
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ApplicationSerializer(
            data={"student": student.id, "job": job.id}
        )

        if serializer.is_valid():
            application = serializer.save()
            return Response(
                ApplicationSerializer(application).data,
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ApplicationDetailAPIView(APIView):

    permission_classes = [IsAuthenticated, ApplicationPermission]

    def get(self, request, id):
        application = get_object_or_404(Application, id=id)

        if request.user.groups.filter(name="Student").exists():
            if application.student.user != request.user:
                return Response(
                    {"error": "You can only view your own application."},
                    status=status.HTTP_403_FORBIDDEN
                )

        return Response(ApplicationSerializer(application).data)

    def patch(self, request, id):
        application = get_object_or_404(Application, id=id)

        new_status = request.data.get("status")

        if not new_status:
            return Response(
                {"error": "status is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        allowed = ["pending", "shortlisted", "rejected", "selected"]

        if new_status not in allowed:
            return Response(
                {"error": "Invalid application status."},
                status=status.HTTP_400_BAD_REQUEST
            )

        application.status = new_status
        application.save()

        return Response(ApplicationSerializer(application).data)

class NotificationListCreateAPIView(APIView):

    permission_classes = [IsAuthenticated, NotificationPermission]

    def get(self, request):
        notifications = Notification.objects.all().order_by("id")

        if request.user.groups.filter(name="Student").exists():
            notifications = notifications.filter(user=request.user)

        search = request.query_params.get("search")
        if search:
            notifications = notifications.filter(
                Q(message__icontains=search) |
                Q(notification_type__icontains=search)
            )

        is_read = request.query_params.get("is_read")
        if is_read is not None and is_read.lower() in ["true", "false"]:
            notifications = notifications.filter(
                is_read=is_read.lower() == "true"
            )

        return paginate(notifications, request, NotificationSerializer, self)

    def post(self, request):
        if request.user.groups.filter(name="Student").exists():
            return Response(
                {"error": "Students cannot create notifications."},
                status=status.HTTP_403_FORBIDDEN
            )

        user_id = request.data.get("user")
        if not user_id:
            return Response(
                {"error": "user is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        from django.contrib.auth import get_user_model
        User = get_user_model()

        recipient = User.objects.filter(id=user_id).first()
        if recipient is None:
            return Response(
                {"error": "Recipient user not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = NotificationSerializer(data=request.data)

        if serializer.is_valid():
            notification = serializer.save(user=recipient)
            return Response(
                NotificationSerializer(notification).data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class NotificationMarkReadAPIView(APIView):

    permission_classes = [IsAuthenticated, NotificationPermission]

    def patch(self, request, id):
        notification = get_object_or_404(Notification, id=id)

        if request.user.groups.filter(name="Student").exists():
            if notification.user != request.user:
                return Response(
                    {"error": "You can only mark your own notification as read."},
                    status=status.HTTP_403_FORBIDDEN
                )

        notification.is_read = True
        notification.save()

        return Response(NotificationSerializer(notification).data)

class DashboardAPIView(APIView):

    permission_classes = [IsAuthenticated, DashboardPermission]

    def get(self, request):

        total_students = Student.objects.count()
        total_companies = Company.objects.count()
        total_active_companies = Company.objects.filter(is_active=True).count()
        total_drives = PlacementDrive.objects.count()
        total_jobs = Job.objects.count()
        total_active_jobs = Job.objects.filter(is_active=True).count()
        total_applications = Application.objects.count()
        total_pending = Application.objects.filter(status="pending").count()
        total_rejected = Application.objects.filter(status="rejected").count()
        total_interviews = Interview.objects.count()
        total_selected = Selection.objects.filter(status="selected").count()

        if total_applications > 0:
            placement_percentage = (total_selected / total_applications) * 100
        else:
            placement_percentage = 0

        total_vacancies = Job.objects.aggregate(
            total=Sum("vacancies")
        )["total"]
        average_salary = Job.objects.aggregate(
            average=Avg("salary")
        )["average"]

        recent_applications = Application.objects.order_by("-applied_at")[:5]

        today = timezone.now().date()
        upcoming_interviews = Interview.objects.filter(
            interview_date__gte=today
        ).order_by("interview_date", "interview_time")[:5]

        # Course-wise student count (Course related_name is "student")
        course_statistics = Course.objects.annotate(
            student_count=Count("student")
        )
        course_statistics_data = [
            {"course": c.name, "student_count": c.student_count}
            for c in course_statistics
        ]

        # Company-wise selections
        company_statistics = Company.objects.annotate(
            selected_count=Count(
                "placement_drives__jobs__applications__selection",
                filter=Q(
                    placement_drives__jobs__applications__selection__status="selected"
                )
            )
        )
        company_statistics_data = [
            {"company": c.name, "selected_count": c.selected_count}
            for c in company_statistics
        ]

        return Response(
            {
                "total_students": total_students,
                "total_companies": total_companies,
                "total_active_companies": total_active_companies,
                "total_placement_drives": total_drives,
                "total_jobs": total_jobs,
                "total_active_jobs": total_active_jobs,
                "total_applications": total_applications,
                "total_pending_applications": total_pending,
                "total_rejected_applications": total_rejected,
                "total_interviews": total_interviews,
                "total_selected_students": total_selected,
                "placement_percentage": round(placement_percentage, 2),
                "total_vacancies": total_vacancies or 0,
                "average_salary": average_salary or 0,
                "recent_applications": ApplicationSerializer(
                    recent_applications, many=True
                ).data,
                "upcoming_interviews": InterviewSerializer(
                    upcoming_interviews, many=True
                ).data,
                "course_statistics": course_statistics_data,
                "company_statistics": company_statistics_data,
            },
            status=status.HTTP_200_OK
        )

class AuditLogListAPIView(APIView):

    permission_classes = [IsAuthenticated, DashboardPermission]

    def get(self, request):
        audit_logs = AuditLog.objects.all().order_by("-timestamp")
        return paginate(audit_logs, request, AuditLogSerializer, self)

class InterviewListCreateAPIView(APIView):

    permission_classes = [IsAuthenticated, InterviewPermission]

    def get(self, request):
        interviews = Interview.objects.all().order_by("id")

        # STUDENT → ONLY THEIR OWN INTERVIEWS
        if request.user.groups.filter(name="Student").exists():
            try:
                student = request.user.student
            except Student.DoesNotExist:
                return Response(
                    {"error": "Student profile not found."},
                    status=status.HTTP_404_NOT_FOUND
                )
            interviews = interviews.filter(application__student=student)

        search = request.query_params.get("search")
        if search:
            interviews = interviews.filter(
                application__job__title__icontains=search
            )

        interview_status = request.query_params.get("status")
        if interview_status:
            interviews = interviews.filter(status__iexact=interview_status)

        return paginate(interviews, request, InterviewSerializer, self)

    def post(self, request):
        serializer = InterviewSerializer(data=request.data)

        if serializer.is_valid():
            interview = serializer.save()

            # AUTOMATIC NOTIFICATION
            student_user = interview.application.student.user
            if student_user is not None:
                Notification.objects.create(
                    user=student_user,
                    notification_type="interview",
                    message=(
                        f"Your interview for "
                        f"{interview.application.job.title} "
                        f"has been scheduled on "
                        f"{interview.interview_date} "
                        f"at {interview.interview_time}."
                    )
                )

            return Response(
                InterviewSerializer(interview).data,
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class InterviewDetailAPIView(APIView):

    permission_classes = [IsAuthenticated, InterviewPermission]

    def get_object(self, id):
        return Interview.objects.filter(id=id).first()

    def get(self, request, id):
        interview = self.get_object(id)

        if interview is None:
            return Response(
                {"error": "Interview not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Student → only their own interview
        if request.user.groups.filter(name="Student").exists():
            try:
                student = request.user.student
            except Student.DoesNotExist:
                return Response(
                    {"error": "Student profile not found."},
                    status=status.HTTP_404_NOT_FOUND
                )

            if interview.application.student != student:
                return Response(
                    {"error": "You can only view your own interview."},
                    status=status.HTTP_403_FORBIDDEN
                )

        return Response(
            InterviewSerializer(interview).data,
            status=status.HTTP_200_OK
        )

    def put(self, request, id):
        interview = self.get_object(id)

        if interview is None:
            return Response(
                {"error": "Interview not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = InterviewSerializer(interview, data=request.data)

        if serializer.is_valid():
            interview = serializer.save()
            return Response(
                InterviewSerializer(interview).data,
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, id):
        interview = self.get_object(id)

        if interview is None:
            return Response(
                {"error": "Interview not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = InterviewSerializer(
            interview, data=request.data, partial=True
        )

        if serializer.is_valid():
            interview = serializer.save()
            return Response(
                InterviewSerializer(interview).data,
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        interview = self.get_object(id)

        if interview is None:
            return Response(
                {"error": "Interview not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        interview.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SelectionListCreateAPIView(APIView):

    permission_classes = [IsAuthenticated, SelectionPermission]

    def get(self, request):
        selections = Selection.objects.all().order_by("id")

        # STUDENT → ONLY THEIR OWN SELECTIONS
        if request.user.groups.filter(name="Student").exists():
            try:
                student = request.user.student
            except Student.DoesNotExist:
                return Response(
                    {"error": "Student profile not found."},
                    status=status.HTTP_404_NOT_FOUND
                )
            selections = selections.filter(application__student=student)

        return Response(
            SelectionSerializer(selections, many=True).data,
            status=status.HTTP_200_OK
        )

    def post(self, request):
        serializer = SelectionSerializer(data=request.data)

        if serializer.is_valid():
            selection = serializer.save()

            # AUTOMATIC NOTIFICATION
            student_user = selection.application.student.user
            if student_user is not None:
                Notification.objects.create(
                    user=student_user,
                    notification_type="selection",
                    message=(
                        f"Your selection status for "
                        f"{selection.application.job.title} "
                        f"is {selection.get_status_display()}."
                    )
                )

            return Response(
                SelectionSerializer(selection).data,
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SelectionDetailAPIView(APIView):

    permission_classes = [IsAuthenticated, SelectionPermission]

    def get_object(self, id):
        return Selection.objects.filter(id=id).first()

    def get(self, request, id):
        selection = self.get_object(id)

        if selection is None:
            return Response(
                {"error": "Selection not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Student → only their own selection
        if request.user.groups.filter(name="Student").exists():
            try:
                student = request.user.student
            except Student.DoesNotExist:
                return Response(
                    {"error": "Student profile not found."},
                    status=status.HTTP_404_NOT_FOUND
                )

            if selection.application.student != student:
                return Response(
                    {"error": "You can only view your own selection."},
                    status=status.HTTP_403_FORBIDDEN
                )

        return Response(
            SelectionSerializer(selection).data,
            status=status.HTTP_200_OK
        )

    def put(self, request, id):
        selection = self.get_object(id)

        if selection is None:
            return Response(
                {"error": "Selection not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = SelectionSerializer(selection, data=request.data)

        if serializer.is_valid():
            selection = serializer.save()
            return Response(
                SelectionSerializer(selection).data,
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, id):
        selection = self.get_object(id)

        if selection is None:
            return Response(
                {"error": "Selection not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = SelectionSerializer(
            selection, data=request.data, partial=True
        )

        if serializer.is_valid():
            selection = serializer.save()
            return Response(
                SelectionSerializer(selection).data,
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        selection = self.get_object(id)

        if selection is None:
            return Response(
                {"error": "Selection not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        selection.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)





            


    
    
                    
        
        
        

            




