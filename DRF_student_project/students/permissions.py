
from rest_framework.permissions import BasePermission, SAFE_METHODS


def in_group(user, *names):
    return (
        user.is_authenticated
        and user.groups.filter(name__in=names).exists()
    )


def is_admin(user):
    return user.is_authenticated and (
        user.is_superuser or in_group(user, "Admin")
    )


def is_assigned_teacher_for_student(user, student):
    from .models import TeacherCourseAssignment

    return TeacherCourseAssignment.objects.filter(
        teacher=user,
        course_id=student.Course_id
    ).exists()


# ---------- Basic custom permissions ----------

class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or is_admin(request.user)


class IsStaffOrreadonly(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS or (
            request.user and request.user.is_staff
        )


class IsStudentOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


# ---------- Reusable role-based permissions ----------

class RoleBasedPermission(BasePermission):
    allowed_roles = []

    def has_permission(self, request, view):
        return in_group(request.user, *self.allowed_roles)


class IsAdminOrTeacher(RoleBasedPermission):
    allowed_roles = ["Admin", "Teacher"]


class IsAdmin(RoleBasedPermission):
    allowed_roles = ["Admin"]


class IsTeacher(RoleBasedPermission):
    allowed_roles = ["Teacher"]


class IsStudent(RoleBasedPermission):
    allowed_roles = ["Student"]


class RoleMethodPermission(BasePermission):
    role_methods = {}

    def has_permission(self, request, view):
        if is_admin(request.user):
            return request.method in self.role_methods.get(
                "Admin", []
            )

        for role, methods in self.role_methods.items():
            if in_group(request.user, role):
                return request.method in methods

        return False


# ---------- Student ----------

class StudentManagementPermissions(BasePermission):
    """
    Admin: full access.
    Teacher: read-only access.
    Registration Officer: read-only access.
    Student: no access to student management.
    """

    def has_permission(self, request, view):
        if is_admin(request.user):
            return True

        return (
            request.method in SAFE_METHODS
            and in_group(request.user, "Teacher", "Registration Officer")
        )


class StudentDetailPermission(BasePermission):
    """
    Admin: full access.
    Teacher: read-only access to assigned-course students.
    Registration Officer: read-only access to all students.
    """

    def has_permission(self, request, view):
        if is_admin(request.user):
            return True

        if in_group(request.user, "Teacher", "Registration Officer"):
            return request.method in SAFE_METHODS

        return False

    def has_object_permission(self, request, view, obj):
        if is_admin(request.user):
            return True

        if in_group(request.user, "Registration Officer"):
            return request.method in SAFE_METHODS

        if in_group(request.user, "Teacher"):
            return (
                request.method in SAFE_METHODS
                and is_assigned_teacher_for_student(request.user, obj)
            )

        return False


class StudentDetailAllPermission(RoleMethodPermission):
    """
    Used for student profile/detail operations.
    Teachers are restricted to assigned-course students.
    """

    role_methods = {
        "Admin": ["GET", "PUT", "PATCH", "DELETE"],
        "Teacher": ["GET"],
        "Student": ["GET"],
        "Registration Officer": ["GET"],
    }

    def has_object_permission(self, request, view, obj):
        if is_admin(request.user):
            return True

        if in_group(request.user, "Student"):
            return (
                request.method == "GET"
                and obj.user_id == request.user.id
            )

        if in_group(request.user, "Teacher"):
            return (
                request.method == "GET"
                and is_assigned_teacher_for_student(request.user, obj)
            )

        if in_group(request.user, "Registration Officer"):
            return request.method == "GET"

        return False


class StudentImageDeletePermission(BasePermission):
    def has_permission(self, request, view):
        return is_admin(request.user)


# ---------- Academic record ----------

class AcademicRecordPermission(BasePermission):
    """
    Admin: full access.
    Teacher: view-only for assigned-course students.
    Registration Officer: view-only.
    Student: view-only for own records.
    """
    
    def has_permission(self, request, view):
        if is_admin(request.user):
            return True

        # All three roles can view academic records
        if request.method in SAFE_METHODS:
            return in_group(
                request.user,
                "Teacher",
                "Registration Officer",
                "Student"
            )

        # Teacher can PATCH attendance only
        if in_group(request.user, "Teacher"):
            return (
                request.method == "PATCH"
                and set(request.data.keys()) == {"attendance"}
            )

        return False

    def has_object_permission(self, request, view, obj):
        if is_admin(request.user):
            return True

        # Student can view only their own records
        if in_group(request.user, "Student"):
            return (
                request.method in SAFE_METHODS
                and obj.student.user_id == request.user.id
            )

        # Teacher can access assigned students' records
        if in_group(request.user, "Teacher"):
            return (
                is_assigned_teacher_for_student(
                    request.user, obj.student
                )
                and (
                    request.method in SAFE_METHODS
                    or (
                        request.method == "PATCH"
                        and set(request.data.keys()) == {"attendance"}
                    )
                )
            )

        # Registration Officer is view-only
        if in_group(request.user, "Registration Officer"):
            return request.method in SAFE_METHODS

        return False


# ---------- Skill master data ----------

class SkillPermission(BasePermission):
    def has_permission(self, request, view):
        if is_admin(request.user):
            return True

        if in_group(request.user, "Student"):
            return request.method in SAFE_METHODS

        return False


# ---------- Certification ----------

class CertificationPermission(BasePermission):
    def has_permission(self, request, view):
        if is_admin(request.user):
            return request.method in SAFE_METHODS

        if in_group(
            request.user,
            "Teacher",
            "Registration Officer"
        ):
            return request.method in SAFE_METHODS

        if in_group(request.user, "Student"):
            return request.method in SAFE_METHODS or request.method in [
                "POST", "PUT", "PATCH", "DELETE"
            ]

        return False

    def has_object_permission(self, request, view, obj):
        if is_admin(request.user):
            return True

        if in_group(request.user, "Student"):
            return obj.student.user_id == request.user.id

        if in_group(request.user, "Teacher"):
            return (
                request.method in SAFE_METHODS
                and is_assigned_teacher_for_student(
                    request.user, obj.student
                )
            )

        if in_group(request.user, "Registration Officer"):
            return request.method in SAFE_METHODS

        return False


# ---------- Company ----------

class CompanyPermission(BasePermission):
    def has_permission(self, request, view):
        if is_admin(request.user):
            return True

        return (
            request.method in SAFE_METHODS
            and in_group(
                request.user,
                "Teacher",
                "Student",
                "Registration Officer"
            )
        )


# ---------- Placement drive ----------

class PlacementDrivePermission(BasePermission):
    def has_permission(self, request, view):
        if is_admin(request.user):
            return True

        return (
            request.method in SAFE_METHODS
            and in_group(
                request.user,
                "Teacher",
                "Student",
                "Registration Officer"
            )
        )


# ---------- Job ----------

class JobPermission(BasePermission):
    def has_permission(self, request, view):
        if is_admin(request.user):
            return True

        return (
            request.method in SAFE_METHODS
            and in_group(
                request.user,
                "Teacher",
                "Student",
                "Registration Officer"
            )
        )


# ---------- Eligibility ----------

class EligibilityPermission(BasePermission):
    """
    Teacher: can perform eligibility checks and view checks.
    Registration Officer: can view saved eligibility results.
    Student: can view own eligibility results.
    Admin: does not perform eligibility checks.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.method == "POST":
            return in_group(request.user, "Teacher")

        if request.method == "GET":
            return in_group(
                request.user,
                "Teacher",
                "Registration Officer",
                "Student"
            )

        return False


# ---------- Application ----------

class ApplicationPermission(BasePermission):
    """
    Admin: view-only.
    Teacher: view-only.
    Registration Officer: view-only.
    Student: view and create own applications.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Admin can only view applications.
        if is_admin(request.user):
            return request.method in SAFE_METHODS

        # Teachers and Registration Officers can only view.
        if in_group(
            request.user,
            "Teacher",
            "Registration Officer"
        ):
            return request.method in SAFE_METHODS

        # Students can view and create applications.
        if in_group(request.user, "Student"):
            return (
                request.method in SAFE_METHODS
                or request.method == "POST"
            )

        return False


# ---------- Interview ----------


class InterviewPermission(BasePermission):

    def has_permission(self, request, view):

        if not request.user or not request.user.is_authenticated:
            return False

        # Get the user's Django groups
        groups = list(
            request.user.groups.values_list("name", flat=True)
        )

        # DEBUG INFORMATION
        print("========== INTERVIEW PERMISSION DEBUG ==========")

        print("USER:", request.user.username)
        print("AUTHENTICATED:", request.user.is_authenticated)
        print("USERNAME:", request.user.username)
        print("METHOD:", request.method)
        print("GROUPS:", groups)

        print("IS ADMIN:", is_admin(request.user))

        print(
            "IN ALLOWED GROUP:",
            in_group(
                request.user,
                "Teacher",
                "Student",
                "Registration Officer"
            )
        )

        print("================================================")

        # Admin can access all interview operations
        if is_admin(request.user):
            return True

        # Teacher, Student and Registration Officer
        # can perform read-only operations
        return (
            request.method in SAFE_METHODS
            and in_group(
                request.user,
                "Teacher",
                "Student",
                "Registration Officer"
            )
        )


# ---------- Selection ----------

class SelectionPermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if is_admin(request.user):
            return True

        return (
            request.method in SAFE_METHODS
            and in_group(
                request.user,
                "Teacher",
                "Student",
                "Registration Officer"
            )
        )


# ---------- Notification ----------

class NotificationPermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if is_admin(request.user):
            return True

        if in_group(
            request.user,
            "Teacher",
            "Registration Officer"
        ):
            return request.method in SAFE_METHODS

        if in_group(request.user, "Student"):
            return request.method in ["GET", "PATCH"]

        return False


# ---------- Dashboard / Audit logs ----------

class DashboardPermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        return in_group(
            request.user,
            "Admin",
            "Teacher",
            "Registration Officer"
        )


class AuditLogPermission(BasePermission):
    def has_permission(self, request, view):
        return is_admin(request.user)


# ---------- Course ----------

class CoursePermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if is_admin(request.user):
            return True

        return (
            request.method in SAFE_METHODS
            and in_group(
                request.user,
                "Teacher",
                "Student",
                "Registration Officer"
            )
        )


# ---------- Student profile ----------

class StudentProfilePermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if is_admin(request.user):
            return True

        if in_group(request.user, "Teacher", "Registration Officer"):
            return request.method in SAFE_METHODS

        if in_group(request.user, "Student"):
            return request.method in ["GET", "POST", "PUT", "PATCH"]

        return False

    def has_object_permission(self, request, view, obj):
        if is_admin(request.user):
            return True

        if in_group(request.user, "Student"):
            return obj.user_id == request.user.id

        if in_group(request.user, "Teacher"):
            return (
                request.method in SAFE_METHODS
                and is_assigned_teacher_for_student(request.user, obj)
            )

        if in_group(request.user, "Registration Officer"):
            return request.method in SAFE_METHODS

        return False


# ---------- Subject ----------

class SubjectPermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if is_admin(request.user):
            return True

        return (
            request.method in SAFE_METHODS
            and in_group(
                request.user,
                "Teacher",
                "Student",
                "Registration Officer"
            )
        )
