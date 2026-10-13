from django.http import request

from .models import Student,Course,StudentProfile,Subject, AcademicRecord, Skill, Certification,Company,Job, EligibilityCheck,PlacementDrive, Application
from .Serializer import StudentSerializer,CourseSerializer,StudentProfileSerializer,AcademicRecordSerializer, SkillSerializer, CertificationSerializer,CompanySerializer,EligibilityCheckSerializer,JobSerializer,  PlacementDriveSerializer, ApplicationSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from rest_framework.permissions import BasePermission, IsAuthenticated, SAFE_METHODS
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from rest_framework.generics import ListCreateAPIView
from .Serializer import SubjectSerializer
from .services import check_student_eligibility
from rest_framework.parsers import MultiPartParser, FormParser
from .permissions import (
    ApplicationPermission,
    EligibilityPermission,
    StudentManagementPermissions,
    StudentImageDeletePermission,
    StudentDetailPermission,
    StudentDetailAllPermission,
    AcademicRecordPermission,
    SkillPermission,
    CertificationPermission,
    CompanyPermission
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
    def get(self,request):
        student=Student.objects.all()
        serializer=StudentSerializer(
            student,many=True
            )
        return Response( 
            serializer.data,
            status=status.HTTP_200_OK
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
    permission_classes=[IsAuthenticated, StudentDetailPermission,StudentImageDeletePermission]

    #get one student
    def get(self,request,id):
        student=Student.objects.get(id=id)
        self.check_object_permissions(request,student)
        if student is None:
            return Response(
                {
                    "error":"Student not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )
        serializer=StudentSerializer(
            student
        )
        return Response(serializer.data,
                        status=status.HTTP_200_OK
                        )

    #PUT
    def put(self,request,id):
        student=Student.objects.get(id=id)
        self.check_object_permissions(request,student)
        if student is None:
            return Response(
                {
                    "error":"student not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )
        serializer=StudentSerializer(
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

    #PATCH
    def patch(self,request,id):
        student=Student.objects.get(id=id)
        self.check_object_permissions(request,student)
        if student is None:
            return Response(
                {
                    "error":"Student not found"
                }, 
                status=status.HTTP_404_NOT_FOUND
            )
        serializer=StudentSerializer(
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

    #DELETE
    def delete(self, request,id):
        student=Student.objects.get(id=id)
        self.check_object_permissions(request,student)
        if student is None:
            return Response(
                {
                    "error":"Student not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )
        if student.Image: 
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
class StudentImageDeleteAPIView(APIView):
    permission_classes = [IsAuthenticated]

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

# get Student Profile
class StudentProfileAPIView(APIView):
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
    permission_classes = [IsAuthenticated, CertificationPermission]
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

        serializer = CompanySerializer(
            companies,
            many=True
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
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

    permission_classes = [IsAuthenticated]

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

        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            return Response(
                {
                    "error": "Student not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            job = Job.objects.get(id=job_id)
        except Job.DoesNotExist:
            return Response(
                {
                    "error": "Job not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        result = check_student_eligibility(
            student,
            job
        )

        eligibility_check = EligibilityCheck.objects.create(
            student=student,
            job=job,
            is_eligible=result["is_eligible"],
            reason=result["reason"]
        )

        serializer = EligibilityCheckSerializer(
            eligibility_check
        )

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )
    
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

class JobListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        jobs = Job.objects.all()
        serializer = JobSerializer(jobs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = JobSerializer(data=request.data)

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

class JobDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        try:
            job = Job.objects.get(id=id)
        except Job.DoesNotExist:
            return Response(
                {"error": "Job not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = JobSerializer(job)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    def put(self, request, id):
        try:
            job = Job.objects.get(id=id)
        except Job.DoesNotExist:
            return Response(
                {"error": "Job not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = JobSerializer(job, data=request.data)

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
        try:
            job = Job.objects.get(id=id)
        except Job.DoesNotExist:
            return Response(
                {"error": "Job not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        job.delete()

        return Response(
            {"message": "Job deleted successfully."},
            status=status.HTTP_204_NO_CONTENT
        )

class PlacementDriveListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        placement_drives = PlacementDrive.objects.all()

        serializer = PlacementDriveSerializer(
            placement_drives,
            many=True
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    def post(self, request):
        serializer = PlacementDriveSerializer(
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

class PlacementDriveDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        try:
            placement_drive = PlacementDrive.objects.get(id=id)
        except PlacementDrive.DoesNotExist:
            return Response(
                {"error": "Placement drive not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = PlacementDriveSerializer(placement_drive)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    def put(self, request, id):
        try:
            placement_drive = PlacementDrive.objects.get(id=id)
        except PlacementDrive.DoesNotExist:
            return Response(
                {"error": "Placement drive not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = PlacementDriveSerializer(
            placement_drive,
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

    def delete(self, request, id):
        try:
            placement_drive = PlacementDrive.objects.get(id=id)
        except PlacementDrive.DoesNotExist:
            return Response(
                {"error": "Placement drive not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        placement_drive.delete()

        return Response(
            {"message": "Placement drive deleted successfully."},
            status=status.HTTP_204_NO_CONTENT
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

        applications = Application.objects.all()

        # STUDENT → ONLY THEIR OWN APPLICATIONS
        if request.user.groups.filter(name="Student").exists():

            try:
                student = request.user.student
            except Student.DoesNotExist:
                return Response(
                    {"error": "Student profile not found."},
                    status=status.HTTP_404_NOT_FOUND
                )

            applications = applications.filter(
                student=student
            )

        serializer = ApplicationSerializer(
            applications,
            many=True
        )

        return Response(serializer.data)


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



