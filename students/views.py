
from django.db.models import Sum, Avg, Count, Q
from django.utils import timezone
from rest_framework.pagination import PageNumberPagination

from .models import (
    Student,
    Course,
    StudentProfile,
    Subject,
    AcademicRecord,
    Skill,
    Certification,
    Company,
    Job,
    EligibilityCheck,
    PlacementDrive,
    Application,
    Interview,
    Selection,
    Notification,
)

from .Serializer import (
    StudentSerializer,
    CourseSerializer,
    StudentProfileSerializer,
    AcademicRecordSerializer,
    SkillSerializer,
    CertificationSerializer,
    CompanySerializer,
    EligibilityCheckSerializer,
    JobSerializer,
    PlacementDriveSerializer,
    ApplicationSerializer,
    InterviewSerializer,
    SelectionSerializer,
    NotificationSerializer,
    SubjectSerializer,
)

from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from rest_framework.generics import ListCreateAPIView
from .Serializer import SubjectSerializer
from .services import check_student_eligibility
from rest_framework.parsers import MultiPartParser, FormParser


from .permissions import (
    ApplicationPermission,
    DashboardPermission,
    EligibilityPermission,
    StudentManagementPermissions,
    StudentImageDeletePermission,
    StudentDetailPermission,
    StudentDetailAllPermission,
    AcademicRecordPermission,
    SkillPermission,
    CertificationPermission,
    CompanyPermission,
    InterviewPermission,
    SelectionPermission,
    NotificationPermission,
    PlacementDrivePermission,
    JobPermission,
)


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

# creating class for listcreateAPI
class StudentListCreateAPIView(APIView):
    
    permission_classes=[IsAuthenticated,StudentManagementPermissions]
    #Get all student data
    def get(self, request):
        students = Student.objects.all().order_by("id")

        # 1. Search by student name or email
        search = request.query_params.get("search")
        if search:
            students = students.filter(
                Q(Name__icontains=search) |
                Q(Email__icontains=search)
            )

        # 2. Filter by status
        student_status = request.query_params.get("status")
        if student_status:
            students = students.filter(status=student_status)

        # 3. Filter by course ID
        course_id = request.query_params.get("course")
        if course_id:
            students = students.filter(course_id=course_id)

        # 4. Pagination
        paginator = PageNumberPagination()
        paginator.page_size = 10

        page = paginator.paginate_queryset(
            students,
            request
        )

        serializer = StudentSerializer(
            page,
            many=True
        )

        return paginator.get_paginated_response(
            serializer.data
        )
    
    # post student data
    def post(self,request):
        serializer=StudentSerializer(
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

#Creating class for DetailAPIview
class StudentDetailAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
        StudentDetailPermission,
        
    ]

    # GET one student
    def get(self, request, id):
        student = get_object_or_404(Student, id=id)
        self.check_object_permissions(request, student)

        serializer = StudentSerializer(student)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    # PUT: update the complete student
    def put(self, request, id):
        student = get_object_or_404(Student, id=id)
        self.check_object_permissions(request, student)

        serializer = StudentSerializer(
            student,
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

    # PATCH: update selected fields
    def patch(self, request, id):
        student = get_object_or_404(Student, id=id)
        self.check_object_permissions(request, student)

        serializer = StudentSerializer(
            student,
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

    # DELETE one student
    def delete(self, request, id):
        student = get_object_or_404(Student, id=id)
        self.check_object_permissions(request, student)

        student.delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )


#LOGOUT API VIEW
class logoutAPIView(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request):
         try: 
            refresh_token=request.data.get("refresh")
            token=RefreshToken(refresh_token)
            token.blacklist()
            return Response(
                 {
                     "message":"Successfully logged out"
                       },
                       status=status.HTTP_200_OK
                       )
         except Exception:
            return Response(
                {
                    "error":"Invalid refresh token"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

# delete only image 

# Delete only the student image
class StudentImageDeleteAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
        StudentImageDeletePermission,
    ]

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
    def get(self,request,id):
        course=Course.objects.get(id=id)
        Student=course.student.all()

        serializer=StudentSerializer(
            Student,
            many=True
            )

        return Response(
            {
            "course":course.name,
            "Students":serializer.data
            }

        )

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



#List  student profile
class StudentProfileListAPIView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request,id):
        student=get_object_or_404(Student,id=id)
        Profile=student.profile

        serializer=StudentProfileSerializer(Profile)
        return Response(
            serializer.data
        )
    
 # Create student profile
class StudentProfileCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = StudentProfileSerializer(data=request.data)

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

# detail update student profile
class StudentProfileDetailAPIView(APIView):
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
    parser_classes = [MultiPartParser, FormParser]

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
    parser_classes = [MultiPartParser, FormParser]

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
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        certification = get_object_or_404(
            Certification,
            id=id
        )

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

        certification.delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )

