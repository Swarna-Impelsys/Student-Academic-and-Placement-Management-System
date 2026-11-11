from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate
from django.db.models import Q, Sum, Avg, Count, Exists, OuterRef
from django.utils import timezone
from django.contrib.auth.models import User, Group
from django.db import transaction
from django.utils.crypto import salted_hmac
from django.core.files.uploadedfile import UploadedFile
from datetime import datetime, date, time
import hashlib
import json
from decimal import Decimal, InvalidOperation
from openpyxl import load_workbook
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from .tasks import send_account_invitation_task
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.conf import settings 
from rest_framework.throttling import AnonRateThrottle
from .models import  AccountInvitation, ArchivedUser
from .tasks import send_account_invitation_task
from django.db import transaction
from django.contrib.auth import get_user_model

from .ocr_utils import (
    extract_text_from_image,
    extract_text_from_pdf,
    compare_document_text,
)



from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import ListCreateAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework_simplejwt.tokens import RefreshToken


from .models import (
    Student, Course, Subject, AcademicRecord, Skill,
    Certification, Company, PlacementDrive, Job, EligibilityCheck,
    Application, Interview, Selection, Notification, AuditLog,
    CourseSubject, CourseSelectionRule, StudentSubjectSelection,
    SubjectSelectionAuditLog, TeacherCourseAssignment, StudentSkill,
    ProfileCorrectionRequest, CorrectionDocument, JobInterestResponse,
    InterviewShortlistUpload, SelectionResultUpload
)


from .Serializer import (
    StudentSerializer, CourseSerializer,
    SubjectSerializer, AcademicRecordSerializer, SkillSerializer,
    CertificationSerializer, CompanySerializer, PlacementDriveSerializer,
    JobSerializer, EligibilityCheckSerializer, ApplicationSerializer,
    InterviewSerializer, SelectionSerializer, NotificationSerializer,
    AuditLogSerializer, CourseSubjectSerializer, CourseSelectionRuleSerializer,
    StudentSubjectSelectionSerializer, SubjectSelectionAuditLogSerializer,
    TeacherCourseAssignmentSerializer,StudentSkillSerializer,ProfileCorrectionRequestSerializer,
    CorrectionDocumentSerializer, JobInterestResponseSerializer,
    InterviewShortlistUploadSerializer, SelectionResultUploadSerializer
)

