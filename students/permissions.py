from rest_framework.permissions import BasePermission, SAFE_METHODS


def in_group(user, *names):
    return user.is_authenticated and user.groups.filter(
        name__in=names
    ).exists()


# ---------- Basic custom permissions ----------

class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or (
            request.user and request.user.is_staff
        )


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
        for role, methods in self.role_methods.items():
            if in_group(request.user, role):
                return request.method in methods
        return False


# ---------- Student ----------

class StudentManagementPermissions(BasePermission):
    def has_permission(self, request, view):
        if in_group(request.user, "Admin"):
            return True
        if in_group(request.user, "Teacher"):
            return request.method in ["GET", "POST", "PUT", "PATCH"]
        if in_group(request.user, "Student"):
            return request.method == "GET"
        return False


class StudentDetailPermission(BasePermission):

    def has_permission(self, request, view):
        if in_group(request.user, "Admin"):
            return True
        if in_group(request.user, "Teacher"):
            return request.method in ["GET", "PUT", "PATCH"]
        if in_group(request.user, "Student"):
            return request.method == "GET"
        return False

    def has_object_permission(self, request, view, obj):
        if in_group(request.user, "Admin"):
            return True
        if in_group(request.user, "Teacher"):
            return True
        if in_group(request.user, "Student"):
            return obj.user == request.user
        return False


class StudentDetailAllPermission(RoleMethodPermission):
    role_methods = {
        "Admin": ["GET", "PUT", "PATCH", "DELETE"],
        "Teacher": ["GET", "PUT", "PATCH"],
        "Student": ["GET"],
    }

    def has_object_permission(self, request, view, obj):
        if in_group(request.user, "Admin", "Teacher"):
            return True
        if in_group(request.user, "Student"):
            return obj.user == request.user
        return False


class StudentImageDeletePermission(BasePermission):
    def has_permission(self, request, view):
        return in_group(request.user, "Admin")


# ---------- Academic record ----------

class AcademicRecordPermission(BasePermission):

    def has_permission(self, request, view):
        if in_group(request.user, "Admin"):
            return True
        if in_group(request.user, "Teacher"):
            return request.method in ["GET", "POST", "PUT", "PATCH"]
        if in_group(request.user, "Student"):
            return request.method == "GET"
        return False

    def has_object_permission(self, request, view, obj):
        if in_group(request.user, "Admin"):
            return True
        if in_group(request.user, "Teacher"):
            return request.method in ["GET", "POST", "PUT", "PATCH"]
        if in_group(request.user, "Student"):
            return (
                request.method == "GET"
                and obj.student.user == request.user
            )
        return False


# ---------- Skill ----------

class SkillPermission(BasePermission):
    def has_permission(self, request, view):
        if in_group(request.user, "Admin"):
            return True
        if in_group(request.user, "Teacher", "Student"):
            return request.method in SAFE_METHODS
        return False


# ---------- Certification ----------

class CertificationPermission(BasePermission):

    def has_permission(self, request, view):
        if in_group(request.user, "Admin"):
            return True
        if in_group(request.user, "Teacher"):
            return request.method in ["GET", "POST", "PUT", "PATCH"]
        if in_group(request.user, "Student"):
            return request.method == "GET"
        return False

    def has_object_permission(self, request, view, obj):
        if in_group(request.user, "Admin"):
            return True
        if in_group(request.user, "Teacher"):
            return request.method in ["GET", "POST", "PUT", "PATCH"]
        if in_group(request.user, "Student"):
            return (
                request.method == "GET"
                and obj.student.user == request.user
            )
        return False


# ---------- Company ----------

class CompanyPermission(BasePermission):
    def has_permission(self, request, view):
        if in_group(request.user, "Admin"):
            return True
        if in_group(request.user, "Teacher", "Student"):
            return request.method in SAFE_METHODS
        return False


# ---------- Placement drive ----------

class PlacementDrivePermission(BasePermission):
    def has_permission(self, request, view):
        if in_group(request.user, "Admin"):
            return True
        if in_group(request.user, "Teacher"):
            return request.method in ["GET", "POST", "PUT", "PATCH"]
        if in_group(request.user, "Student"):
            return request.method in SAFE_METHODS
        return False


# ---------- Job ----------

class JobPermission(BasePermission):
    def has_permission(self, request, view):
        if in_group(request.user, "Admin"):
            return True
        if in_group(request.user, "Teacher"):
            return request.method in ["GET", "POST", "PUT", "PATCH"]
        if in_group(request.user, "Student"):
            return request.method in SAFE_METHODS
        return False


# ---------- Eligibility ----------

class EligibilityPermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.method == "GET"


# ---------- Application ----------

class ApplicationPermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if in_group(request.user, "Admin"):
            return True
        if in_group(request.user, "Teacher"):
            return request.method in ["GET", "POST", "PUT", "PATCH"]
        if in_group(request.user, "Student"):
            return request.method in ["GET", "POST"]
        return False


# ---------- Interview ----------

class InterviewPermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if in_group(request.user, "Admin", "Teacher"):
            return True
        if in_group(request.user, "Student"):
            return request.method == "GET"
        return False


# ---------- Selection ----------

class SelectionPermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if in_group(request.user, "Admin", "Teacher"):
            return True
        if in_group(request.user, "Student"):
            return request.method == "GET"
        return False


# ---------- Notification ----------

class NotificationPermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if in_group(request.user, "Admin", "Teacher"):
            return True
        # Students can read, and PATCH to mark their own as read
        if in_group(request.user, "Student"):
            return request.method in ["GET", "PATCH"]
        return False


# ---------- Dashboard / Audit logs ----------

class DashboardPermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return in_group(request.user, "Admin", "Teacher")