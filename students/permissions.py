from rest_framework.permissions import BasePermission, IsAuthenticated, SAFE_METHODS

# custom permissions for get and post
class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or (
            request.user and request.user.is_staff
        )

# custom pertmissions for modify and delete
class IsStaffOrreadonly (BasePermission): 
    def has_object_permission(self, request, view, obj): 
        return request.method in SAFE_METHODS or (
            request.user and request.user.is_staff
        )
# custom permissions (user can get,modify,delete its own student)
class IsStudentOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        print("Logged in user:", request.user)
        print("Student owner:", obj.user)
        return obj.user == request.user


# '''' RBAC performing the resulble permissions '''
class RoleBasedPermission(BasePermission):
    allowed_roles=[]
    def has_permission(self, request, view):
        return request.user.groups.filter(
            name__in=self.allowed_roles).exists()

# continue(rolebasedpermissions) create specific role permissions
# Admin OR Teacher
class IsAdminOrTeacher(RoleBasedPermission):
    allowed_roles=["Admin","Teacher"]

#continue (rolebasedpermissions)
#Admin Only
class IsAdmin(RoleBasedPermission):
    allowed_roles=["Admin"]

#continue(rolebasedpermissions)
#Teacher only
class IsTeacher(RoleBasedPermission):
    allowed_roles=["Teacher"]

#continue(rolebasedpermissions)
#student only
class IsStudent(RoleBasedPermission):
    allowed_roles=["Student"]


# Role + HTTP Method
class StudentManagementPermissions(BasePermission):
    def has_permission(self, request, view):
        if request.user.groups.filter(name="Admin").exists():#Admin can work on every method
            return True
        if request.user.groups.filter(name="Teacher").exists(): # Teacher can work on all method except delete
            return request.method in [
                "GET",
                "POST",
                "PUT",
                "PATCH"
            ]
        if request.user.groups.filter(name="Student").exists():#Student can only get the data
            return request.method=="GET"
        return False

#### RBAC + Owner Permission ####
class StudentDetailPermission(BasePermission): 
 
    def has_permission(self, request, view): 
 
        # Admin can do everything 
        if request.user.groups.filter(name="Admin").exists(): 
            return True 
 
        # Teacher can GET, PUT and PATCH 
        if request.user.groups.filter(name="Teacher").exists(): 
            return request.method in [ 
                "GET", 
                "PUT", 
                "PATCH" 
            ] 
 
        # Student can only GET 
        if request.user.groups.filter(name="Student").exists(): 
            return request.method == "GET" 
 
        return False 
 
    def has_object_permission(self, request, view, obj): 
  
 
        # Admin → can access any student 
        if request.user.groups.filter(name="Admin").exists(): 
            return True 
 
        # Teacher → can access any student 
        if request.user.groups.filter(name="Teacher").exists(): 
            return True 
 
        # Student → only their own student record 
        if request.user.groups.filter(name="Student").exists(): 
            return obj.user == request.user 
 
        return False 
    
 # Create an image-delete permission 
class StudentImageDeletePermission(BasePermission): 
    def has_permission(self, request, view): 
        if request.user.groups.filter(name="Admin").exists(): 
            return True 
        return False 

# Apply the reusable RBAC permission
class StudentDetailAllPermission(RoleBasedPermission): 
 
    role_methods = { 
        "Admin": ["GET", "PUT", "PATCH", "DELETE"], 
        "Teacher": ["GET", "PUT", "PATCH"], 
        "Student": ["GET"] 
    } 
 
    def has_object_permission(self, request, view, obj): 
 
        user = request.user 
 
        # Admin → any student 
        if user.groups.filter(name="Admin").exists(): 
            return True 
 
        # Teacher → any student 
        if user.groups.filter(name="Teacher").exists(): 
            return True 
 
        # Student → only own student 
        if user.groups.filter(name="Student").exists(): 
            return obj.user == user 
 
        return False 

# RBAC+HTTP METHOD + OWNER PERMISSION For academic record permissions
class AcademicRecordPermission(BasePermission):

    def has_object_permission(self, request, view, obj):

        if request.user.groups.filter(name="Admin").exists():
            return True

        if request.user.groups.filter(name="Teacher").exists():
            return request.method in ["GET", "POST", "PUT", "PATCH"]

        if request.user.groups.filter(name="Student").exists():
            return (
                request.method == "GET"
                and obj.student.user == request.user
            )

        return False

class SkillPermission(BasePermission):

    def has_permission(self, request, view):

        if request.user.groups.filter(name="Admin").exists():
            return True

        if request.user.groups.filter(
            name__in=["Teacher", "Student"]
        ).exists():
            return request.method in SAFE_METHODS

        return False

class CertificationPermission(BasePermission):

    def has_permission(self, request, view):

        if request.user.groups.filter(name="Admin").exists():
            return True

        if request.user.groups.filter(name="Teacher").exists():
            return request.method in ["GET", "POST", "PUT", "PATCH"]

        if request.user.groups.filter(name="Student").exists():
            return request.method == "GET"

        return False

    def has_object_permission(self, request, view, obj):

        if request.user.groups.filter(name="Admin").exists():
            return True

        if request.user.groups.filter(name="Teacher").exists():
            return request.method in ["GET", "POST", "PUT", "PATCH"]

        if request.user.groups.filter(name="Student").exists():
            return (
                request.method == "GET"
                and obj.student.user == request.user
            )

        return False

class CompanyPermission(BasePermission):

    def has_permission(self, request, view):

        if request.user.groups.filter(name="Admin").exists():
            return True

        if request.user.groups.filter(
            name__in=["Teacher", "Student"]
        ).exists():
            return request.method in SAFE_METHODS

        return False



class EligibilityPermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.method == "GET":
            return True

        if request.method == "POST":
            return request.user.groups.filter(
                name__in=["Admin", "Teacher"]
            ).exists()

        return False



class ApplicationPermission(BasePermission):

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if request.user.groups.filter(name="Admin").exists():
            return True

        if request.user.groups.filter(name="Teacher").exists():
            return request.method in [
                "GET",
                "POST",
                "PUT",
                "PATCH"
            ]

        if request.user.groups.filter(name="Student").exists():
            return request.method in [
                "GET",
                "POST"
            ]

        return False


class InterviewPermission(BasePermission):

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Admin and Teacher can manage interviews
        if request.user.groups.filter(
            name__in=["Admin", "Teacher"]
        ).exists():
            return True

        # Student can view interviews
        if request.user.groups.filter(name="Student").exists():
            return request.method == "GET"

        return False


class SelectionPermission(BasePermission):

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Admin and Teacher can manage selections
        if request.user.groups.filter(
            name__in=["Admin", "Teacher"]
        ).exists():
            return True

        # Student can only view selections
        if request.user.groups.filter(name="Student").exists():
            return request.method == "GET"

        return False


class PlacementDrivePermission(BasePermission):

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if request.user.groups.filter(name="Admin").exists():
            return True

        if request.user.groups.filter(name="Teacher").exists():
            return request.method in ["GET", "POST", "PUT", "PATCH"]

        if request.user.groups.filter(name="Student").exists():
            return request.method in SAFE_METHODS

        return False


class JobPermission(BasePermission):

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if request.user.groups.filter(name="Admin").exists():
            return True

        if request.user.groups.filter(name="Teacher").exists():
            return request.method in ["GET", "POST", "PUT", "PATCH"]

        if request.user.groups.filter(name="Student").exists():
            return request.method in SAFE_METHODS

        return False