from .permissions import (
    StudentManagementPermissions, StudentDetailPermission,
    StudentImageDeletePermission, AcademicRecordPermission,
    SkillPermission, CertificationPermission, CompanyPermission,
    PlacementDrivePermission, JobPermission, EligibilityPermission,
    ApplicationPermission, InterviewPermission, SelectionPermission,
    NotificationPermission, DashboardPermission,AuditLogPermission,CoursePermission,
    StudentProfilePermission,SubjectPermission,IsStudent,IsAdmin
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
    paginator.page_size_query_param = "page_size"
    paginator.max_page_size = 100

    page = paginator.paginate_queryset(
        queryset,
        request,
        view=view
    )

    serializer = serializer_class(page, many=True)

    return paginator.get_paginated_response(serializer.data)


def user_has_role(user, role):
    return user.is_superuser or user.groups.filter(name=role).exists()

def eligibility_source_fingerprint(student, job):
    """Create a stable fingerprint of the student/job inputs used for checking."""
    academic = list(
        student.academic_records.order_by("id").values(
            "semester", "subject_id", "marks", "attendance", "backlog"
        )
    )
    skills = sorted(student.skills.values_list("id", flat=True))
    payload = {
        "student": {
            "id": student.pk, "age": student.Age, "course_id": student.Course_id,
            "status": student.status, "skills": skills, "academic": academic,
        },
        "job": {
            "id": job.pk, "active": job.is_active,
            "minimum_age": job.minimum_age, "minimum_marks": job.minimum_marks,
            "minimum_attendance": job.minimum_attendance,
            "required_course_id": job.required_course_id,
            "required_skills": sorted(job.required_skills.values_list("id", flat=True)),
            "maximum_backlogs": job.maximum_backlogs,
        },
    }
    raw = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

def latest_current_eligibility(student, job, checked_by=None):
    """Return the newest saved check only when its source data is still current."""
    checks = EligibilityCheck.objects.filter(student=student, job=job)
    if checked_by is not None:
        checks = checks.filter(checked_by=checked_by)
    check = checks.order_by("-checked_at", "-id").first()
    if check is None:
        return None
    current_fingerprint = eligibility_source_fingerprint(student, job)
    if not check.source_fingerprint or check.source_fingerprint != current_fingerprint:
        return None
    return check

def is_registration_officer(user):
    return user.groups.filter(name="Registration Officer").exists()

# users 
class UserListAPIView(APIView):

    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):

        users = User.objects.filter(
    archive_record__isnull=True
).order_by("id")

        user_data = []

        for user in users:

            groups = list(
                user.groups.values_list("name", flat=True)
            )

            if user.is_superuser:
                role = "Admin"
            elif "Admin" in groups:
                role = "Admin"
            
            elif "Registration Officer" in groups:
                role = "Registration Officer"
            elif "Teacher" in groups:
                role = "Teacher"
            elif "Student" in groups:
                role = "Student"
            else:
                role = "Unassigned"


            user_data.append({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": role,
                "is_active": user.is_active,
            })

        return Response(user_data, status=status.HTTP_200_OK)
    
    
    def post(self, request):
        username = request.data.get("username", "").strip()
        email = request.data.get("email", "").strip()
        role = request.data.get("role", "").strip()
        student_id = request.data.get("student_id")

        # 1. Validate required fields.
        if not username or not email or not role:
            return Response(
                {"error": "Username, email, and role are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 2. Only allow Teacher and Student accounts here.
        
        # 2. Allow Teacher, Student, and Registration Officer accounts.
        if role not in ["Teacher", "Student", "Registration Officer"]:
            return Response(
                {
                    "error": (
                        "Role must be Teacher, Student, "
                        "or Registration Officer."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


        # 3. Check duplicate username and email.
        if User.objects.filter(username=username).exists():
            return Response(
                {"error": "This username already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.objects.filter(email__iexact=email).exists():
            return Response(
                {"error": "This email already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 4. Find the requested role group.
        try:
            group = Group.objects.get(name=role)
        except Group.DoesNotExist:
            return Response(
                {"error": f"The {role} group does not exist."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 5. Validate the Student record when creating a Student account.
        student = None

        if role == "Student":
            if not student_id:
                return Response(
                    {"error": "Please select a student record."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                student = Student.objects.get(pk=student_id)
            except (Student.DoesNotExist, ValueError, TypeError):
                return Response(
                    {"error": "The selected student does not exist."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if student.user_id is not None:
                return Response(
                    {"error": "This student already has a user account."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if student.Email.strip().lower() != email.lower():
                return Response(
                    {
                        "error": (
                            "The account email must match "
                            "the selected student's email."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        
        # 6. Create the account and invitation record together.
        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=None,
                )

                user.groups.add(group)

                if student is not None:
                    student.user = user
                    student.save(update_fields=["user"])

                invitation = AccountInvitation.objects.create(
                    user=user,
                    status="pending",
                )

        except Exception:
            return Response(
                {
                    "error": (
                        "Account creation failed. "
                        "Check the submitted information and try again."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 7. Queue the invitation after the transaction commits.
        def queue_invitation():
            import logging

            logger = logging.getLogger(__name__)

            try:
                send_account_invitation_task.delay(invitation.id)
            except Exception:
                logger.exception(
                    "Failed to queue invitation ID %s for user ID %s",
                    invitation.id,
                    user.id,
                )

        transaction.on_commit(queue_invitation)



        
        return Response(
            {
                "message": (
                    "Account created successfully. "
                    "The invitation is pending processing."
                ),
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": role,
                "is_active": user.is_active,
                "student_id": student.id if student else None,
                "invitation_id": invitation.id,
                "invitation_status": invitation.status,
                "invitation_queued": None,
            },
            status=status.HTTP_201_CREATED,
        )


class ArchiveUserAPIView(APIView):

    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request, user_id):

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if user.is_superuser or user.groups.filter(name="Admin").exists():
            return Response(
                {"error": "Admin accounts cannot be archived here."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if ArchivedUser.objects.filter(user=user).exists():
            return Response(
                {"error": "This user is already archived."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reason = request.data.get("reason", "").strip()

        try:
            with transaction.atomic():
                user.is_active = False
                user.save(update_fields=["is_active"])

                ArchivedUser.objects.create(
                    user=user,
                    archived_by=request.user,
                    reason=reason,
                )

        except Exception:
            return Response(
                {"error": "Unable to archive this user."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "message": "User archived and account deactivated successfully.",
                "user_id": user.id,
                "is_active": user.is_active,
            },
            status=status.HTTP_200_OK,
        )
    

class RestoreUserAPIView(APIView):

    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request, user_id):

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            with transaction.atomic():
                archive_record = ArchivedUser.objects.select_for_update().get(
                    user=user
                )

                user.is_active = True
                user.save(update_fields=["is_active"])

                archive_record.delete()

        except ArchivedUser.DoesNotExist:
            return Response(
                {"error": "This user is not archived."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "message": "User restored and account reactivated successfully.",
                "user_id": user.id,
                "is_active": user.is_active,
            },
            status=status.HTTP_200_OK,
        )


class ArchivedUserListAPIView(APIView):

    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):

        archived_users = ArchivedUser.objects.select_related(
            "user", "archived_by"
        ).order_by("-archived_at")

        user_data = []

        for archive in archived_users:
            user = archive.user

            groups = list(
                user.groups.values_list("name", flat=True)
            )

            if user.is_superuser:
                role = "Admin"
            elif "Admin" in groups:
                role = "Admin"
            elif "Teacher" in groups:
                role = "Teacher"
            elif "Student" in groups:
                role = "Student"
            else:
                role = "Unassigned"

            user_data.append({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": role,
                "is_active": user.is_active,
                "reason": archive.reason,
                "archived_at": archive.archived_at,
                "archived_by": (
                    archive.archived_by.username
                    if archive.archived_by else None
                ),
            })

        return Response(user_data, status=status.HTTP_200_OK)



    
#login APIView
class loginAPIView(APIView):
    permission_classes = []

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is None:
            return Response(
                {"error": "Invalid username and password"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Identify the user's role
        if user.is_superuser or user.groups.filter(name="Admin").exists():
            role = "Admin"
        elif user.groups.filter(name="Registration Officer").exists():
            role = "Registration Officer"
        elif user.groups.filter(name="Teacher").exists():
            role = "Teacher"
        elif user.groups.filter(name="Student").exists():
            role = "Student"
        else:
            return Response(
                {"error": "No valid role assigned to this account."},
                status=status.HTTP_403_FORBIDDEN
            )


        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "role": role
            },
            status=status.HTTP_200_OK
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

        # Admin and Registration Officer can see all students.
        if request.user.is_superuser or request.user.groups.filter(
            name__in=["Admin", "Registration Officer"]
        ).exists():
            pass
        # Teachers can see only students in assigned courses.
        elif request.user.groups.filter(name="Teacher").exists():
            assigned_course_ids = TeacherCourseAssignment.objects.filter(
                teacher=request.user
            ).values_list("course_id", flat=True)
            students = students.filter(Course_id__in=assigned_course_ids)
        else:
            return Response({"error": "You do not have permission to view students."}, status=status.HTTP_403_FORBIDDEN)

        search = request.query_params.get("search")
        if search:
            students = students.filter(
                Q(Name__icontains=search) |
                Q(Email__icontains=search)
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

            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class StudentDetailAPIView(APIView):

    permission_classes = [IsAuthenticated, StudentDetailPermission]

    def get_student(self, request, id):
        if request.user.is_superuser or request.user.groups.filter(
            name__in=["Admin", "Registration Officer"]
        ).exists():
            student = get_object_or_404(Student, id=id)
        elif request.user.groups.filter(name="Teacher").exists():
            assigned_course_ids = TeacherCourseAssignment.objects.filter(
                teacher=request.user
            ).values_list("course_id", flat=True)
            student = get_object_or_404(Student, id=id, Course_id__in=assigned_course_ids)
        else:
            raise PermissionDenied("You do not have permission to view this student.")

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

    @transaction.atomic
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
    permission_classes = [IsAuthenticated, CoursePermission]

    def get(self, request, id):
        # Admin can view any course and its students.
        if request.user.groups.filter(name="Admin").exists():
            course = get_object_or_404(Course, id=id)

        # Student can view only their enrolled course.
        elif request.user.groups.filter(name="Student").exists():
            student = Student.objects.filter(
                user=request.user
            ).first()

            if student is None:
                return Response(
                    {
                        "detail": (
                            "No student profile is linked "
                            "to this account."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN
                )

            course = get_object_or_404(Course, id=id)

            if course.id != student.Course_id:
                return Response(
                    {
                        "detail": (
                            "You do not have permission "
                            "to view this course."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN
                )

        # Teacher can view only an assigned course.
        elif request.user.groups.filter(name="Teacher").exists():
            assignment_exists = TeacherCourseAssignment.objects.filter(
                teacher=request.user,
                course_id=id
            ).exists()

            if not assignment_exists:
                return Response(
                    {
                        "detail": (
                            "You can only view students "
                            "in courses assigned to you."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN
                )

            course = get_object_or_404(Course, id=id)

        else:
            return Response(
                {
                    "detail": (
                        "You do not have permission "
                        "to view this course."
                    )
                },
                status=status.HTTP_403_FORBIDDEN
            )

        # Get students enrolled in this course.
        students = course.student.all()

        # Students can see only their own student record.
        if request.user.groups.filter(name="Student").exists():
            students = students.filter(user=request.user)

        serializer = StudentSerializer(students, many=True)

        return Response({
            "course": course.name,
            "students": serializer.data
        })


# course by student using filter  

class StudentbyCourseAPIView(APIView):
    permission_classes = [IsAuthenticated, CoursePermission]

    def get(self, request, id):
        course = get_object_or_404(Course, id=id)
        students = Student.objects.filter(Course=course)

        # Students can view only their own student record.
        if request.user.groups.filter(name="Student").exists():
            students = students.filter(user=request.user)

        serializer = StudentSerializer(students, many=True)

        return Response({
            "course": course.name,
            "students": serializer.data
        })

# course by student using nestedserializer

class CourseDetailAPIView(APIView):
    permission_classes = [IsAuthenticated, CoursePermission]

    def get(self, request, id):
        if request.user.groups.filter(name="Admin").exists():
            courses = Course.objects.all()

        elif request.user.groups.filter(name="Student").exists():
            student = Student.objects.filter(
                user=request.user
            ).first()

            if student is None:
                return Response(
                    {"detail": "No student profile is linked to this account."},
                    status=status.HTTP_403_FORBIDDEN
                )

            courses = Course.objects.filter(
                id=student.Course_id
            )

        else:
            # Teacher access will be configured
            # after teacher-course assignments are defined.
            courses = Course.objects.none()

        course = get_object_or_404(courses, id=id)

        serializer = CourseSerializer(course)
        return Response(serializer.data)

    def patch(self, request, id):
        course = get_object_or_404(Course, id=id)

        serializer = CourseSerializer(
            course,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


#Active status 
class ActiveStudentsAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
        StudentManagementPermissions
    ]

    def get(self, request):
        students = Student.objects.filter(status="active")

        # Students can see only their own active record.
        if request.user.groups.filter(name="Student").exists():
            students = students.filter(user=request.user)

        serializer = StudentSerializer(students, many=True)

        return Response(serializer.data)


# get Student Profile
class StudentProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        student = get_object_or_404(Student, id=id)

        # Students can view only their own profile.
        if request.user.groups.filter(name="Student").exists():
            if student.user != request.user:
                return Response(
                    {"error": "You can only view your own profile."},
                    status=status.HTTP_403_FORBIDDEN
                )

        return Response(
            {
                "student": student.id,
                "address": student.address,
                "date_of_birth": student.date_of_birth
            },
            status=status.HTTP_200_OK
        )


#create student profile

# Create or save student profile details directly on Student
class StudentProfileCreateAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
        StudentProfilePermission
    ]

    def post(self, request):
        student_id = request.data.get("student")

        if not student_id:
            return Response(
                {"error": "student is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        student = get_object_or_404(Student, id=student_id)

        if (
            request.user.groups.filter(name="Student").exists()
            and student.user != request.user
        ):
            return Response(
                {"error": "You can only update your own profile."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Save address and date of birth on the Student model.
        serializer = StudentSerializer(
            student,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()

            return Response(
                {
                    "message": "Student profile details saved successfully.",
                    "student": serializer.data
                },
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

# update student profile

# Update student profile details
class StudentProfileUpdateAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
        StudentProfilePermission
    ]

    def put(self, request, id):
        student = get_object_or_404(Student, id=id)

        if (
            request.user.groups.filter(name="Student").exists()
            and student.user != request.user
        ):
            return Response(
                {"error": "You can only update your own profile."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = StudentSerializer(
            student,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def patch(self, request, id):
        student = get_object_or_404(Student, id=id)

        if (
            request.user.groups.filter(name="Student").exists()
            and student.user != request.user
        ):
            return Response(
                {"error": "You can only update your own profile."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = StudentSerializer(
            student,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


# Delete Student Profile

# Clear student profile details without deleting the student
class StudentProfileDeleteAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
        StudentProfilePermission
    ]

    def delete(self, request, id):
        student = get_object_or_404(Student, id=id)

        student.address = None
        student.date_of_birth = None
        student.save(update_fields=["address", "date_of_birth"])

        return Response(
            {
                "message": "Student profile details cleared successfully."
            },
            status=status.HTTP_200_OK
        )


# get students subject
class StudentsBySubjectAPIView(APIView):
    permission_classes = [IsAuthenticated, CoursePermission]

    def get(self, request, id):
        subject = get_object_or_404(Subject, id=id)

        students = Student.objects.filter(subjects=subject)

        # Students can view only their own student record.
        if request.user.groups.filter(name="Student").exists():
            students = students.filter(user=request.user)

        serializer = StudentSerializer(students, many=True)

        return Response({
            "subject": subject.name,
            "students": serializer.data
        })

 #newly adding courses 

class CourseListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated, CoursePermission]

    def get(self, request):
        if request.user.groups.filter(name="Admin").exists():
            # Admin can see all courses
            courses = Course.objects.all()

        elif request.user.groups.filter(name="Student").exists():
            # Student can see only their enrolled course
            student = Student.objects.filter(
                user=request.user
            ).first()

            if student is None:
                return Response(
                    {
                        "detail": (
                            "No student profile is linked to this account."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN
                )

            courses = Course.objects.filter(
                id=student.Course_id
            )

        elif request.user.groups.filter(name="Teacher").exists():
            # Teacher can see only courses assigned by Admin
            courses = Course.objects.filter(
                teacher_assignments__teacher=request.user
            ).distinct()

        else:
            courses = Course.objects.none()

        serializer = CourseSerializer(courses, many=True)
        return Response(serializer.data)

    def post(self, request):
        # Only Admin should create courses
        if not request.user.groups.filter(name="Admin").exists():
            return Response(
                {"detail": "Only Admin can create courses."},
                status=status.HTTP_403_FORBIDDEN
            )

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
    permission_classes = [IsAuthenticated,SubjectPermission]
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

        elif request.user.groups.filter(name="Teacher").exists():
            assigned_courses = TeacherCourseAssignment.objects.filter(
                teacher=request.user
            ).values_list("course_id", flat=True)

            records = AcademicRecord.objects.filter(
                student__Course_id__in=assigned_courses
            )

        else:
            # Admin and Registration Officer
            records = AcademicRecord.objects.all()

        serializer = AcademicRecordSerializer(
            records,
            many=True,
            context={"request": request}
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    def post(self, request):
        serializer = AcademicRecordSerializer(
            data=request.data,
            context={"request": request}
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


# Get, update and delete academic record
class AcademicRecordDetailAPIView(APIView):

    permission_classes = [IsAuthenticated, AcademicRecordPermission]

    def get(self, request, id):
        record = get_object_or_404(
            AcademicRecord,
            id=id
        )
        self.check_object_permissions(request, record)

        serializer = AcademicRecordSerializer(
            record,
            context={"request": request}
        )

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
            data=request.data,
            context={"request": request}
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
            partial=True,
            context={"request": request}
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

        record_id = record.id
        record_description = (
            f"Deleted academic record for {record.student.Name}, "
            f"Semester {record.semester}, Subject {record.subject.name}"
        )

        record.delete()

        AuditLog.objects.create(
            user=request.user,
            action="DELETE",
            model_name="AcademicRecord",
            record_id=str(record_id),
            description=record_description
        )

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
        user = request.user

        if (
            user.is_superuser
            or user.groups.filter(name="Admin").exists()
        ):
            certifications = Certification.objects.all()

        elif user.groups.filter(name="Teacher").exists():
            assigned_course_ids = TeacherCourseAssignment.objects.filter(
                teacher=user
            ).values_list("course_id", flat=True)

            certifications = Certification.objects.filter(
                student__Course_id__in=assigned_course_ids
            )

        elif user.groups.filter(name="Student").exists():
            certifications = Certification.objects.filter(
                student__user=user
            )

        else:
            return Response(
                {"detail": "You do not have permission to view certificates."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = CertificationSerializer(
            certifications.select_related("student"),
            many=True,
            context={"request": request}
        )

        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        user = request.user

        # Only Admin and Student can create certificates.
        is_admin = (
            user.is_superuser
            or user.groups.filter(name="Admin").exists()
        )
        is_student = user.groups.filter(name="Student").exists()

        if not (is_admin or is_student):
            return Response(
                {"detail": "Teachers cannot add certificates."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = CertificationSerializer(
            data=request.data,
            context={"request": request}
        )

        if serializer.is_valid():
            if is_student:
                student = get_object_or_404(Student, user=user)
                # Ignore any student ID submitted by the student.
                serializer.save(student=student)
            else:
                serializer.save()

            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class CertificationDetailAPIView(APIView):
    permission_classes = [IsAuthenticated, CertificationPermission]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_certification(self, request, id):
        user = request.user

        if (
            user.is_superuser
            or user.groups.filter(name="Admin").exists()
        ):
            queryset = Certification.objects.all()

        elif user.groups.filter(name="Teacher").exists():
            assigned_course_ids = TeacherCourseAssignment.objects.filter(
                teacher=user
            ).values_list("course_id", flat=True)

            queryset = Certification.objects.filter(
                student__Course_id__in=assigned_course_ids
            )

        elif user.groups.filter(name="Student").exists():
            queryset = Certification.objects.filter(
                student__user=user
            )

        else:
            queryset = Certification.objects.none()

        return get_object_or_404(queryset, id=id)

    def get(self, request, id):
        certification = self.get_certification(request, id)

        serializer = CertificationSerializer(
            certification,
            context={"request": request}
        )

        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, id):
        return self.update_certification(request, id, partial=False)

    def patch(self, request, id):
        return self.update_certification(request, id, partial=True)

    def update_certification(self, request, id, partial):
        user = request.user

        is_admin = (
            user.is_superuser
            or user.groups.filter(name="Admin").exists()
        )
        is_student = user.groups.filter(name="Student").exists()

        if not (is_admin or is_student):
            return Response(
                {"detail": "Teachers cannot edit certificates."},
                status=status.HTTP_403_FORBIDDEN
            )

        certification = self.get_certification(request, id)

        serializer = CertificationSerializer(
            certification,
            data=request.data,
            partial=partial,
            context={"request": request}
        )

        if serializer.is_valid():
            if is_student:
                # Keep the certificate linked to its original owner.
                serializer.save(student=certification.student)
            else:
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
        user = request.user

        is_admin = (
            user.is_superuser
            or user.groups.filter(name="Admin").exists()
        )
        is_student = user.groups.filter(name="Student").exists()

        if not (is_admin or is_student):
            return Response(
                {"detail": "Teachers cannot delete certificates."},
                status=status.HTTP_403_FORBIDDEN
            )

        certification = self.get_certification(request, id)
        certification.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

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


def get_visible_placement_drives(user):
    drives = PlacementDrive.objects.all()

    # Admin can see all placement drives.
    if user.is_superuser or user.groups.filter(name="Admin").exists():
        return drives

    # Teacher can see drives related to assigned courses.
    if user.groups.filter(name="Teacher").exists():
        assigned_courses = TeacherCourseAssignment.objects.filter(
            teacher=user
        ).values_list("course_id", flat=True)

        if not assigned_courses.exists():
            return drives.none()

        return drives.filter(
            Q(jobs__required_course_id__in=assigned_courses)
            | Q(jobs__required_course__isnull=True)
        ).distinct()

    # Student can see drives related to their own course.
    if user.groups.filter(name="Student").exists():
        student = Student.objects.filter(user=user).first()

        if student is None:
            return drives.none()

        drives = drives.filter(
            Q(jobs__required_course_id=student.Course_id)
            | Q(jobs__required_course__isnull=True)
        ).distinct()

        relevant_jobs = (
            Q(job__required_course_id=student.Course_id)
            | Q(job__required_course__isnull=True)
        )

        eligible_checks = EligibilityCheck.objects.filter(
            student=student,
            job__placement_drive=OuterRef("pk"),
            is_eligible=True,
        ).filter(relevant_jobs)

        any_checks = EligibilityCheck.objects.filter(
            student=student,
            job__placement_drive=OuterRef("pk"),
        ).filter(relevant_jobs)

        return drives.annotate(
            _has_eligible_check=Exists(eligible_checks),
            _has_any_check=Exists(any_checks),
        )

     # Registration Officer can see all placement drives.
    if user.groups.filter(name="Registration Officer").exists():
        return drives

    # Users without an allowed role see no drives.
    return drives.none()


class PlacementDriveListCreateAPIView(APIView):

    permission_classes = [IsAuthenticated, PlacementDrivePermission]

    def get(self, request):
        drives = get_visible_placement_drives(
            request.user
        ).order_by("id")

        # Search filter
        search = request.query_params.get("search")
        if search:
            drives = drives.filter(
                Q(title__icontains=search)
                | Q(description__icontains=search)
                | Q(location__icontains=search)
            )

        # Active/inactive filter
        is_active = request.query_params.get("is_active")
        if is_active is not None and is_active.lower() in ["true", "false"]:
            drives = drives.filter(
                is_active=is_active.lower() == "true"
            )

        # Keep existing pagination
        return paginate(
            drives,
            request,
            PlacementDriveSerializer,
            self,
        )

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
        drive = get_object_or_404(
            get_visible_placement_drives(request.user),
            id=id,
        )
        return Response(PlacementDriveSerializer(drive).data)

    def put(self, request, id):
        drive = get_object_or_404(
            get_visible_placement_drives(request.user),
            id=id,
        )
        serializer = PlacementDriveSerializer(
            drive,
            data=request.data,
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )

    def patch(self, request, id):
        drive = get_object_or_404(
            get_visible_placement_drives(request.user),
            id=id,
        )
        serializer = PlacementDriveSerializer(
            drive,
            data=request.data,
            partial=True,
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request, id):
        drive = get_object_or_404(
            get_visible_placement_drives(request.user),
            id=id,
        )
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
    permission_classes = [IsAuthenticated, EligibilityPermission]

    def post(self, request):
        # Eligibility decisions are made by Teachers for their assigned students.
        if not user_has_role(request.user, "Teacher"):
            return Response({"error": "Only Teachers can check eligibility."}, status=status.HTTP_403_FORBIDDEN)
        student_id = request.data.get("student")
        job_id = request.data.get("job")
        if not student_id or not job_id:
            return Response({"error": "student and job are required."}, status=status.HTTP_400_BAD_REQUEST)
        student = Student.objects.select_related("Course").filter(pk=student_id).first()
        job = Job.objects.filter(pk=job_id).first()
        if student is None:
            return Response({"error": "Student not found."}, status=status.HTTP_404_NOT_FOUND)
        if job is None:
            return Response({"error": "Job not found."}, status=status.HTTP_404_NOT_FOUND)
        assigned = TeacherCourseAssignment.objects.filter(teacher=request.user, course_id=student.Course_id).exists()
        if not assigned:
            return Response({"error": "You can check only students in your assigned courses."}, status=status.HTTP_403_FORBIDDEN)
        result = check_student_eligibility(student, job)
        fingerprint = eligibility_source_fingerprint(student, job)
        check = EligibilityCheck.objects.create(
            student=student, job=job, checked_by=request.user,
            is_eligible=bool(result["is_eligible"]), reason=result.get("reason", ""),
            source_fingerprint=fingerprint
        )
        return Response(EligibilityCheckSerializer(check).data, status=status.HTTP_201_CREATED)


class EligibilityCheckListAPIView(APIView):
    permission_classes = [IsAuthenticated, EligibilityPermission]

    def get(self, request):
        checks = EligibilityCheck.objects.select_related("student", "student__Course", "job", "checked_by").order_by("-checked_at")
        if user_has_role(request.user, "Student"):
            student = Student.objects.filter(user=request.user).first()
            if student is None:
                return Response({"error": "Student profile not found."}, status=status.HTTP_404_NOT_FOUND)
            checks = checks.filter(student=student)
        elif user_has_role(request.user, "Teacher") and not user_has_role(request.user, "Admin"):
            course_ids = TeacherCourseAssignment.objects.filter(teacher=request.user).values_list("course_id", flat=True)
            checks = checks.filter(student__Course_id__in=course_ids, checked_by=request.user)
        elif is_registration_officer(request.user):
            teacher_id = request.query_params.get("teacher")
            if teacher_id:
                course_ids = TeacherCourseAssignment.objects.filter(teacher_id=teacher_id).values_list("course_id", flat=True)
                checks = checks.filter(student__Course_id__in=course_ids, checked_by_id=teacher_id)
            else:
                checks = checks.none()
        elif not user_has_role(request.user, "Admin"):
            return Response({"error": "You do not have permission to view eligibility checks."}, status=status.HTTP_403_FORBIDDEN)
        student_id = request.query_params.get("student")
        job_id = request.query_params.get("job")
        if student_id: checks = checks.filter(student_id=student_id)
        if job_id: checks = checks.filter(job_id=job_id)
        return Response(EligibilityCheckSerializer(checks, many=True).data)



class EligibleStudentsByJobAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        job_id = request.query_params.get("job")

        if not job_id:
            return Response(
                {"error": "Please provide a job ID."},
                status=status.HTTP_400_BAD_REQUEST
            )

        job = Job.objects.filter(pk=job_id).first()

        if job is None:
            return Response(
                {"error": "Job not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        teacher_id = request.query_params.get("teacher")

        checks = (
            EligibilityCheck.objects
            .select_related(
                "student",
                "student__Course",
                "student__user",
                "checked_by"
            )
            .filter(job=job)
            .order_by("-checked_at", "-id")
        )

        if (
            user_has_role(request.user, "Teacher")
            and not user_has_role(request.user, "Admin")
        ):
            checks = checks.filter(checked_by=request.user)

        elif is_registration_officer(request.user):
            if not teacher_id:
                return Response(
                    {"error": "Registration Officer must select a Teacher."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            assigned_course_ids = (
                TeacherCourseAssignment.objects
                .filter(teacher_id=teacher_id)
                .values_list("course_id", flat=True)
            )

            checks = checks.filter(
                checked_by_id=teacher_id,
                student__Course_id__in=assigned_course_ids
            )

        elif not user_has_role(request.user, "Admin"):
            return Response(
                {"error": "You do not have permission to view this list."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Keep only the latest valid eligibility check per student.
        latest_by_student = {}

        for check in checks:
            if check.student_id not in latest_by_student:
                current = eligibility_source_fingerprint(
                    check.student,
                    job
                )

                if (
                    check.source_fingerprint
                    and check.source_fingerprint == current
                ):
                    latest_by_student[check.student_id] = check

        rows = []

        for check in latest_by_student.values():
            interest = JobInterestResponse.objects.filter(
                student=check.student,
                job=job
            ).first()

            already_applied = Application.objects.filter(
                student_id=check.student_id,
                job=job
            ).exists()

            rows.append({
                "student_id": check.student_id,
                "student_name": check.student.Name,
                "email": check.student.Email,
                "phone": check.student.Phone,
                "course": check.student.Course.name,
                "is_eligible": check.is_eligible,
                "reason": check.reason,
                "checked_by": check.checked_by_id,
                "checked_at": check.checked_at,

                "interest_response": (
                    interest.response if interest else None
                ),

                "decline_reason": (
                    interest.decline_reason if interest else ""
                ),

                "already_applied": already_applied,
            })

        eligible_students = [
            row for row in rows if row["is_eligible"]
        ]

        ineligible_students = [
            row for row in rows if not row["is_eligible"]
        ]

        # Students who have not been notified or are awaiting a response.
        # Already-applied students are kept in a separate section.
        pending_students = [
            row for row in eligible_students
            if row["interest_response"] in (None, "pending")
            and not row["already_applied"]
        ]

        accepted_students = [
            row for row in eligible_students
            if row["interest_response"] == "accepted"
        ]

        declined_students = [
            row for row in eligible_students
            if row["interest_response"] == "declined"
        ]

        applied_students = [
            row for row in eligible_students
            if row["already_applied"]
            and row["interest_response"] not in ("accepted", "declined")
        ]

        return Response({
            "job_id": job.id,
            "job_title": job.title,
            "teacher_id": teacher_id,
            "total_checked": len(rows),

            # Keep the original fields for compatibility.
            "eligible_students": eligible_students,
            "ineligible_students": ineligible_students,

            # New separate coordination sections.
            "pending_students": pending_students,
            "accepted_students": accepted_students,
            "declined_students": declined_students,
            "applied_students": applied_students,
        })



class ApplicationListCreateAPIView(APIView):

    permission_classes = [IsAuthenticated, ApplicationPermission]

    def get(self, request):
        applications = Application.objects.select_related(
            "student", "student__Course", "job"
        ).all().order_by("id")

        is_admin = request.user.groups.filter(name="Admin").exists()
        is_teacher = request.user.groups.filter(name="Teacher").exists()
        is_student = request.user.groups.filter(name="Student").exists()

        if is_student:
            try:
                student = request.user.student
            except Student.DoesNotExist:
                return Response(
                    {"error": "Student profile not found."},
                    status=status.HTTP_404_NOT_FOUND
                )

            applications = applications.filter(student=student)

        elif is_teacher and not is_admin:
            assigned_course_ids = TeacherCourseAssignment.objects.filter(
                teacher=request.user
            ).values_list("course_id", flat=True)

            applications = applications.filter(
                student__Course_id__in=assigned_course_ids
            )

        elif is_registration_officer(request.user):
            pass

        job_id = request.query_params.get("job")

        if job_id:
            applications = applications.filter(job_id=job_id)

        search = request.query_params.get("search")

        if search:
            applications = applications.filter(
                job__title__icontains=search
            )

        application_status = request.query_params.get("status")

        if application_status:
            applications = applications.filter(
                status__iexact=application_status
            )

        return paginate(applications, request, ApplicationSerializer, self)

    def post(self, request):
        is_student = request.user.groups.filter(name="Student").exists()

        # Only Students can submit applications.
        if not is_student:
            return Response(
                {"error": "Only Students can submit applications."},
                status=status.HTTP_403_FORBIDDEN
            )

        job_id = request.data.get("job")

        if not job_id:
            return Response(
                {"error": "job is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Always use the logged-in Student's profile.
        try:
            student = request.user.student
        except Student.DoesNotExist:
            return Response(
                {"error": "Student profile not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        job = Job.objects.filter(id=job_id).first()

        if job is None:
            return Response(
                {"error": "Job not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Students may apply even when the saved eligibility result is negative.

        serializer = ApplicationSerializer(
            data={
                "student": student.id,
                "job": job.id,
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


class ApplicationDetailAPIView(APIView):

    permission_classes = [IsAuthenticated, ApplicationPermission]

    def get(self, request, id):
        application = get_object_or_404(Application, id=id)

        is_admin = request.user.groups.filter(name="Admin").exists()
        is_teacher = request.user.groups.filter(name="Teacher").exists()
        is_student = request.user.groups.filter(name="Student").exists()

        # Students can view only their own applications.
        if is_student:
            if application.student.user != request.user:
                return Response(
                    {"error": "You can only view your own application."},
                    status=status.HTTP_403_FORBIDDEN
                )

        # Teachers can view applications only for assigned courses.
        elif is_teacher and not is_admin:
            is_assigned = TeacherCourseAssignment.objects.filter(
                teacher=request.user,
                course=application.student.Course
            ).exists()

            if not is_assigned:
                return Response(
                    {
                        "error": (
                            "You can only view applications for "
                            "students in your assigned courses."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN
                )

        return Response(ApplicationSerializer(application).data)

    def patch(self, request, id):
        return Response(
            {
                "error": (
                    "Application status cannot be changed "
                    "through this endpoint."
                )
            },
            status=status.HTTP_403_FORBIDDEN
        )


class NotificationListCreateAPIView(APIView):

    permission_classes = [IsAuthenticated, NotificationPermission]

    def get(self, request):
        notifications = Notification.objects.all().order_by("-id")

        # Notifications are private to their recipient for every role.
        # Admin may review all notifications.
        if not (request.user.is_superuser or request.user.groups.filter(name="Admin").exists()):
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
        if not (request.user.is_superuser or request.user.groups.filter(name="Admin").exists()):
            return Response(
                {"error": "Only Admin can create notifications directly. Use the relevant workflow for role-based notifications."},
                status=status.HTTP_403_FORBIDDEN
            )

        user_id = request.data.get("user")
        if not user_id:
            return Response(
                {"error": "user is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        
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

        if not (request.user.is_superuser or request.user.groups.filter(name="Admin").exists()):
            if notification.user_id != request.user.id:
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



class StudentDashboardAPIView(APIView):

    permission_classes = [IsAuthenticated, IsStudent]

    def get(self, request):

        # Get the logged-in student's record.
        try:
            student = Student.objects.select_related(
                "Course"
            ).get(user=request.user)

        except Student.DoesNotExist:
            return Response(
                {"error": "Student profile not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Student's academic records.
        academic_records = AcademicRecord.objects.filter(
            student=student
        ).select_related("subject").order_by("semester")

        # Student's applications.
        applications = Application.objects.filter(
            student=student
        ).select_related(
            "job",
            "job__placement_drive",
            "job__placement_drive__company"
        ).order_by("-applied_at")

        # Interviews for this student's applications.
        interviews = Interview.objects.filter(
            application__student=student
        ).select_related(
            "application",
            "application__job"
        ).order_by("interview_date", "interview_time")

        # Selection records for this student's applications.
        selections = Selection.objects.filter(
            application__student=student
        ).select_related(
            "application",
            "application__job"
        )

        return Response(
            {
                "student": StudentSerializer(student).data,

                # Temporarily preserve the existing dashboard structure.
                "profile": {
                    "address": student.address,
                    "date_of_birth": student.date_of_birth,
                },

                "academic_records": AcademicRecordSerializer(
                    academic_records,
                    many=True
                ).data,

                "applications": ApplicationSerializer(
                    applications,
                    many=True
                ).data,

                "interviews": InterviewSerializer(
                    interviews,
                    many=True
                ).data,

                "selections": SelectionSerializer(
                    selections,
                    many=True
                ).data,

                "summary": {
                    "total_academic_records": academic_records.count(),

                    "total_applications": applications.count(),

                    "pending_applications": applications.filter(
                        status="pending"
                    ).count(),

                    "total_interviews": interviews.count(),

                    "total_selections": selections.count(),
                }
            },
            status=status.HTTP_200_OK
        )


class AuditLogListAPIView(APIView):

    permission_classes = [IsAuthenticated, AuditLogPermission]

    def get(self, request):
        audit_logs = AuditLog.objects.all().order_by("-timestamp")

        return paginate(
            audit_logs,
            request,
            AuditLogSerializer,
            self
        )
class InterviewListCreateAPIView(APIView):

    permission_classes = [IsAuthenticated, InterviewPermission]
    def get(self, request):
        interviews = Interview.objects.all().order_by("id")

        # Student: only their own interviews
        if request.user.groups.filter(name="Student").exists():
            student = Student.objects.filter(user=request.user).first()

            if student is None:
                return Response(
                    {"error": "Student profile not found."},
                    status=status.HTTP_404_NOT_FOUND
                )

            interviews = interviews.filter(
                application__student=student
            )

        # Teacher: interviews for students in assigned courses
        elif request.user.groups.filter(name="Teacher").exists():
            assigned_courses = TeacherCourseAssignment.objects.filter(
                teacher=request.user
            ).values_list("course_id", flat=True)

            interviews = interviews.filter(
                application__student__Course_id__in=assigned_courses
            )

        # Admin and Registration Officer can view all interviews.
        elif is_registration_officer(request.user) or user_has_role(request.user, "Admin"):
            pass
        else:
            return Response({"error": "You do not have permission to view interviews."}, status=status.HTTP_403_FORBIDDEN)

        # Search filter
        search = request.query_params.get("search")
        if search:
            interviews = interviews.filter(
                application__job__title__icontains=search
            )

        # Interview status filter
        interview_status = request.query_params.get("status")
        if interview_status:
            interviews = interviews.filter(
                status__iexact=interview_status
            )

        return paginate(
            interviews,
            request,
            InterviewSerializer,
            self
        )


    def post(self, request):
        if not user_has_role(request.user, "Admin"):
            return Response({"error": "Only Admins can schedule interviews."}, status=status.HTTP_403_FORBIDDEN)
        serializer = InterviewSerializer(data=request.data)

        if serializer.is_valid():
            interview = serializer.save()

            # AUTOMATIC NOTIFICATION
            # AUTOMATIC INTERVIEW NOTIFICATION
            student_user = interview.application.student.user

            if student_user is not None:
                interview_mode = interview.interview_type.title()

                if interview.interview_type == "online":
                    interview_details = f"Meeting Link: {interview.meeting_link}"
                else:
                    interview_details = f"Location: {interview.location}"

                Notification.objects.create(
                    user=student_user,
                    notification_type="interview",
                    interview=interview,
                    message=(
                        f"Interview Scheduled!\n"
                        f"Company/Job: {interview.application.job.title}\n"
                        f"Interview Date: {interview.interview_date}\n"
                        f"Interview Time: {interview.interview_time}\n"
                        f"Interview Mode: {interview_mode}\n"
                        f"{interview_details}\n"
                        f"Please be available at the scheduled time."
                    )
                )

            return Response(
                InterviewSerializer(interview).data,
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class InterviewDetailAPIView(APIView):
    permission_classes = [IsAuthenticated, InterviewPermission]

    def get_object(self, request, interview_id):
        interview = Interview.objects.select_related("application__student", "application__student__Course").filter(pk=interview_id).first()
        if interview is None:
            return None
        user = request.user
        if user_has_role(user, "Admin") or is_registration_officer(user):
            return interview
        if user_has_role(user, "Student"):
            student = Student.objects.filter(user=user).first()
            return interview if student and interview.application.student_id == student.id else None
        if user_has_role(user, "Teacher"):
            assigned = TeacherCourseAssignment.objects.filter(teacher=user, course_id=interview.application.student.Course_id).exists()
            return interview if assigned else None
        return None

    def get(self, request, id):
        interview = self.get_object(request, id)
        if interview is None:
            return Response({"error": "Interview not found or you do not have access."}, status=status.HTTP_404_NOT_FOUND)
        return Response(InterviewSerializer(interview).data, status=status.HTTP_200_OK)

    def put(self, request, id):
        return self.update_interview(request, id, partial=False)

    def patch(self, request, id):
        return self.update_interview(request, id, partial=True)

    def update_interview(self, request, id, partial=False):
        if not user_has_role(request.user, "Admin"):
            return Response({"error": "Only Admins can modify interviews."}, status=status.HTTP_403_FORBIDDEN)
        interview = Interview.objects.filter(pk=id).first()
        if interview is None:
            return Response({"error": "Interview not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = InterviewSerializer(interview, data=request.data, partial=partial)
        if serializer.is_valid():
            interview = serializer.save()
            return Response(InterviewSerializer(interview).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        if not user_has_role(request.user, "Admin"):
            return Response({"error": "Only Admins can delete interviews."}, status=status.HTTP_403_FORBIDDEN)
        interview = Interview.objects.filter(pk=id).first()
        if interview is None:
            return Response({"error": "Interview not found."}, status=status.HTTP_404_NOT_FOUND)
        interview.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


def sync_application_status(selection):
    """
    Synchronize the selection decision with the application.
    """

    application = selection.application

    if selection.status == "selected":
        new_status = "selected"

    elif selection.status == "rejected":
        new_status = "rejected"

    elif selection.status == "pending":
        new_status = "shortlisted"

    else:
        return

    if application.status != new_status:
        application.status = new_status
        application.save(update_fields=["status", "updated_at"])


def notify_selection_status(selection):
    """Notify the student about their current selection status."""
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


class SelectionListCreateAPIView(APIView):

    permission_classes = [IsAuthenticated, SelectionPermission]

    def get(self, request):
        selections = Selection.objects.all().order_by("id")

        # ADMIN and Registration Officer → All selections
        if request.user.is_superuser or request.user.groups.filter(name__in=["Admin", "Registration Officer"]).exists():
            pass

        # TEACHER → Selections for students in assigned courses
        elif request.user.groups.filter(name="Teacher").exists():
            assigned_courses = TeacherCourseAssignment.objects.filter(
                teacher=request.user
            ).values_list("course_id", flat=True)

            selections = selections.filter(
                application__student__Course_id__in=assigned_courses
            )

        # STUDENT → Only their own selections
        elif request.user.groups.filter(name="Student").exists():
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

        else:
            return Response(
                {"error": "You do not have permission to view selections."},
                status=status.HTTP_403_FORBIDDEN
            )

        return Response(
            SelectionSerializer(selections, many=True).data,
            status=status.HTTP_200_OK
        )

    def post(self, request):
        # Only Admin can create selections
        if not request.user.groups.filter(name="Admin").exists():
            return Response(
                {"error": "Only Admins can create selections."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = SelectionSerializer(data=request.data)

        if serializer.is_valid():
            selection = serializer.save()

            sync_application_status(selection)
            notify_selection_status(selection)

            return Response(
                SelectionSerializer(selection).data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class SelectionDetailAPIView(APIView):

    permission_classes = [IsAuthenticated, SelectionPermission]

    def get_object(self, request, id):
        # ADMIN and Registration Officer → Can access any selection
        if request.user.is_superuser or request.user.groups.filter(name__in=["Admin", "Registration Officer"]).exists():
            return Selection.objects.filter(id=id).first()

        # TEACHER → Only selections belonging to their assigned courses
        if request.user.groups.filter(name="Teacher").exists():
            assigned_courses = TeacherCourseAssignment.objects.filter(
                teacher=request.user
            ).values_list("course_id", flat=True)

            return Selection.objects.filter(
                id=id,
                application__student__Course_id__in=assigned_courses
            ).first()

        # STUDENT → Only their own selections
        if request.user.groups.filter(name="Student").exists():
            try:
                student = request.user.student
            except Student.DoesNotExist:
                return None

            return Selection.objects.filter(
                id=id,
                application__student=student
            ).first()

        return None

    def get(self, request, id):
        selection = self.get_object(request, id)

        if selection is None:
            return Response(
                {"error": "Selection not found or you do not have access."},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(
            SelectionSerializer(selection).data,
            status=status.HTTP_200_OK
        )

    def put(self, request, id):
        return self.update_selection(request, id, partial=False)

    def patch(self, request, id):
        return self.update_selection(request, id, partial=True)

    def update_selection(self, request, id, partial=False):
        # Preserve full update access for Admin only
        if not (request.user.is_superuser or request.user.groups.filter(name="Admin").exists()):
            return Response(
                {"error": "Only Admins can modify selections."},
                status=status.HTTP_403_FORBIDDEN
            )

        selection = Selection.objects.filter(id=id).first()

        if selection is None:
            return Response(
                {"error": "Selection not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        old_status = selection.status

        serializer = SelectionSerializer(
            selection,
            data=request.data,
            partial=partial
        )

        if serializer.is_valid():
            selection = serializer.save()

            create_audit_log(
                user=request.user,
                action="UPDATE",
                model_name="Selection",
                record_id=selection.id,
                description="Selection record updated"
            )

            if old_status != selection.status:
                sync_application_status(selection)
                notify_selection_status(selection)

            return Response(
                SelectionSerializer(selection).data,
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def delete(self, request, id):
        # Only Admin can delete selections
        if not (
            request.user.is_superuser
            or request.user.groups.filter(name="Admin").exists()
        ):
            return Response(
                {"error": "Only Admins can delete selections."},
                status=status.HTTP_403_FORBIDDEN
            )

        selection = Selection.objects.filter(id=id).first()

        if selection is None:
            return Response(
                {"error": "Selection not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        application = selection.application
        student_user = application.student.user
        job_title = application.job.title

        with transaction.atomic():
            # Reopen the application for further review
            if application.status in ["selected", "rejected"]:
                application.status = "shortlisted"
                application.save(update_fields=["status", "updated_at"])

            create_audit_log(
                user=request.user,
                action="DELETE",
                model_name="Selection",
                record_id=selection.id,
                description="Selection deleted and application returned to shortlisted"
            )

            selection.delete()

            # Inform the student that the decision has been reopened
            if student_user is not None:
                Notification.objects.create(
                    user=student_user,
                    notification_type="selection",
                    message=(
                        f"Your selection decision for {job_title} "
                        "has been reopened for review."
                    )
                )

        return Response(status=status.HTTP_204_NO_CONTENT)

class CourseSubjectListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated, CoursePermission]

    def get(self, request):
        course_id = request.query_params.get("course")

        subjects = CourseSubject.objects.select_related(
            "course", "subject"
        ).order_by("id")

        if course_id:
            subjects = subjects.filter(course_id=course_id)

        serializer = CourseSubjectSerializer(subjects, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = CourseSubjectSerializer(data=request.data)

        if serializer.is_valid():
            course_subject = serializer.save()
            return Response(
                CourseSubjectSerializer(course_subject).data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class CourseSelectionRuleListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated, CoursePermission]

    def get(self, request):
        rules = CourseSelectionRule.objects.select_related(
            "course"
        ).order_by("id")

        course_id = request.query_params.get("course")
        if course_id:
            rules = rules.filter(course_id=course_id)

        serializer = CourseSelectionRuleSerializer(
            rules, many=True
        )
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    def post(self, request):
        serializer = CourseSelectionRuleSerializer(
            data=request.data
        )

        if serializer.is_valid():
            rule = serializer.save()
            return Response(
                CourseSelectionRuleSerializer(rule).data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
    
    def put(self, request, course_id):
        rule = get_object_or_404(
            CourseSelectionRule,
            course_id=course_id
        )

        serializer = CourseSelectionRuleSerializer(
            rule,
            data=request.data
        )

        if serializer.is_valid():
            rule = serializer.save()
            return Response(
                CourseSelectionRuleSerializer(rule).data,
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def patch(self, request, course_id):
        rule = get_object_or_404(
            CourseSelectionRule,
            course_id=course_id
        )

        serializer = CourseSelectionRuleSerializer(
            rule,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            rule = serializer.save()
            return Response(
                CourseSelectionRuleSerializer(rule).data,
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )



class StudentSubjectSelectionAPIView(APIView):
    permission_classes = [IsAuthenticated, IsStudent]

    def get(self, request):
        # Identify the logged-in student's record.
        student = Student.objects.filter(
            user=request.user
        ).select_related("Course").first()

        if not student:
            return Response(
                {"error": "No student record is linked to this account."},
                status=status.HTTP_404_NOT_FOUND
            )

        selection = StudentSubjectSelection.objects.filter(
            student=student
        ).first()

        if not selection:
            return Response(
                {"student": student.id, "selected_subjects": []},
                status=status.HTTP_200_OK
            )

        serializer = StudentSubjectSelectionSerializer(selection)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        # Students can only submit choices for themselves.
        student = Student.objects.filter(
            user=request.user
        ).select_related("Course").first()

        if not student:
            return Response(
                {"error": "No student record is linked to this account."},
                status=status.HTTP_404_NOT_FOUND
            )

        rule = CourseSelectionRule.objects.filter(
            course=student.Course
        ).first()

        if not rule:
            return Response(
                {"error": "Subject-selection rules are not configured for your course."},
                status=status.HTTP_400_BAD_REQUEST
            )

        now = timezone.now()
        selection = StudentSubjectSelection.objects.filter(
            student=student
        ).first()

        # Enforce course deadline and individual reopening.
        if not rule.is_selection_open:
            if not selection or not selection.is_reopened:
                return Response(
                    {"error": "Subject selection is closed for your course."},
                    status=status.HTTP_403_FORBIDDEN
                )
        elif now > rule.selection_deadline:
            if not selection or not selection.is_reopened:
                return Response(
                    {"error": "The subject-selection deadline has passed."},
                    status=status.HTTP_403_FORBIDDEN
                )

        # The client submits only optional and elective subject IDs.
        subject_ids = request.data.get("selected_subjects", [])

        if not isinstance(subject_ids, list):
            return Response(
                {"error": "selected_subjects must be a list of IDs."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Ensure every subject ID is an integer or a numeric string.
        if any(
            isinstance(subject_id, bool)
            or not isinstance(subject_id, (int, str))
            or not str(subject_id).isdigit()
            for subject_id in subject_ids
        ):
            return Response(
                {"error": "Every subject ID must be a valid integer."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Convert IDs to integers before checking duplicates.
        subject_ids = [int(subject_id) for subject_id in subject_ids]

        if len(subject_ids) != len(set(subject_ids)):
            return Response(
                {"error": "Duplicate subject IDs are not allowed."},
                status=status.HTTP_400_BAD_REQUEST
            )


        selected = list(
            CourseSubject.objects.filter(
                id__in=subject_ids,
                course=student.Course
            ).select_related("subject")
        )

        if len(selected) != len(subject_ids):
            return Response(
                {"error": "One or more subjects are invalid for your course."},
                status=status.HTTP_400_BAD_REQUEST
            )

        optional = [
            item for item in selected
            if item.category == "optional"
        ]
        electives = [
            item for item in selected
            if item.category == "elective"
        ]

        if any(item.category == "compulsory" for item in selected):
            return Response(
                {"error": "Submit optional and elective subject IDs only."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if len(optional) != rule.optional_subject_count:
            return Response(
                {
                    "error": (
                        f"Select exactly {rule.optional_subject_count} "
                        "optional subjects."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if len(electives) != rule.elective_subject_count:
            return Response(
                {
                    "error": (
                        f"Select exactly {rule.elective_subject_count} "
                        "additional elective subjects."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        compulsory = CourseSubject.objects.filter(
            course=student.Course,
            category="compulsory"
        )

        available_optional_count = CourseSubject.objects.filter(
            course=student.Course,
            category="optional"
        ).count()

        available_elective_count = CourseSubject.objects.filter(
            course=student.Course,
            category="elective"
        ).count()

        if available_optional_count < rule.optional_subject_count:
            return Response(
                {
                    "error": (
                        "Course configuration is incomplete. "
                        "Not enough optional subjects are available."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if available_elective_count < rule.elective_subject_count:
            return Response(
                {
                    "error": (
                        "Course configuration is incomplete. "
                        "Not enough additional elective subjects are available."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if selection is None:
            selection = StudentSubjectSelection.objects.create(
                student=student
            )

        # Always retain compulsory subjects with the student's choices.
        selection.selected_subjects.set(
            list(compulsory) + selected
        )
        selection.submitted_at = now

        # A successful submission consumes the individual reopening.

        # Record every successful student submission or update.
        was_reopened = selection.is_reopened
        selection.is_reopened = False
        selection.save()

        SubjectSelectionAuditLog.objects.create(
            student_selection=selection,
            admin_user=None,
            action="UPDATE",
            reason=(
                "Student updated subject selection after Admin reopening."
                if was_reopened
                else "Student submitted or updated subject selection."
            )
        )


        serializer = StudentSubjectSelectionSerializer(selection)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

class ReopenStudentSubjectSelectionAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request, selection_id):
        selection = get_object_or_404(
            StudentSubjectSelection,
            pk=selection_id
        )

        reason = request.data.get("reason", "").strip()

        if not reason:
            return Response(
                {"error": "A reason is required to reopen selection."},
                status=status.HTTP_400_BAD_REQUEST
            )

        selection.is_reopened = True
        selection.save(update_fields=["is_reopened"])

        SubjectSelectionAuditLog.objects.create(
            student_selection=selection,
            admin_user=request.user,
            action="REOPEN",
            reason=reason
        )

        return Response(
            {
                "message": "Student subject selection reopened successfully.",
                "selection_id": selection.id,
                "student": selection.student.Name,
                "is_reopened": selection.is_reopened
            },
            status=status.HTTP_200_OK
        )


class AdminStudentSubjectSelectionListAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        selections = StudentSubjectSelection.objects.select_related(
            "student",
            "student__Course"
        ).prefetch_related(
            "selected_subjects__subject",
            "audit_logs__admin_user"
        ).order_by("-id")

        student_id = request.query_params.get("student")
        course_id = request.query_params.get("course")

        if student_id:
            selections = selections.filter(student_id=student_id)

        if course_id:
            selections = selections.filter(
                student__Course_id=course_id
            )

        results = []

        for selection in selections:
            results.append({
                "selection": StudentSubjectSelectionSerializer(
                    selection
                ).data,
                "audit_history": SubjectSelectionAuditLogSerializer(
                    selection.audit_logs.all(),
                    many=True
                ).data
            })

        return Response(results, status=status.HTTP_200_OK)


class SetPasswordAPIView(APIView):

    # This endpoint is used before the user logs in.
    permission_classes = []

    def post(self, request):

        uid = request.data.get("uid")
        token = request.data.get("token")
        password = request.data.get("password")
        confirm_password = request.data.get("confirm_password")

        # 1. Validate required fields.
        if not all([uid, token, password, confirm_password]):
            return Response(
                {"error": "All fields are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. Check that both passwords match.
        if password != confirm_password:
            return Response(
                {"error": "Passwords do not match."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3. Decode the user ID from the invitation link.
        try:
            user_id = urlsafe_base64_decode(uid).decode()
            user = User.objects.get(pk=user_id)
        except (ValueError, TypeError, UnicodeDecodeError, User.DoesNotExist):
            return Response(
                {"error": "This password link is invalid or no longer available."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 4. Validate the invitation token.
        if not default_token_generator.check_token(user, token):
            return Response(
                {"error": "This password link is invalid or expired. Request a new link."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 5. Apply Django's configured password rules.
        try:
            validate_password(password, user=user)
        except ValidationError as exc:
            return Response(
                {"error": list(exc.messages)},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 6. Save the password securely.
        user.set_password(password)
        user.save(update_fields=["password"])

        return Response(
            {"message": "Password set successfully. You can now log in."},
            status=status.HTTP_200_OK
        )

class ForgotPasswordRateThrottle(AnonRateThrottle):
    scope = "forgot_password"

class ForgotPasswordAPIView(APIView):

    # This endpoint must work before login.
    permission_classes = []
    throttle_classes = [ForgotPasswordRateThrottle]

    def post(self, request):
        email = request.data.get("email", "").strip()

        if not email:
            return Response(
                {"error": "Email address is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Use the same response whether the email exists or not.
        # This helps prevent account/email enumeration.
        response_message = (
            "If an account exists for that email, "
            "password reset instructions will be sent."
        )

        users = User.objects.filter(
            email__iexact=email,
            is_active=True,
        )

        for user in users:
            # Don't issue reset links for accounts without a usable password.
            if not user.has_usable_password():
                continue

            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            frontend_url = getattr(
                settings,
                "FRONTEND_URL",
                "http://localhost:5173",
            ).rstrip("/")

            reset_url = (
                f"{frontend_url}/reset-password/"
                f"?uid={uid}&token={token}"
            )

            subject = "Reset your Student PMS password"

            message = (
                f"Hello {user.username},\n\n"
                "We received a request to reset your password.\n\n"
                f"Use this link to choose a new password:\n{reset_url}\n\n"
                "If you did not request this, you can ignore this email."
            )

            try:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=None,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
            except Exception:
                import logging

                logger = logging.getLogger(__name__)
                logger.exception("Failed to send a password-reset email.")
        return Response(
            {"message": response_message},
            status=status.HTTP_200_OK,
        )


class TeacherCourseAssignmentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        is_admin = (
            request.user.is_superuser
            or request.user.groups.filter(name="Admin").exists()
        )
        is_registration_officer_user = is_registration_officer(request.user)

        if not (is_admin or is_registration_officer_user):
            return Response(
                {"error": "You do not have permission to view teacher assignments."},
                status=status.HTTP_403_FORBIDDEN,
            )

        assignments = TeacherCourseAssignment.objects.select_related(
            "teacher", "course"
        ).all()

        serializer = TeacherCourseAssignmentSerializer(assignments, many=True)
        return Response(serializer.data)

    def post(self, request):
        if not (request.user.is_superuser or request.user.groups.filter(name="Admin").exists()):
            return Response(
                {"error": "Only Admin can assign teachers to courses."},
                status=status.HTTP_403_FORBIDDEN
            )

        teacher_id = request.data.get("teacher")
        course_id = request.data.get("course")

        if not teacher_id or not course_id:
            return Response(
                {"error": "Both teacher and course are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        from django.contrib.auth.models import User

        teacher = User.objects.filter(
            id=teacher_id,
            groups__name="Teacher",
            is_active=True
        ).first()

        if not teacher:
            return Response(
                {"error": "Select an active user in the Teacher group."},
                status=status.HTTP_400_BAD_REQUEST
            )

        course = Course.objects.filter(id=course_id).first()

        if not course:
            return Response(
                {"error": "Course not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        assignment, created = TeacherCourseAssignment.objects.get_or_create(
            teacher=teacher,
            course=course
        )

        serializer = TeacherCourseAssignmentSerializer(assignment)

        if not created:
            return Response(
                {
                    "message": "This teacher is already assigned to this course.",
                    "assignment": serializer.data
                },
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )





class SendEligibleJobNotificationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Registration Officer coordinates notifications; Admin may also administer.
        if not (is_registration_officer(request.user) or user_has_role(request.user, "Admin")):
            return Response({"error": "Only Registration Officers can send eligibility notifications."}, status=status.HTTP_403_FORBIDDEN)
        job_id = request.data.get("job")
        teacher_id = request.data.get("teacher")
        student_ids = request.data.get("student_ids")
        if not job_id or not teacher_id:
            return Response({"error": "job and teacher are required."}, status=status.HTTP_400_BAD_REQUEST)
        if not isinstance(student_ids, list) or not student_ids:
            return Response({"error": "Provide a non-empty student_ids list."}, status=status.HTTP_400_BAD_REQUEST)
        job = Job.objects.select_related("placement_drive", "placement_drive__company").filter(pk=job_id).first()
        if job is None:
            return Response({"error": "Job not found."}, status=status.HTTP_404_NOT_FOUND)
        if not job.is_active or not job.placement_drive.is_active:
            return Response({"error": "The job and placement drive must be active."}, status=status.HTTP_400_BAD_REQUEST)
        if not TeacherCourseAssignment.objects.filter(teacher_id=teacher_id).exists():
            return Response({"error": "Selected teacher has no course assignments."}, status=status.HTTP_400_BAD_REQUEST)
        course_ids = set(TeacherCourseAssignment.objects.filter(teacher_id=teacher_id).values_list("course_id", flat=True))
        unique_ids = list(dict.fromkeys(str(value) for value in student_ids))
        students = {str(st.pk): st for st in Student.objects.select_related("Course", "user").filter(pk__in=unique_ids)}
        prepared = []
        for student_id in unique_ids:
            student = students.get(student_id)
            if student is None:
                return Response({"error": f"Student {student_id} was not found."}, status=status.HTTP_400_BAD_REQUEST)
            if student.Course_id not in course_ids:
                return Response({"error": f"Student {student_id} is not in the selected teacher's assigned courses."}, status=status.HTTP_400_BAD_REQUEST)
            check = latest_current_eligibility(student, job, checked_by_id_user(teacher_id))
            if check is None or not check.is_eligible:
                return Response({"error": f"Student {student.Name} does not have a current saved eligible result from the selected teacher."}, status=status.HTTP_400_BAD_REQUEST)
            if student.user is None:
                return Response({"error": f"{student.Name} has no linked user account."}, status=status.HTTP_400_BAD_REQUEST)
            if Application.objects.filter(student=student, job=job).exists():
                return Response({"error": f"{student.Name} has already applied for this job."}, status=status.HTTP_400_BAD_REQUEST)
            existing = JobInterestResponse.objects.filter(
                student=student,
                job=job,
            ).first()

            # Do not send another notification if a response record already exists.
            if existing:
                continue

            prepared.append(student)
        created_count = 0
        with transaction.atomic():
            for student in prepared:
                notification = Notification.objects.create(
                    user=student.user, job=job, notification_type="job",
                    message=f"You have been marked eligible for {job.title} at {job.placement_drive.company.name}. Please accept or decline this opportunity."
                )
                interest, _ = JobInterestResponse.objects.get_or_create(student=student, job=job)
                interest.sent_by = request.user
                interest.notification = notification
                interest.response = "pending"
                interest.decline_reason = ""
                interest.sent_at = timezone.now()
                interest.responded_at = None
                interest.save()
                created_count += 1
        return Response({"message": "Eligibility notifications sent.", "job_id": job.id, "teacher_id": int(teacher_id), "notifications_sent": created_count}, status=status.HTTP_201_CREATED)


def checked_by_id_user(user_id):
    return User.objects.filter(pk=user_id).first()


class JobInterestResponseAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, id=None):
        student = Student.objects.filter(user=request.user).first()
        if student is None or not user_has_role(request.user, "Student"):
            return Response({"error": "Only students can respond to job notifications."}, status=status.HTTP_403_FORBIDDEN)
        response_value = request.data.get("response")
        if response_value not in ("accepted", "declined"):
            return Response({"error": "response must be accepted or declined."}, status=status.HTTP_400_BAD_REQUEST)
        job_id = request.data.get("job")
        if id is not None:
            interest = JobInterestResponse.objects.filter(pk=id, student=student).first()
        else:
            interest = JobInterestResponse.objects.filter(student=student, job_id=job_id).first()
        if interest is None:
            return Response({"error": "Job notification response not found."}, status=status.HTTP_404_NOT_FOUND)
        if interest.response != "pending":
            return Response({"error": "You have already responded to this job."}, status=status.HTTP_400_BAD_REQUEST)
        reason = (request.data.get("decline_reason") or "").strip()
        if response_value == "declined" and not reason:
            return Response({"error": "Please provide a reason for declining."}, status=status.HTTP_400_BAD_REQUEST)
        interest.response = response_value
        interest.decline_reason = reason if response_value == "declined" else ""
        interest.responded_at = timezone.now()
        interest.save(update_fields=["response", "decline_reason", "responded_at"])
        return Response(JobInterestResponseSerializer(interest).data, status=status.HTTP_200_OK)


def _excel_cell_text(value):
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def _excel_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if value in (None, ""):
        return None
    return datetime.strptime(str(value).strip(), "%Y-%m-%d").date()


def _excel_time(value):
    if isinstance(value, datetime):
        return value.time().replace(second=0, microsecond=0)
    if isinstance(value, time):
        return value.replace(second=0, microsecond=0)
    if value in (None, ""):
        return None
    return datetime.strptime(str(value).strip(), "%H:%M").time()



def _read_excel_rows(uploaded_file, required_headers):
    workbook = load_workbook(
        uploaded_file,
        read_only=True,
        data_only=True
    )

    worksheet = (
        workbook["Upload Data"]
        if "Upload Data" in workbook.sheetnames
        else workbook.active
    )

    iterator = worksheet.iter_rows(values_only=True)

    # Read headers from Excel row 1.
    header_row = next(iterator, None)

    if header_row is None:
        workbook.close()
        raise ValueError("The Excel file is empty.")

    headers = [_excel_cell_text(value) for value in header_row]

    missing = [
        header for header in required_headers
        if header not in headers
    ]

    if missing:
        workbook.close()
        raise ValueError(
            "Missing required column(s): " + ", ".join(missing)
        )

    positions = {
        header: headers.index(header)
        for header in required_headers
    }

    rows = []

    # Data starts from Excel row 2.
    for excel_row_number, values in enumerate(iterator, start=2):
        if not values or all(
            value is None or str(value).strip() == ""
            for value in values
        ):
            continue

        rows.append((
            excel_row_number,
            {
                header: (
                    values[index]
                    if index < len(values)
                    else None
                )
                for header, index in positions.items()
            }
        ))

    workbook.close()

    if not rows:
        raise ValueError("The Excel file contains no data rows.")

    return rows




class InterviewShortlistUploadAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    REQUIRED_HEADERS = [
    "Student ID",
    "Student Email",
    "Application ID",
    "Interview Date",
    "Interview Time",
    "Interview Type",
    "Location",
    "Meeting Link",
    "Status",
    "Feedback",
    ]

    @transaction.atomic
    def post(self, request):
        if not user_has_role(request.user, "Admin"):
            return Response(
                {"error": "Only Admins can upload interview shortlists."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = InterviewShortlistUploadSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        # A job must be selected for every new upload.
        if not serializer.validated_data.get("job"):
            return Response(
                {"error": "Please select a job for this interview shortlist."},
                status=status.HTTP_400_BAD_REQUEST
            )

        upload = serializer.save(
            uploaded_by=request.user,
            status="uploaded"
        )

        return Response(
            InterviewShortlistUploadSerializer(upload).data,
            status=status.HTTP_201_CREATED
        )


    def get(self, request):
        if not (
            user_has_role(request.user, "Admin")
            or is_registration_officer(request.user)
        ):
            return Response(
                {"error": "You do not have permission to view uploads."},
                status=status.HTTP_403_FORBIDDEN
            )

        uploads = InterviewShortlistUpload.objects.all().order_by(
            "-uploaded_at"
        )

        return Response(
            InterviewShortlistUploadSerializer(
                uploads,
                many=True
            ).data
        )
    


class InterviewShortlistExtractAPIView(APIView):
    permission_classes = [IsAuthenticated]

    REQUIRED_HEADERS = [
        "Student ID",
        "Student Email",
        "Application ID",
        "Interview Date",
        "Interview Time",
        "Interview Type",
        "Location",
        "Meeting Link",
        "Status",
        "Feedback",
    ]

    def post(self, request, upload_id):
        if not is_registration_officer(request.user):
            return Response(
                {"error": "Only Registration Officers can extract interview shortlists."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            with transaction.atomic():

                upload = get_object_or_404(
                    InterviewShortlistUpload.objects.select_for_update(),
                    pk=upload_id
                )

                if upload.status != "uploaded":
                    return Response(
                        {
                            "error": (
                                "This upload cannot be extracted. "
                                f"Current status: {upload.status}."
                            )
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

                if not upload.job_id:
                    return Response(
                        {"error": "This upload is not associated with a job."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                errors = []
                validated_rows = []
                seen_applications = set()

                rows = _read_excel_rows(
                    upload.file,
                    self.REQUIRED_HEADERS
                )

                upload.total_rows = len(rows)

                # PHASE 1: Validate every Excel row.
                # No interview or application changes happen here.

                for row_number, row in rows:
                    try:
                        student_id = int(
                            _excel_cell_text(row["Student ID"])
                        )

                        student_email = (
                            _excel_cell_text(row["Student Email"])
                            .strip()
                            .casefold()
                        )

                        application_id = int(
                            _excel_cell_text(row["Application ID"])
                        )

                        if not student_email:
                            raise ValueError("Student Email is required.")

                        if application_id in seen_applications:
                            raise ValueError(
                                "Duplicate Application ID in this file."
                            )

                        seen_applications.add(application_id)

                        application = Application.objects.select_related(
                            "student",
                            "job"
                        ).get(
                            pk=application_id,
                            student_id=student_id,
                            job_id=upload.job_id
                        )

                        if (
                            application.student.Email.strip().casefold()
                            != student_email
                        ):
                            raise ValueError(
                                "Student Email does not match the application."
                            )

                        interview_date = _excel_date(
                            row["Interview Date"]
                        )

                        interview_time = _excel_time(
                            row["Interview Time"]
                        )

                        if not interview_date or not interview_time:
                            raise ValueError(
                                "Interview Date and Interview Time are required."
                            )

                        interview_type = (
                            _excel_cell_text(row["Interview Type"]).lower()
                        )

                        if interview_type not in ("online", "offline"):
                            raise ValueError(
                                "Interview Type must be Online or Offline."
                            )

                        interview_status = (
                            _excel_cell_text(row["Status"])
                            .lower()
                            .replace(" ", "_") or "scheduled"
                        )

                        if interview_status not in dict(
                            Interview.STATUS_CHOICES
                        ):
                            raise ValueError("Invalid interview status.")

                        location = _excel_cell_text(row["Location"])
                        meeting_link = _excel_cell_text(row["Meeting Link"])
                        feedback = _excel_cell_text(row["Feedback"])

                        if interview_type == "online" and not meeting_link:
                            raise ValueError(
                                "Meeting Link is required for online interviews."
                            )

                        if interview_type == "offline" and not location:
                            raise ValueError(
                                "Location is required for offline interviews."
                            )

                        validated_rows.append({
                            "application": application,
                            "interview_date": interview_date,
                            "interview_time": interview_time,
                            "interview_type": interview_type,
                            "location": location or None,
                            "meeting_link": meeting_link or None,
                            "status": interview_status,
                            "feedback": feedback,
                        })

                    except (
                        ValueError,
                        TypeError,
                        Application.DoesNotExist,
                        Interview.MultipleObjectsReturned
                    ) as exc:
                        errors.append({
                            "row": row_number,
                            "error": str(exc)
                        })

                # If any row is invalid, do not change interviews or applications.
                if errors:
                    upload.status = "completed_with_errors"
                    upload.failed_rows = len(errors)
                    upload.matched_rows = 0
                    upload.processing_summary = {
                        "errors": errors,
                        "message": (
                            "No interview or application records were changed. "
                            "Correct the file and upload it again."
                        )
                    }
                    upload.processed_at = timezone.now()
                    upload.save()

                    return Response(
                        InterviewShortlistUploadSerializer(upload).data,
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # PHASE 2: All rows passed validation.
                # Now create/update interviews and shortlist applications.

                extracted_interviews = []
                shortlisted_application_ids = []

                for item in validated_rows:
                    interview, created = Interview.objects.update_or_create(
                        application=item["application"],
                        interview_date=item["interview_date"],
                        interview_time=item["interview_time"],
                        defaults={
                            "interview_type": item["interview_type"],
                            "location": item["location"],
                            "meeting_link": item["meeting_link"],
                            "status": item["status"],
                            "feedback": item["feedback"],
                        }
                    )

                    application = item["application"]

                    application.status = "shortlisted"
                    application.save(
                        update_fields=["status", "updated_at"]
                    )

                    shortlisted_application_ids.append(application.id)

                    extracted_interviews.append({
                        "interview_id": interview.id,
                        "application_id": application.id,
                        "student_id": application.student_id,
                        "student_name": application.student.Name,
                        "student_email": application.student.Email,
                        "job_id": application.job_id,
                        "job_title": application.job.title,
                        "interview_date": str(interview.interview_date),
                        "interview_time": str(interview.interview_time),
                        "interview_type": interview.interview_type,
                        "location": interview.location,
                        "meeting_link": interview.meeting_link,
                        "status": interview.status,
                        "feedback": interview.feedback,
                    })

                # Reject omitted applicants for this job,
                # but preserve applications already selected.

                rejected_count = Application.objects.filter(
                    job_id=upload.job_id
                ).exclude(
                    id__in=shortlisted_application_ids
                ).exclude(
                    status="selected"
                ).update(
                    status="rejected",
                    updated_at=timezone.now()
                )

                upload.matched_rows = len(validated_rows)
                upload.failed_rows = 0
                upload.status = "completed"
                upload.processing_summary = {
                    "extracted_interviews": extracted_interviews,
                    "shortlisted_count": len(shortlisted_application_ids),
                    "rejected_count": rejected_count,
                    "notifications_sent": False,
                }
                upload.processed_at = timezone.now()
                upload.save()

                return Response(
                    {
                        "message": "Interview shortlist extracted successfully.",
                        "upload": InterviewShortlistUploadSerializer(upload).data,
                        "extracted_interviews": extracted_interviews,
                        "shortlisted_count": len(shortlisted_application_ids),
                        "rejected_count": rejected_count,
                        "notifications_sent": False,
                    },
                    status=status.HTTP_200_OK
                )

        except Exception as exc:
            # The atomic transaction has already rolled back here.
            try:
                upload = InterviewShortlistUpload.objects.get(
                    pk=upload_id
                )

                upload.status = "failed"
                upload.processing_summary = {
                    "errors": [{"error": str(exc)}],
                    "message": (
                        "Extraction failed. Database changes were rolled back."
                    )
                }
                upload.failed_rows = max(upload.total_rows, 1)
                upload.processed_at = timezone.now()
                upload.save()

            except InterviewShortlistUpload.DoesNotExist:
                pass

            return Response(
                {"error": f"Interview extraction failed: {str(exc)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

class InterviewShortlistSendNotificationsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, upload_id):
        if not is_registration_officer(request.user):
            return Response(
                {"error": "Only Registration Officers can send interview notifications."},
                status=status.HTTP_403_FORBIDDEN
            )

        interview_ids = request.data.get("interview_ids", [])

        if not isinstance(interview_ids, list) or not interview_ids:
            return Response(
                {"error": "Please select at least one interview."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Remove duplicate IDs while preserving their order.
        interview_ids = list(dict.fromkeys(interview_ids))

        try:
            with transaction.atomic():

                upload = get_object_or_404(
                    InterviewShortlistUpload.objects.select_for_update(),
                    pk=upload_id
                )

                if upload.status != "completed":
                    return Response(
                        {"error": "Extract the shortlist successfully before sending notifications."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Only interviews returned by this upload's extraction
                # can be selected for notification.
                extracted_rows = upload.processing_summary.get(
                    "extracted_interviews", []
                )

                extracted_ids = {
                    int(row["interview_id"])
                    for row in extracted_rows
                    if row.get("interview_id") is not None
                }

                try:
                    selected_ids = {int(value) for value in interview_ids}
                except (ValueError, TypeError):
                    return Response(
                        {"error": "Interview IDs must be valid numbers."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                if not selected_ids.issubset(extracted_ids):
                    return Response(
                        {"error": "One or more selected interviews do not belong to this upload."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                interviews = list(
                    Interview.objects.select_related(
                        "application__student__user",
                        "application__job"
                    ).filter(
                        id__in=selected_ids,
                        application__job_id=upload.job_id
                    )
                )

                if len(interviews) != len(selected_ids):
                    return Response(
                        {"error": "Some selected interview records could not be found."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                from students.tasks import send_interview_notification_task

                created_count = 0
                duplicate_count = 0
                skipped_count = 0
                results = []

                for interview in interviews:
                    student = interview.application.student

                    if not student.user_id:
                        skipped_count += 1
                        results.append({
                            "interview_id": interview.id,
                            "student_email": student.Email,
                            "status": "skipped",
                            "reason": "Student has no linked user account."
                        })
                        continue

                    message = (
                        f"Your interview for {interview.application.job.title} "
                        f"is scheduled on {interview.interview_date} "
                        f"at {interview.interview_time}."
                    )

                    notification, created = Notification.objects.get_or_create(
                        user=student.user,
                        interview=interview,
                        notification_type="interview",
                        defaults={
                            "job": interview.application.job,
                            "message": message,
                        }
                    )

                    if created:
                        created_count += 1

                        # Queue the email only after the database transaction commits.
                        transaction.on_commit(
                            lambda interview_id=interview.id:
                                send_interview_notification_task.delay(interview_id)
                        )

                        results.append({
                            "interview_id": interview.id,
                            "student_email": student.Email,
                            "status": "notification_created"
                        })
                    else:
                        duplicate_count += 1
                        results.append({
                            "interview_id": interview.id,
                            "student_email": student.Email,
                            "status": "already_notified"
                        })

                # Update the upload summary without deleting extraction details.
                summary = upload.processing_summary or {}
                summary["notifications_sent"] = True
                summary["notification_results"] = results
                summary["notifications_created"] = created_count
                summary["duplicate_notifications"] = duplicate_count
                summary["skipped_notifications"] = skipped_count

                upload.processing_summary = summary
                upload.save(update_fields=["processing_summary"])

                return Response(
                    {
                        "message": "Interview notification processing completed.",
                        "notifications_created": created_count,
                        "duplicate_notifications": duplicate_count,
                        "skipped_notifications": skipped_count,
                        "results": results,
                    },
                    status=status.HTTP_200_OK
                )

        except Exception as exc:
            return Response(
                {"error": f"Could not send interview notifications: {str(exc)}"},
                status=status.HTTP_400_BAD_REQUEST
            )




class SelectionResultUploadAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    REQUIRED_HEADERS = [
        "Student ID", "Application ID", "Selection Status", "Company Name",
        "Package (LPA)", "Offer Date", "Joining Date", "Remarks"
    ]

    def post(self, request):
        if not user_has_role(request.user, "Admin"):
            return Response(
                {"error": "Only Admins can upload selection results."},
                status=status.HTTP_403_FORBIDDEN
            )

        job_id = request.data.get("job_id")

        if not job_id:
            return Response(
                {"error": "job_id is required. Each final selection upload must cover one job."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            job = Job.objects.select_related(
                "placement_drive__company"
            ).get(pk=job_id)
        except Job.DoesNotExist:
            return Response(
                {"error": "The specified job was not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        confirm_complete = str(
            request.data.get("confirm_complete_final_list", "false")
        ).lower() in ("true", "1", "yes")

        serializer = SelectionResultUploadSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        # Save the upload record outside the processing transaction.
        upload = serializer.save(
            uploaded_by=request.user,
            status="processing",
            is_complete_final_list=confirm_complete
        )

        summary = {
            "created": 0,
            "updated": 0,
            "errors": [],
            "job_id": job.id,
            "complete_list_confirmed": confirm_complete
        }

        try:
            # All selection processing happens inside this transaction.
            with transaction.atomic():

                rows = _read_excel_rows(
                    upload.file,
                    self.REQUIRED_HEADERS
                )

                upload.total_rows = len(rows)

                seen_apps = set()
                included_application_ids = set()

                for row_number, row in rows:
                    try:
                        student_id = int(
                            _excel_cell_text(row["Student ID"])
                        )

                        application_id = int(
                            _excel_cell_text(row["Application ID"])
                        )

                        if application_id in seen_apps:
                            raise ValueError(
                                "Duplicate Application ID in this file."
                            )

                        seen_apps.add(application_id)

                        application = Application.objects.select_related(
                            "student",
                            "job__placement_drive__company"
                        ).get(
                            pk=application_id,
                            student_id=student_id,
                            job_id=job.id
                        )

                        company_name = _excel_cell_text(
                            row["Company Name"]
                        )

                        if (
                            company_name
                            and company_name.casefold()
                            != application.job.placement_drive.company.name.casefold()
                        ):
                            raise ValueError(
                                "Company Name does not match the company for this application."
                            )

                        decision = (
                            _excel_cell_text(row["Selection Status"])
                            .lower()
                            .replace("_", " ")
                        )

                        if decision not in ("selected", "not selected"):
                            raise ValueError(
                                "Selection Status must be Selected or Not Selected."
                            )

                        offer_date = _excel_date(row["Offer Date"])
                        joining_date = _excel_date(row["Joining Date"])

                        package_raw = row["Package (LPA)"]

                        package = (
                            Decimal(str(package_raw))
                            if package_raw not in (None, "")
                            else None
                        )

                        if decision == "selected":
                            if package is None or package <= 0:
                                raise ValueError(
                                    "Package (LPA) must be greater than 0 for Selected rows."
                                )

                            if offer_date is None:
                                raise ValueError(
                                    "Offer Date is required for Selected rows."
                                )

                            if joining_date is None:
                                raise ValueError(
                                    "Joining Date is required for Selected rows."
                                )

                            db_status = "selected"

                        else:
                            if package is not None:
                                raise ValueError(
                                    "Package (LPA) must be empty for Not Selected rows."
                                )

                            if offer_date is not None:
                                raise ValueError(
                                    "Offer Date must be empty for Not Selected rows."
                                )

                            if joining_date is not None:
                                raise ValueError(
                                    "Joining Date must be empty for Not Selected rows."
                                )

                            db_status = "rejected"

                        # Check the existing selection status before updating.
                        existing_status = Selection.objects.filter(
                            application=application
                        ).values_list("status", flat=True).first()

                        selection, created = Selection.objects.update_or_create(
                            application=application,
                            defaults={
                                "status": db_status,
                                "offer_date": offer_date,
                                "joining_date": joining_date,
                                "package": package,
                                "remarks": _excel_cell_text(row["Remarks"]),
                            },
                        )

                        # Send notification only for a new selection
                        # or when its status has changed.
                        status_changed = (
                            created or existing_status != db_status
                        )

                        sync_application_status(selection)

                        if status_changed:
                            notify_selection_status(selection)

                        included_application_ids.add(application.id)

                        if created:
                            summary["created"] += 1
                        else:
                            summary["updated"] += 1

                    except (
                        ValueError,
                        TypeError,
                        InvalidOperation,
                        Application.DoesNotExist,
                        Selection.MultipleObjectsReturned
                    ) as exc:
                        summary["errors"].append({
                            "row": row_number,
                            "error": str(exc)
                        })

                # Only a clean, explicitly confirmed complete list can reject omitted applications.
                if confirm_complete and not summary["errors"]:
                    omitted = Application.objects.filter(
                        job=job
                    ).exclude(
                        id__in=included_application_ids
                    )

                    for application in omitted.select_related("student"):

                        # Check the existing status before updating.
                        existing_status = Selection.objects.filter(
                            application=application
                        ).values_list("status", flat=True).first()

                        selection, created = Selection.objects.update_or_create(
                            application=application,
                            defaults={
                                "status": "rejected",
                                "offer_date": None,
                                "package": None,
                                "joining_date": None,
                                "remarks": "Not included in the Admin-confirmed complete final selection list.",
                            },
                        )

                        status_changed = (
                            created or existing_status != "rejected"
                        )

                        sync_application_status(selection)

                        if status_changed:
                            notify_selection_status(selection)

                        if created:
                            summary["created"] += 1
                        else:
                            summary["updated"] += 1

                    summary["omitted_marked_not_selected"] = omitted.count()

                elif confirm_complete and summary["errors"]:
                    summary["complete_list_action_skipped"] = (
                        "There were row errors; omitted applications were not changed."
                    )

                upload.matched_rows = (
                    summary["created"] + summary["updated"]
                )

                upload.failed_rows = len(summary["errors"])
                upload.processing_summary = summary

                upload.status = (
                    "completed"
                    if not summary["errors"]
                    else (
                        "completed_with_errors"
                        if upload.matched_rows
                        else "failed"
                    )
                )

        except Exception as exc:
            # This handler is outside transaction.atomic().
            # Selection changes are rolled back before this executes.
            upload.status = "failed"

            upload.processing_summary = {
                "errors": [{"error": str(exc)}]
            }

            upload.failed_rows = max(upload.total_rows, 1)

        # Save the final upload status outside the processing transaction.
        upload.processed_at = timezone.now()
        upload.save()

        code = (
            status.HTTP_200_OK
            if upload.status != "failed"
            else status.HTTP_400_BAD_REQUEST
        )

        return Response(
            SelectionResultUploadSerializer(upload).data,
            status=code
        )

    def get(self, request):
        if not (
            user_has_role(request.user, "Admin")
            or is_registration_officer(request.user)
        ):
            return Response(
                {"error": "You do not have permission to view uploads."},
                status=status.HTTP_403_FORBIDDEN
            )

        uploads = SelectionResultUpload.objects.all().order_by(
            "-uploaded_at"
        )

        return Response(
            SelectionResultUploadSerializer(
                uploads,
                many=True
            ).data
        )

class MyStudentSkillsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_student(self, request):
        # Only a Student-group user can access personal skills.
        if not request.user.groups.filter(name="Student").exists():
            return None

        try:
            return request.user.student
        except Student.DoesNotExist:
            return None

    def get(self, request):
        student = self.get_student(request)

        if student is None:
            return Response(
                {"error": "Student access only, or student profile not found."},
                status=status.HTTP_403_FORBIDDEN
            )

        skills = StudentSkill.objects.filter(
            student=student
        ).order_by("id")

        serializer = StudentSkillSerializer(skills, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        student = self.get_student(request)

        if student is None:
            return Response(
                {"error": "Student access only, or student profile not found."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = StudentSkillSerializer(data=request.data)

        if serializer.is_valid():
            name = serializer.validated_data["name"]

            if StudentSkill.objects.filter(
                student=student,
                name__iexact=name
            ).exists():
                return Response(
                    {"name": ["You have already added this skill."]},
                    status=status.HTTP_400_BAD_REQUEST
                )

            skill = serializer.save(student=student)

            return Response(
                StudentSkillSerializer(skill).data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class MyStudentSkillDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_skill(self, request, id):
        if not request.user.groups.filter(name="Student").exists():
            return None, Response(
                {"error": "Student access only."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            student = request.user.student
        except Student.DoesNotExist:
            return None, Response(
                {"error": "Student profile not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        skill = StudentSkill.objects.filter(
            id=id,
            student=student
        ).first()

        if skill is None:
            return None, Response(
                {"error": "Personal skill not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        return skill, None

    def put(self, request, id):
        skill, error = self.get_skill(request, id)

        if error:
            return error

        serializer = StudentSkillSerializer(
            skill,
            data=request.data
        )

        if serializer.is_valid():
            name = serializer.validated_data["name"]

            if StudentSkill.objects.filter(
                student=skill.student,
                name__iexact=name
            ).exclude(id=skill.id).exists():
                return Response(
                    {"name": ["You have already added this skill."]},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer.save(student=skill.student)
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def patch(self, request, id):
        skill, error = self.get_skill(request, id)

        if error:
            return error

        serializer = StudentSkillSerializer(
            skill,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            name = serializer.validated_data.get("name", skill.name)

            if StudentSkill.objects.filter(
                student=skill.student,
                name__iexact=name
            ).exclude(id=skill.id).exists():
                return Response(
                    {"name": ["You have already added this skill."]},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer.save(student=skill.student)
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def delete(self, request, id):
        skill, error = self.get_skill(request, id)

        if error:
            return error

        skill.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)



class ProfileCorrectionRequestListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    ACTIVE_STATUSES = [
        "pending",
        "under_review",
        "more_evidence_required",
    ]

    def get(self, request):
        user = request.user

        is_officer = user.groups.filter(
            name="Registration Officer"
        ).exists()
        is_student = user.groups.filter(name="Student").exists()
        is_teacher = user.groups.filter(name="Teacher").exists()

        requests = ProfileCorrectionRequest.objects.select_related(
            "student", "teacher", "reviewed_by"
        ).order_by("-submitted_at")

        if is_officer:
            pass
        elif is_student:
            requests = requests.filter(student__user=user)
        elif is_teacher:
            requests = requests.filter(teacher=user)
        else:
            return Response(
                {"error": "You are not allowed to view these requests."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = ProfileCorrectionRequestSerializer(
            requests, many=True
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @transaction.atomic
    def post(self, request):
        user = request.user

        is_student = user.groups.filter(name="Student").exists()
        is_teacher = user.groups.filter(name="Teacher").exists()

        # A user must belong to exactly one supported submitter role.
        if is_student == is_teacher:
            return Response(
                {
                    "error": (
                        "Only Student or Teacher users can submit "
                        "profile correction requests."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        student = None
        teacher = None

        if is_student:
            student = get_object_or_404(Student, user=user)
        else:
            teacher = user

        field_name = str(request.data.get("field_name", "")).strip()
        requested_value = str(
            request.data.get("requested_value", "")
        ).strip()
        reason = str(request.data.get("reason", "")).strip()

        if not reason:
            return Response(
                {"error": "Please explain why this profile correction is needed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Accept legacy address and date-of-birth submissions.
        if not requested_value and "requested_address" in request.data:
            field_name = field_name or "address"
            requested_value = str(
                request.data.get("requested_address", "")
            ).strip()

        if (
            not requested_value
            and request.data.get("requested_date_of_birth")
        ):
            field_name = field_name or "date_of_birth"
            requested_value = str(
                request.data.get("requested_date_of_birth", "")
            ).strip()

        if not field_name or not requested_value:
            return Response(
                {
                    "error": (
                        "Provide field_name and requested_value."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Only allow fields that exist on the relevant profile.
        student_fields = {
            "name", "date_of_birth", "address", "phone", "email"
        }
        teacher_fields = {"first_name", "last_name", "email"}

        allowed_fields = (
            student_fields if is_student else teacher_fields
        )

        if field_name not in allowed_fields:
            return Response(
                {
                    "error": (
                        "This field cannot be corrected through "
                        "this request for your role."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        filters = {
            "status__in": self.ACTIVE_STATUSES,
        }

        if student:
            filters["student"] = student
        else:
            filters["teacher"] = teacher

        if ProfileCorrectionRequest.objects.filter(**filters).exists():
            return Response(
                {
                    "error": (
                        "You already have an active profile "
                        "correction request."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Capture the existing value for the reviewer's comparison.
        if student:
            current_values = {
                "name": student.Name,
                "address": student.address,
                "date_of_birth": (
                    str(student.date_of_birth)
                    if student.date_of_birth else ""
                ),
                "phone": student.Phone,
                "email": student.Email,
            }
        else:
            current_values = {
                "first_name": teacher.first_name,
                "last_name": teacher.last_name,
                "email": teacher.email,
            }

        old_value = str(current_values.get(field_name) or "")

        data = request.data.copy()
        data["field_name"] = field_name
        data["requested_value"] = requested_value
        data["reason"] = reason
        data["old_value"] = old_value

        # Keep legacy fields populated for existing clients.
        if field_name == "address":
            data["requested_address"] = requested_value
        elif field_name == "date_of_birth":
            data["requested_date_of_birth"] = requested_value

        serializer = ProfileCorrectionRequestSerializer(data=data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        correction = serializer.save(
            student=student,
            teacher=teacher,
            old_value=old_value,
        )

        # Audit the submission.
        create_audit_log(
            user=user,
            action="CREATE",
            model_name="ProfileCorrectionRequest",
            record_id=correction.id,
            description=(
                f"Profile correction submitted for field "
                f"'{field_name}'."
            ),
        )

        # Notify Registration Officers.
        officers = User.objects.filter(
            groups__name="Registration Officer",
            is_active=True,
        ).distinct()

        target_name = (
            student.Name if student else
            (teacher.get_full_name() or teacher.username)
        )

        for officer in officers:
            Notification.objects.create(
                user=officer,
                notification_type="profile_correction",
                message=(
                    f"{target_name} submitted a correction request "
                    f"#{correction.id} for {field_name}."
                ),
            )

        return Response(
            {
                "message": (
                    "Correction request submitted. "
                    "Your profile will change only after approval."
                ),
                "request": ProfileCorrectionRequestSerializer(
                    correction
                ).data,
            },
            status=status.HTTP_201_CREATED,
        )


class ProfileCorrectionRequestEditAPIView(APIView):
    permission_classes = [IsAuthenticated]

    EDITABLE_STATUSES = ["pending", "more_evidence_required"]

    @transaction.atomic
    def patch(self, request, id):
        user = request.user

        is_student = user.groups.filter(name="Student").exists()
        is_teacher = user.groups.filter(name="Teacher").exists()

        if is_student == is_teacher:
            return Response(
                {"error": "Only Student or Teacher users can edit requests."},
                status=status.HTTP_403_FORBIDDEN,
            )

        correction = get_object_or_404(
            ProfileCorrectionRequest.objects.select_for_update(),
            id=id,
        )

        # Users may edit only their own requests.
        if is_student:
            if not correction.student or correction.student.user_id != user.id:
                return Response(
                    {"error": "You can edit only your own requests."},
                    status=status.HTTP_403_FORBIDDEN,
                )
        else:
            if not correction.teacher or correction.teacher_id != user.id:
                return Response(
                    {"error": "You can edit only your own requests."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        if correction.status not in self.EDITABLE_STATUSES:
            return Response(
                {
                    "error": (
                        "Only pending requests or requests requiring "
                        "more evidence can be edited."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        field_name = str(
            request.data.get("field_name", correction.field_name)
        ).strip()
        requested_value = str(
            request.data.get("requested_value", correction.requested_value or "")
        ).strip()
        reason = str(
            request.data.get("reason", correction.reason or "")
        ).strip()

        if not field_name or not requested_value or not reason:
            return Response(
                {
                    "error": (
                        "Field name, requested value, and reason "
                        "are all required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        allowed_fields = (
            {"name", "date_of_birth", "address", "phone", "email"}
            if is_student
            else {"first_name", "last_name", "email"}
        )

        if field_name not in allowed_fields:
            return Response(
                {"error": "This profile field is not supported."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Do not allow a request for a value already in the profile.
        if correction.student:
            student = correction.student
            current_values = {
                "name": student.Name,
                "date_of_birth": (
                    str(student.date_of_birth)
                    if student.date_of_birth else ""
                ),
                "address": student.address,
                "phone": student.Phone,
                "email": student.Email,
            }
        else:
            teacher = correction.teacher
            current_values = {
                "first_name": teacher.first_name,
                "last_name": teacher.last_name,
                "email": teacher.email,
            }

        old_value = str(current_values.get(field_name) or "")

        if requested_value == old_value:
            return Response(
                {
                    "error": (
                        "The requested value is already the current value. "
                        "Please enter a different value."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        correction.field_name = field_name
        correction.requested_value = requested_value
        correction.reason = reason
        correction.old_value = old_value

        # Keep legacy fields in sync with the primary request value.
        if field_name == "address":
            correction.requested_address = requested_value
        elif field_name == "date_of_birth":
            correction.requested_date_of_birth = requested_value

        # Editing resets the previous review decision and reviewer details.
        correction.reviewed_by = None
        correction.reviewed_at = None
        correction.rejection_reason = ""
        correction.decision_note = ""
        correction.status = "pending"

        correction.save()

        create_audit_log(
            user=user,
            action="UPDATE",
            model_name="ProfileCorrectionRequest",
            record_id=correction.id,
            description=(
                f"User edited profile correction request "
                f"#{correction.id} for '{field_name}'."
            ),
        )

        return Response(
            {
                "message": "Correction request updated and returned to pending review.",
                "request": ProfileCorrectionRequestSerializer(correction).data,
            },
            status=status.HTTP_200_OK,
        )



class ProfileCorrectionRequestReviewAPIView(APIView):
    permission_classes = [IsAuthenticated]

    ACTIVE_STATUSES = [
        "pending",
        "under_review",
        "more_evidence_required",
    ]

    @transaction.atomic
    def patch(self, request, id):
        from datetime import date
        import re
        from django.core.exceptions import ValidationError
        from django.core.validators import validate_email
        
        if not request.user.groups.filter(
        name="Registration Officer"
        ).exists():
            return Response(
            {"error": "Only Registration Officers can review requests."},
            status=status.HTTP_403_FORBIDDEN,
        )

        
        correction = get_object_or_404(
            ProfileCorrectionRequest.objects.select_for_update(
                of=("self",)
            ).select_related(
                "student", "teacher"
            ),
            id=id,
        )


        if correction.status not in self.ACTIVE_STATUSES:
            return Response(
                {"error": "This request is already closed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        decision = str(request.data.get("status", "")).strip()
        reason = str(request.data.get("rejection_reason", "")).strip()
        decision_note = str(request.data.get("decision_note", "")).strip()

        allowed_decisions = {
            "under_review",
            "more_evidence_required",
            "approved",
            "rejected",
        }

        if decision not in allowed_decisions:
            return Response(
                {
                    "error": (
                        "Status must be under_review, "
                        "more_evidence_required, approved, or rejected."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if decision == "rejected" and not reason:
            return Response(
                {"error": "Please provide a rejection_reason."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if decision == "more_evidence_required" and not decision_note:
            return Response(
                {
                    "error": (
                        "Explain what additional evidence is required "
                        "in decision_note."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Determine the target user for notifications.
        if correction.student:
            target_user = correction.student.user
        else:
            target_user = correction.teacher

        if decision == "approved":
            # Evidence is checked for this request before profile changes.
            documents = list(correction.documents.all())

            # OCR results assist review; they do not authenticate documents.
            has_usable_ocr_match = any(
                document.ocr_result == "match"
                and bool((document.ocr_text or "").strip())
                for document in documents
            )

            if not documents and not decision_note:
                return Response(
                    {
                        "error": (
                            "Upload supporting evidence or provide a "
                            "decision_note documenting the alternative "
                            "manual verification before approval."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if documents and not has_usable_ocr_match and not decision_note:
                return Response(
                    {
                        "error": (
                            "OCR could not confirm the requested value. "
                            "Review the evidence manually and provide "
                            "your verification findings in decision_note."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            field_name = correction.field_name

            new_value = str(
                correction.requested_value or ""
            ).strip()

            if not new_value:
                new_value = str(
                    correction.requested_address or ""
                ).strip()

            if (
                not new_value
                and correction.requested_date_of_birth
            ):
                new_value = str(correction.requested_date_of_birth)

            if not new_value:
                return Response(
                    {
                        "error": (
                            "The request has no usable requested value."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if correction.student:
                student = correction.student

                if field_name == "name":
                    student.Name = new_value
                    student.save(update_fields=["Name"])

                elif field_name == "address":
                    student.address = new_value
                    student.save(update_fields=["address"])

                elif field_name == "date_of_birth":
                    try:
                        parsed_date = date.fromisoformat(new_value)
                    except ValueError:
                        return Response(
                            {
                                "error": (
                                    "Date of birth must use YYYY-MM-DD."
                                )
                            },
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                    student.date_of_birth = parsed_date
                    student.save(update_fields=["date_of_birth"])

                elif field_name == "phone":
                    digits = re.sub(r"\D", "", new_value)

                    if not 10 <= len(digits) <= 15:
                        return Response(
                            {
                                "error": (
                                    "Enter a valid phone number containing "
                                    "10 to 15 digits."
                                )
                            },
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                    phone_field = student._meta.get_field("Phone")

                    if (
                        phone_field.max_length
                        and len(new_value) > phone_field.max_length
                    ):
                        return Response(
                            {"error": "The phone number is too long."},
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                    student.Phone = new_value
                    student.save(update_fields=["Phone"])

                elif field_name == "email":
                    try:
                        validate_email(new_value)
                    except ValidationError:
                        return Response(
                            {"error": "Enter a valid email address."},
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                    duplicate = Student.objects.filter(
                        Email__iexact=new_value
                    ).exclude(pk=student.pk).exists()

                    if duplicate:
                        return Response(
                            {
                                "error": (
                                    "This email address is already used "
                                    "by another student."
                                )
                            },
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                    student.Email = new_value
                    student.save(update_fields=["Email"])

                else:
                    return Response(
                        {
                            "error": (
                                "This student profile field is not "
                                "supported for approval. Photo corrections "
                                "require a separate implementation."
                            )
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                target_user = student.user

            elif correction.teacher:
                teacher = correction.teacher

                if field_name == "first_name":
                    teacher.first_name = new_value
                    teacher.save(update_fields=["first_name"])

                elif field_name == "last_name":
                    teacher.last_name = new_value
                    teacher.save(update_fields=["last_name"])

                elif field_name == "email":
                    try:
                        validate_email(new_value)
                    except ValidationError:
                        return Response(
                            {"error": "Enter a valid email address."},
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                    duplicate = User.objects.filter(
                        email__iexact=new_value
                    ).exclude(pk=teacher.pk).exists()

                    if duplicate:
                        return Response(
                            {
                                "error": (
                                    "This email address is already used "
                                    "by another user."
                                )
                            },
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                    teacher.email = new_value
                    teacher.save(update_fields=["email"])

                else:
                    return Response(
                        {
                            "error": (
                                "This teacher profile field is not "
                                "supported for approval."
                            )
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                target_user = teacher

            else:
                return Response(
                    {
                        "error": (
                            "This request is not linked to a "
                            "student or teacher."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Update the review decision after the requested changes succeed.
        correction.status = decision
        correction.reviewed_by = request.user
        correction.reviewed_at = timezone.now()
        correction.rejection_reason = (
            reason if decision == "rejected" else ""
        )
        correction.decision_note = decision_note

        correction.save(
            update_fields=[
                "status",
                "reviewed_by",
                "reviewed_at",
                "rejection_reason",
                "decision_note",
            ]
        )

        create_audit_log(
            user=request.user,
            action="UPDATE",
            model_name="ProfileCorrectionRequest",
            record_id=correction.id,
            description=(
                f"Correction request #{correction.id} "
                f"reviewed with decision '{decision}'."
            ),
        )

        if target_user:
            message = (
                f"Your profile correction request #{correction.id} "
                f"is now {decision.replace('_', ' ')}."
            )

            if decision == "rejected":
                message += f" Reason: {reason}"

            if decision == "more_evidence_required":
                message += f" Details: {decision_note}"

            Notification.objects.create(
                user=target_user,
                notification_type="profile_correction",
                message=message,
            )

        return Response(
            {
                "message": (
                    f"Profile correction request "
                    f"{decision.replace('_', ' ')}."
                ),
                "request": ProfileCorrectionRequestSerializer(
                    correction
                ).data,
            },
            status=status.HTTP_200_OK,
        )

class CorrectionDocumentUploadAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
    MAX_PDF_PAGES = 20
    ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
    OCR_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}

    def post(self, request, id):
        import os

        from PIL import Image
        import pymupdf

        correction = get_object_or_404(
            ProfileCorrectionRequest.objects.select_related(
                "student", "teacher"
            ),
            id=id,
        )

        user = request.user

        is_officer = user.groups.filter(
            name="Registration Officer"
        ).exists()

        owns_student_request = (
            correction.student is not None
            and correction.student.user_id == user.id
        )

        owns_teacher_request = correction.teacher_id == user.id

        if not (
            is_officer
            or owns_student_request
            or owns_teacher_request
        ):
            return Response(
                {
                    "error": (
                        "You are not allowed to upload evidence "
                        "for this request."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if correction.status not in {
            "pending",
            "under_review",
            "more_evidence_required",
        }:
            return Response(
                {
                    "error": (
                        "Evidence cannot be uploaded to a closed request."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        uploaded_file = request.FILES.get("file")
        document_type = str(
            request.data.get("document_type", "")
        ).strip()

        if not uploaded_file:
            return Response(
                {"error": "Please attach an evidence file."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not document_type:
            return Response(
                {"error": "Please specify the document type."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if uploaded_file.size > self.MAX_FILE_SIZE:
            return Response(
                {"error": "The maximum allowed file size is 5 MB."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        extension = os.path.splitext(uploaded_file.name)[1].lower()

        if extension not in self.ALLOWED_EXTENSIONS:
            return Response(
                {
                    "error": (
                        "Only PDF, JPG, JPEG, and PNG files are allowed."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate file content instead of trusting the extension alone.
        try:
            uploaded_file.seek(0)

            if extension in self.OCR_IMAGE_EXTENSIONS:
                with Image.open(uploaded_file) as image:
                    image.verify()

                uploaded_file.seek(0)

            elif extension == ".pdf":
                pdf_bytes = uploaded_file.read()

                with pymupdf.open(
                    stream=pdf_bytes,
                    filetype="pdf",
                ) as pdf:
                    if pdf.page_count < 1:
                        raise ValueError("The PDF contains no pages.")
                    if pdf.page_count > self.MAX_PDF_PAGES:
                        return Response(
                            {
                                "error": (
                                    f"PDF files may contain at most "
                                    f"{self.MAX_PDF_PAGES} pages."
                                )
                            },
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                uploaded_file.seek(0)

        except Exception:
            uploaded_file.seek(0)
            return Response(
                {
                    "error": (
                        "The uploaded file is invalid or corrupted. "
                        "Please upload a valid PDF or image."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Save evidence before running OCR so it remains available
        # if OCR cannot read the document.
        document = CorrectionDocument.objects.create(
            correction_request=correction,
            uploaded_by=user,
            document_type=document_type,
            file=uploaded_file,
        )

        try:
            if extension in self.OCR_IMAGE_EXTENSIONS:
                extracted_text, ocr_error = extract_text_from_image(
                    document.file.path
                )
            else:
                extracted_text, ocr_error = extract_text_from_pdf(
                    document.file.path
                )

        except Exception:
            extracted_text = ""
            ocr_error = (
                "OCR processing failed. Manual review is required."
            )

        extracted_text = extracted_text or ""
        ocr_error = ocr_error or ""

        document.ocr_text = extracted_text
        document.ocr_warning = ocr_error

        if ocr_error or not extracted_text.strip():
            document.ocr_result = "unable_to_verify"

            if not document.ocr_warning:
                document.ocr_warning = (
                    "No readable text was found. Manual review is required."
                )

        else:
            requested_value = str(
                correction.requested_value or ""
            ).strip()

            if not requested_value:
                requested_value = str(
                    correction.requested_address or ""
                ).strip()

            if (
                not requested_value
                and correction.requested_date_of_birth
            ):
                requested_value = str(
                    correction.requested_date_of_birth
                )

            document.ocr_result = compare_document_text(
                extracted_text=extracted_text,
                requested_value=requested_value,
                field_name=correction.field_name,
            )

            if document.ocr_result == "unable_to_verify":
                document.ocr_warning = (
                    "The document text could not be reliably matched. "
                    "Manual review is required."
                )

        document.save(
            update_fields=[
                "ocr_text",
                "ocr_warning",
                "ocr_result",
            ]
        )

        create_audit_log(
            user=user,
            action="CREATE",
            model_name="CorrectionDocument",
            record_id=document.id,
            description=(
                f"Evidence uploaded for profile correction request "
                f"#{correction.id}. OCR result: {document.ocr_result}."
            ),
        )

        return Response(
            {
                "message": (
                    "Evidence uploaded successfully. "
                    "The Registration Officer must review the evidence."
                ),
                "document": CorrectionDocumentSerializer(
                    document
                ).data,
            },
            status=status.HTTP_201_CREATED,
        )
