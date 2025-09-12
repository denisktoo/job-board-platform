from rest_framework import permissions
from .models import Company, Job, Application
from rest_framework.exceptions import PermissionDenied

class IsAdminUser(permissions.BasePermission):
    """
    - Authenticated users can perform SAFE methods
    - Only admins can perform unsafe methods
    """

    def has_permission(self, request, view):
        # Allow SAFE methods for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated

        # Unsafe methods only allowed for admins
        return getattr(request.user, 'role', None) == 'admin'

class IsRecruiterOrAdminUser(permissions.BasePermission):
    """
    - Admins: full access
    - Recruiters: manage only their own company/jobs/applications
    - Others/Anonymous: can view companies & jobs, cannot view applications
    """

    def has_permission(self, request, view):
        role = getattr(request.user, "role", None)

        # Only recruiters/admins can access company-job-applications endpoint
        if view.basename == "company-job-applications" and role not in ["recruiter", "admin"]:
            return False

        # SAFE methods allowed for everyone
        if request.method in permissions.SAFE_METHODS:
            return True

        # Only authenticated users for unsafe methods
        if not request.user.is_authenticated:
            return False

        # Admin can do anything
        if role == "admin":
            return True

        # Recruiters: allow, ownership checks moved to view
        if role == "recruiter":
            return True

        return False

    def has_object_permission(self, request, view, obj):
        role = getattr(request.user, "role", None)

        # Applications: only admin or recruiter of owning company
        if isinstance(obj, Application):
            if role == "admin":
                return True
            if role == "recruiter" and obj.job.company.user == request.user:
                return True
            return False

        # Companies & Jobs: public read allowed
        if request.method in permissions.SAFE_METHODS:
            return True

        # Admin full access
        if role == "admin":
            return True

        # Recruiter: modify only own company/jobs
        if role == "recruiter":
            if isinstance(obj, Company) and obj.user == request.user:
                return True
            if isinstance(obj, Job) and obj.company.user == request.user:
                return True

        return False

class IsApplicantOrAdmin(permissions.BasePermission):
    """
    - Admins: full access
    - Applicants: can view/update only their own profile
    """

    def has_permission(self, request, view):
        # Only authenticated users with role 'user' or 'admin'
        if not request.user.is_authenticated:
            return False
        return getattr(request.user, 'role', None) in ['user', 'admin']

    def has_object_permission(self, request, view, obj):
        # Admin can access any object
        if getattr(request.user, 'role', None) == 'admin':
            return True
        # Applicant can access only their own applicaition
        return obj == request.user


class IsApplicantOrAdminUser(permissions.BasePermission):
    """
    - Admins: full access
    - Applicants: can access only their own job applications
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return getattr(request.user, 'role', None) in ['user', 'admin']

    def has_object_permission(self, request, view, obj):
        role = getattr(request.user, 'role', None)
        if role == 'admin':
            return True
        if role == 'user' and obj.user == request.user:
            return True
        return False