class CompanyListCreateAPIView(APIView):

    permission_classes = [ IsAuthenticated, CompanyPermission]
    parser_classes = [MultiPartParser, FormParser]
    def get(self, request):
        companies = Company.objects.all()

        # 1. Search by company name, description, or location
        search = request.query_params.get("search")

        if search:
            companies = companies.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(location__icontains=search)
            )

        # 2. Filter by active status
        is_active = request.query_params.get("is_active")

        if is_active is not None and is_active.lower() in ["true", "false"]:
            companies = companies.filter(
                is_active=is_active.lower() == "true"
            )

        # 3. Pagination
        paginator = PageNumberPagination()
        paginator.page_size = 10

        page = paginator.paginate_queryset(
            companies,
            request
        )

        serializer = CompanySerializer(
            page,
            many=True
        )

        return paginator.get_paginated_response(
            serializer.data
        )

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
    parser_classes = [MultiPartParser, FormParser]

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


class EligibilityCheckAPIView(APIView):
    permission_classes = [IsAuthenticated, EligibilityPermission]

    def post(self, request):
        student_id = request.data.get("student")
        job_id = request.data.get("job")

        if not student_id or not job_id:
            return Response(
                {"error": "student and job are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        student = get_object_or_404(Student, id=student_id)
        job = get_object_or_404(Job, id=job_id)

        result = check_student_eligibility(student, job)

        eligibility_check = EligibilityCheck.objects.create(
            student=student,
            job=job,
            is_eligible=result["is_eligible"],
            reason=result["reason"],
        )

        serializer = EligibilityCheckSerializer(eligibility_check)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
        )


class PlacementDriveListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated, PlacementDrivePermission]

    def get(self, request):
        drives = PlacementDrive.objects.all()
        serializer = PlacementDriveSerializer(drives, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = PlacementDriveSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )


class PlacementDriveDetailAPIView(APIView):
    permission_classes = [IsAuthenticated, PlacementDrivePermission]

    def get(self, request, id):
        drive = get_object_or_404(PlacementDrive, id=id)
        serializer = PlacementDriveSerializer(drive)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, id):
        drive = get_object_or_404(PlacementDrive, id=id)
        serializer = PlacementDriveSerializer(drive, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )

    def patch(self, request, id):
        drive = get_object_or_404(PlacementDrive, id=id)
        serializer = PlacementDriveSerializer(
            drive,
            data=request.data,
            partial=True,
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request, id):
        drive = get_object_or_404(PlacementDrive, id=id)
        drive.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class JobListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated, JobPermission]

    def get(self, request):
        jobs = Job.objects.all()
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
            if is_active is not None:
                jobs = jobs.filter(is_active=is_active.lower() == "true")

        paginator = PageNumberPagination()
        paginator.page_size = 10

        page = paginator.paginate_queryset(jobs, request)

        serializer = JobSerializer(page, many=True)

        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = JobSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )


