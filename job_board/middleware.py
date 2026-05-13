import os
from datetime import datetime

from rest_framework_simplejwt.authentication import JWTAuthentication


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

        base_dir = os.path.dirname(os.path.dirname(__file__))
        self.log_path = os.path.join(base_dir, "requests.log")

    def __call__(self, request):
        user = request.user

        # If still anonymous, try to resolve JWT auth manually
        if user.is_anonymous:
            jwt_auth = JWTAuthentication()
            try:
                user_auth_tuple = jwt_auth.authenticate(request)
                if user_auth_tuple:
                    user, _ = user_auth_tuple
            except Exception:
                pass

        with open(self.log_path, "a") as log_file:
            log_file.write(f"{datetime.now()} - User: {user} - Path: {request.path}\n")

        response = self.get_response(request)
        return response
