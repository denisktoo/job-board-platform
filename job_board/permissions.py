from rest_framework import permissions

from .models import Application, Company, CompanyReview, Job


class IsAdminUser(permissions.BasePermission):
    """
    - Authenticated users can perform SAFE methods
    - Only admins can perform unsafe methods
    """

    def has_permission(self, request, view):
        # Allow SAFE methods for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True

        # Unsafe methods only allowed for admins
        return getattr(request.user, "role", None) == "admin"


class IsRecruiterOrAdminUser(permissions.BasePermission):
    """
    - Admins: full access
    - Recruiters: manage only their own company/jobs/applications
    - Others/Anonymous: can view companies & jobs, cannot view applications
    """

    def has_permission(self, request, view):
        role = getattr(request.user, "role", None)

        # Only recruiters/admins can access company-job-applications endpoint
        if view.basename == "company-job-applications" and role not in [
            "recruiter",
            "admin",
        ]:
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

        # Recruiter: modify only own company/jobs bt only view CompanyRevew
        if role == "recruiter":
            if isinstance(obj, Company) and obj.user == request.user:
                return True
            if isinstance(obj, Job) and obj.company.user == request.user:
                return True
            if isinstance(obj, CompanyReview) and obj.company.user == request.user:
                # Only allow safe operations (read-only)
                return request.method in permissions.SAFE_METHODS

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
        return getattr(request.user, "role", None) in ["user", "admin"]

    def has_object_permission(self, request, view, obj):
        role = getattr(request.user, "role", None)

        # Admin has complete access
        if role == "admin":
            return True

        # Applicant can access only their own applicaition and profile
        if role == "user":
            if hasattr(obj, "user"):  # Profile object
                return obj.user == request.user
            return obj == request.user  # Application object

        return False


class IsApplicantOrAdminUser(permissions.BasePermission):
    """
    - Admins: full access
    - Applicants: can access only their own job applications
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return getattr(request.user, "role", None) in ["user", "admin"]

    def has_object_permission(self, request, view, obj):
        role = getattr(request.user, "role", None)

        # Admin has complete access
        if role == "admin":
            return True

        # Job application ownership
        if role == "user":
            if hasattr(obj, "user"):
                return obj.user == request.user

        return False


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    - Admin: full access
    - Any authenticated user: can view/update ONLY their own profile
    """

    def has_permission(self, request, view):
        # Must be authenticated
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Admin can access everything
        if getattr(request.user, "role", None) == "admin":
            return True

        # Only allow users to access their own profile
        return obj.user == request.user


class IsParticipantOrAdmin(permissions.BasePermission):
    """
    - Admin: full access
    - Participants: can view/update conversations they are part of
    """

    def has_permission(self, request, view):
        # Must be authenticated
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Admin can access everything
        if getattr(request.user, "role", None) == "admin":
            return True

        participants = getattr(obj, "participants", None)
        if participants is not None:
            return request.user in participants.all()

        conversation = getattr(obj, "conversation", None)
        if conversation is not None:
            return request.user in conversation.participants.all()

        return False