class JobDetailAPIView(APIView):
    permission_classes = [IsAuthenticated, JobPermission]

    def get(self, request, id):
        job = get_object_or_404(Job, id=id)
        serializer = JobSerializer(job)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, id):
        job = get_object_or_404(Job, id=id)
        serializer = JobSerializer(job, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
       
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )

    def patch(self, request, id):
        job = get_object_or_404(Job, id=id)
        serializer = JobSerializer(
            job,
            data=request.data,
            partial=True,
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_200_OK,
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request, id):
        job = get_object_or_404(Job, id=id)
        job.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PlacementDriveListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        placement_drives = PlacementDrive.objects.all()

        # Search
        search = request.query_params.get("search")
        if search:
            placement_drives = placement_drives.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(location__icontains=search)
            )

        # Filter by active status
        is_active = request.query_params.get("is_active")
        if is_active is not None:
            if is_active.lower() in ["true", "false"]:
                placement_drives = placement_drives.filter(
                    is_active=is_active.lower() == "true"
                )

        # Pagination
        paginator = PageNumberPagination()
        paginator.page_size = 10
        page = paginator.paginate_queryset(
            placement_drives, request
        )

        serializer = PlacementDriveSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = PlacementDriveSerializer(
            data=request.data
            status=status.HTTP_400_BAD_REQUEST,
        )

    def patch(self, request, id):
        job = get_object_or_404(Job, id=id)
        serializer = JobSerializer(
            job,
            data=request.data,
            partial=True,
          development
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request, id):
        job = get_object_or_404(Job, id=id)
        job.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
class EligibilityCheckListAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        EligibilityPermission
    ]

    def get(self, request):

        checks = EligibilityCheck.objects.all()

        # Filter by student
        student_id = request.query_params.get("student")

        if request.user.groups.filter(name="Student").exists():

            try:
                student = request.user.student
            except Student.DoesNotExist:
                return Response(
                    {"error": "Student profile not found."},
                    status=status.HTTP_404_NOT_FOUND
                )

            checks = checks.filter(
                student=student
            )

        else:
            if student_id:
                checks = checks.filter(
                    student_id=student_id
                )

        serializer = EligibilityCheckSerializer(
            checks,
            many=True
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


class ApplicationListCreateAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        ApplicationPermission
    ]

    def post(self, request):

        student_id = request.data.get("student")
        job_id = request.data.get("job")

        if not student_id or not job_id:
            return Response(
                {
                    "error": "student and job are required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # STUDENT CAN APPLY ONLY FOR THEMSELVES
        if request.user.groups.filter(name="Student").exists():

            try:
                logged_in_student = request.user.student
            except Student.DoesNotExist:
                return Response(
                    {
                        "error": "Student profile not found."
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

            if int(student_id) != logged_in_student.id:
                return Response(
                    {
                        "error": "You can only apply for yourself."
                    },
                    status=status.HTTP_403_FORBIDDEN
                )

        try:
            student = Student.objects.get(
                id=student_id
            )
        except Student.DoesNotExist:
            return Response(
                {
                    "error": "Student not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            job = Job.objects.get(
                id=job_id
            )
        except Job.DoesNotExist:
            return Response(
                {
                    "error": "Job not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        eligibility = check_student_eligibility(
            student,
            job
        )

        if not eligibility["is_eligible"]:
            return Response(
                {
                    "error": "Student is not eligible for this job.",
                    "reason": eligibility["reason"]
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ApplicationSerializer(
            data={
                "student": student.id,
                "job": job.id
            }
        )

        if serializer.is_valid():

            application = serializer.save()

            return Response(
                ApplicationSerializer(application).data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

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

        # SEARCH by job title
        search = request.query_params.get("search")
        if search:
            applications = applications.filter(
                job__title__icontains=search
            )

        # FILTER by application status
        application_status = request.query_params.get("status")
        if application_status:
            applications = applications.filter(
                status=application_status
            )

        # PAGINATION
        paginator = PageNumberPagination()
        paginator.page_size = 10
        page = paginator.paginate_queryset(applications, request)

        serializer = ApplicationSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class ApplicationDetailAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        ApplicationPermission
    ]

    def patch(self, request, id):

        try:
            application = Application.objects.get(id=id)
        except Application.DoesNotExist:
            return Response(
                {"error": "Application not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        new_status = request.data.get("status")

        if not new_status:
            return Response(
                {"error": "status is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        allowed_statuses = [
            "pending",
            "shortlisted",
            "rejected",
            "selected"
        ]

        if new_status not in allowed_statuses:
            return Response(
                {"error": "Invalid application status."},
                status=status.HTTP_400_BAD_REQUEST
            )

        application.status = new_status
        application.save()

        serializer = ApplicationSerializer(application)

        return Response(serializer.data)


class InterviewListCreateAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        InterviewPermission
    ]

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

            interviews = interviews.filter(
                application__student=student
            )

        # SEARCH by job title
        search = request.query_params.get("search")
        if search:
            interviews = interviews.filter(
                application__job__title__icontains=search
            )

        # FILTER by interview status
        interview_status = request.query_params.get("status")
        if interview_status:
            interviews = interviews.filter(
                status=interview_status
            )

        # PAGINATION
        paginator = PageNumberPagination()
        paginator.page_size = 10
        page = paginator.paginate_queryset(interviews, request)

        serializer = InterviewSerializer(page, many=True)

        return paginator.get_paginated_response(serializer.data)

    def post(self, request):

        serializer = InterviewSerializer(
            data=request.data
        )

        if serializer.is_valid():

            interview = serializer.save()

            # CREATE AUTOMATIC NOTIFICATION
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

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

class InterviewDetailAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        InterviewPermission
    ]

    def get_object(self, id):

        try:
            return Interview.objects.get(id=id)

        except Interview.DoesNotExist:
            return None

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

        serializer = InterviewSerializer(interview)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    def put(self, request, id):

        interview = self.get_object(id)

        if interview is None:
            return Response(
                {"error": "Interview not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = InterviewSerializer(
            interview,
            data=request.data
        )

        if serializer.is_valid():

            interview = serializer.save()

            return Response(
                InterviewSerializer(interview).data,
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def delete(self, request, id):

        interview = self.get_object(id)

        if interview is None:
            return Response(
                {"error": "Interview not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        interview.delete()

        return Response(
            {"message": "Interview deleted successfully."},
            status=status.HTTP_204_NO_CONTENT
        )


class SelectionListCreateAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        SelectionPermission
    ]

    def get(self, request):

        selections = Selection.objects.all()

        # STUDENT → ONLY THEIR OWN SELECTIONS
        if request.user.groups.filter(name="Student").exists():

            try:
                student = request.user.student
            except Student.DoesNotExist:
                return Response(
                    {"error": "Student profile not found."},
                    status=status.HTTP_404_NOT_FOUND
                )

            selections = selections.filter(
                application__student=student
            )

        serializer = SelectionSerializer(
            selections,
            many=True
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    def post(self, request):

        serializer = SelectionSerializer(
            data=request.data
        )

        if serializer.is_valid():

            selection = serializer.save()

            # CREATE AUTOMATIC NOTIFICATION
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

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class SelectionDetailAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        SelectionPermission
    ]

    def get_object(self, id):

        try:
            return Selection.objects.get(id=id)

        except Selection.DoesNotExist:
            return None

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
                    {
                        "error": "You can only view your own selection."
                    },
                    status=status.HTTP_403_FORBIDDEN
                )

        serializer = SelectionSerializer(selection)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    def put(self, request, id):

        selection = self.get_object(id)

        if selection is None:
            return Response(
                {"error": "Selection not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = SelectionSerializer(
            selection,
            data=request.data
        )

        if serializer.is_valid():

            selection = serializer.save()

            return Response(
                SelectionSerializer(selection).data,
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def delete(self, request, id):

        selection = self.get_object(id)

        if selection is None:
            return Response(
                {"error": "Selection not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        selection.delete()

        return Response(
            {"message": "Selection deleted successfully."},
            status=status.HTTP_204_NO_CONTENT
        )

class NotificationListCreateAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        NotificationPermission
    ]

    def get(self, request):
        notifications = Notification.objects.all().order_by("id")
        # STUDENT → ONLY THEIR OWN NOTIFICATIONS
        if request.user.groups.filter(name="Student").exists():
            notifications = notifications.filter(
                user=request.user
            )

        # SEARCH by title or message
        search = request.query_params.get("search")
        if search:
            notifications = notifications.filter(
                Q(message__icontains=search) |
                Q(notification_type__icontains=search)
            )

        # FILTER by read/unread status
        is_read = request.query_params.get("is_read")
        if is_read is not None:
            if is_read.lower() in ["true", "false"]:
                notifications = notifications.filter(
                    is_read=is_read.lower() == "true"
                )

        # PAGINATION
        paginator = PageNumberPagination()
        paginator.page_size = 10
        page = paginator.paginate_queryset(notifications, request)

        serializer = NotificationSerializer(page, many=True)

        return paginator.get_paginated_response(serializer.data)

    def post(self, request):

        serializer = NotificationSerializer(
            data=request.data
        )

        if serializer.is_valid():

            notification = serializer.save()

            return Response(
                NotificationSerializer(notification).data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

class NotificationMarkReadAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        NotificationPermission
    ]

    def patch(self, request, id):

        try:
            notification = Notification.objects.get(id=id)

        except Notification.DoesNotExist:
            return Response(
                {"error": "Notification not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Student can only mark their own notification
        if request.user.groups.filter(name="Student").exists():

            if notification.user != request.user:
                return Response(
                    {
                        "error": "You can only mark your own notification as read."
                    },
                    status=status.HTTP_403_FORBIDDEN
                )

        notification.is_read = True
        notification.save()

        serializer = NotificationSerializer(notification)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

class DashboardAPIView(APIView):

    permission_classes = [
        IsAuthenticated,  DashboardPermission
    ]

    def get(self, request):
        total_students = Student.objects.count()
        total_companies = Company.objects.count()
        total_active_companies = Company.objects.filter(
            is_active=True
        ).count()
        total_drives = PlacementDrive.objects.count()
        total_jobs = Job.objects.count()
        total_active_jobs = Job.objects.filter(
            is_active=True
            ).count()
        total_applications = Application.objects.count()
        total_pending_applications = Application.objects.filter(
            status="pending"
            ).count()
        total_rejected_applications = Application.objects.filter(
            status="rejected"
            ).count()
        total_interviews = Interview.objects.count()
        total_selected_students = Selection.objects.filter(
             status="selected"
             ).count()
        if total_applications > 0:
            placement_percentage = (
                 total_selected_students / total_applications
                 ) * 100
        else:
            placement_percentage = 0
        total_vacancies = Job.objects.aggregate(
            total=Sum("vacancies")
            )["total"]
        average_salary = Job.objects.aggregate(
            average=Avg("salary")
            )["average"]
        recent_applications = Application.objects.order_by(
            "-applied_at"
            )[:5]
        recent_applications_serializer = ApplicationSerializer(
            recent_applications,
            many=True
            )
        today = timezone.now().date()
        upcoming_interviews = Interview.objects.filter(
            interview_date__gte=today
            ).order_by(
                "interview_date",
                "interview_time"
                )[:5]
        upcoming_interviews_serializer = InterviewSerializer(
            upcoming_interviews,
            many=True
            )
        course_statistics = Course.objects.annotate(
            student_count=Count("student")
            )
        course_statistics_data = []
        for course in course_statistics:
            course_statistics_data.append({
                "course": course.name,
                "student_count": course.student_count
                })
        company_statistics = Company.objects.annotate(
    selected_count=Count(
        "placement_drives__jobs__applications__selection",
        filter=Q(
            placement_drives__jobs__applications__selection__status="selected"
        )
    )
)
        company_statistics_data = []
        for company in company_statistics:
            company_statistics_data.append({
                "company": company.name,
                "selected_count": company.selected_count
                })
        return Response(
        {
            "total_students": total_students,
            "total_companies": total_companies,
            "total_active_companies": total_active_companies,
            "total_placement_drives": total_drives,
            "total_jobs": total_jobs,
            "total_active_jobs": total_active_jobs,
            "total_applications": total_applications,
            "total_pending_applications": total_pending_applications,
            "total_rejected_applications": total_rejected_applications,
            "total_interviews": total_interviews,
            "total_selected_students": total_selected_students,
            "placement_percentage": round(
                placement_percentage,
                2
                ),
            "total_vacancies": total_vacancies or 0,
            "average_salary": average_salary or 0,
            "recent_applications": recent_applications_serializer.data,
            "upcoming_interviews": upcoming_interviews_serializer.data,
            "course_statistics": course_statistics_data,
            "company_statistics": company_statistics_data,
        },
        status=status.HTTP_200_OK
    )