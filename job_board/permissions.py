from rest_framework import permissions

class IsAdminUser(permissions.BasePermission):
    """
    Allow only users with role 'admin' to have access everywhere
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return request.method in permissions.SAFE_METHODS

        role = getattr(request.user, 'role', None)

        # Admins can do anything
        if role == 'admin':
            return True

        # Others can only do safe methods (GET, HEAD, OPTIONS)
        return request.method in permissions.SAFE_METHODS

class IsRecruiterOrAdminUser(permissions.BasePermission):
    """
    Allow only users with role 'recruiter' or 'admin' for Jobs Management
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return request.method in permissions.SAFE_METHODS

        role = getattr(request.user, 'role', None)

        if role in ['recruiter', 'admin']:
            return True
        
        # Others can only do safe methods (GET, HEAD, OPTIONS)
        return request.method in permissions.SAFE_METHODS
    
class IsApplicantOrAdminUser(permissions.BasePermission):
    """
    Allow only users with role 'admin' or 'user' for Job Application
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return request.method in permissions.SAFE_METHODS

        role = getattr(request.user, 'role', None)

        if role in ['user', 'admin']:
            return True

        # Others can only do safe methods (GET, HEAD, OPTIONS)
        return request.method in permissions.SAFE_METHODS
