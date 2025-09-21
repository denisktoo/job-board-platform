from django.shortcuts import render
from .serializer import (
    UserSerializer, CompanySerializer, CategorySerializer, JobSerializer
    , ApplicationSerializer, RegisterSerializer, ProfileSerializer
    , CompanyReviewSerializer, NotificationSerializer
)
from rest_framework import viewsets, generics, status
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from .models import (
    User, Company, Category, Job, Application, Profile, CompanyReview, Notification
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from .permissions import (
    IsAdminUser, IsApplicantOrAdminUser, IsRecruiterOrAdminUser, IsApplicantOrAdmin
)
from rest_framework.exceptions import (
    MethodNotAllowed, ValidationError, NotFound, PermissionDenied
)
from .tasks import (
    send_company_registration_confirmation_email, send_job_application_confirmation_email
    , send_job_registration_confirmation_email
)
from rest_framework.parsers import MultiPartParser, FormParser
from .filter import (
    ApplicationFilter, JobFilter, ProfileFilter, NotificationFilter, CompanyReviewFilter
)
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import JsonResponse

class UserViewSets(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsApplicantOrAdmin]

    def get_queryset(self):
        # Skip logic during Swagger schema generation
        if getattr(self, "swagger_fake_view", False):
            return User.objects.none()

        role = getattr(self.request.user, 'role', None)
        if role == 'admin':
            return User.objects.all()
        # Applicants can only see themselves
        return User.objects.filter(user_id=self.request.user.user_id)

class UserApplicationsViewSet(viewsets.ModelViewSet):
    serializer_class = ApplicationSerializer
    permission_classes = [IsApplicantOrAdminUser]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = ApplicationFilter
    search_fields = ['user__username', 'job__title']

    def get_queryset(self):
        role = getattr(self.request.user, 'role', None)
        if role == 'admin':
            return Application.objects.all()
        if role == 'user':
            return Application.objects.filter(user=self.request.user)
        return Application.objects.none()

    def create(self, request, *args, **kwargs):
        raise MethodNotAllowed('POST')

    # def destroy(self, request, *args, **kwargs):
    #     raise MethodNotAllowed('DELETE')

class CompanyViewSets(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [IsRecruiterOrAdminUser]

    def perform_create(self, serializer):
        company = serializer.save(user=self.request.user)

        # Call Celery task after saving
        send_company_registration_confirmation_email.delay(
            company.email,
            company.name,
            company.location,
            company.industry
        )

        return company

class CategoryViewSets(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminUser]

class PublicJobViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = JobFilter
    search_fields = ['title', 'company__name', 'location']
    ordering_fields = ['salary', 'created_at', 'deadline'] 

class JobViewSets(viewsets.ModelViewSet):
    serializer_class = JobSerializer
    permission_classes = [IsRecruiterOrAdminUser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = JobFilter
    search_fields = ['title', 'company__name', 'location']
    ordering_fields = ['salary', 'created_at', 'deadline'] 

    def get_queryset(self):
        company_pk = self.kwargs.get('company_pk')
        if company_pk:
            # Nested route: /companies/{company_pk}/jobs/
            return Job.objects.filter(company_id=company_pk)

        # Flat route: /jobs/
        return Job.objects.all()
    
    def perform_create(self, serializer):
        company_pk = self.kwargs.get('company_pk')

        if not company_pk:
            raise ValidationError("Jobs must be created under a company.")

        job = serializer.save(company_id=company_pk)

        # Call Celery task after saving
        send_job_registration_confirmation_email.delay(
            job.company.user.email,
            job.company.user.first_name,
            job.title,
            job.employment_type,
            job.created_at,
            job.deadline
        )

        return job

class JobApplicationViewSets(viewsets.ModelViewSet):
    serializer_class = ApplicationSerializer
    permission_classes = [IsApplicantOrAdminUser]
    parser_classes = (MultiPartParser, FormParser)
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = ApplicationFilter
    search_fields = ['user__username', 'job__title']

    def get_queryset(self):
        job_pk = self.kwargs.get('job_pk')
        return Application.objects.filter(job_id=job_pk)
    
    def perform_create(self, serializer):
        job_pk = self.kwargs.get('job_pk')
        user = self.request.user

        # Check if user already applied for this job
        if Application.objects.filter(user=user, job_id=job_pk).exists():
            raise ValidationError("You have already submitted this application.")
    
        application =  serializer.save(user=self.request.user, job_id=job_pk)

        # Call Celery task after saving
        send_job_application_confirmation_email.delay(
            application.user.email,
            application.user.first_name,
            application.job.title,
            application.job.company.name,
            application.status,
            application.applied_at
        )

        return application

class CompanyJobApplicationsViewSet(viewsets.ModelViewSet):
    serializer_class = ApplicationSerializer
    permission_classes = [IsRecruiterOrAdminUser]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = ApplicationFilter
    search_fields = ['user__username', 'job__title']

    def get_queryset(self):
        # Skip logic during Swagger schema generation
        if getattr(self, "swagger_fake_view", False):
            return Company.objects.none()

        company_pk = self.kwargs.get('company_pk')
        job_pk = self.kwargs.get('job_pk')

        # Check if company exists
        try:
            company = Company.objects.get(company_id=company_pk)
        except Company.DoesNotExist:
            raise NotFound("Company does not exist.")

        # Check if job exists under this company
        try:
            job = Job.objects.get(job_id=job_pk, company=company)
        except Job.DoesNotExist:
            raise NotFound(f"This job does not exist under {company.name} company.")

        # Restrict recruiter to only their own company
        role = getattr(self.request.user, 'role', None)
        if role == 'recruiter' and job.company.user != self.request.user:
            raise PermissionDenied("You cannot access applications for another company.")

        # Return all applications for the job (admins or allowed recruiter)
        return Application.objects.filter(job=job)

    def create(self, request, *args, **kwargs):
        raise MethodNotAllowed('POST')

    def destroy(self, request, *args, **kwargs):
        raise MethodNotAllowed('DELETE')

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [IsApplicantOrAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ProfileFilter

    def get_queryset(self):
        # Skip logic during Swagger schema generation
        if getattr(self, "swagger_fake_view", False):
            return Company.objects.none()
        
        if getattr(self.request.user, 'role', None) == "admin":
            return Profile.objects.all()
        return Profile.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Ensure one profile per user
        if Profile.objects.filter(user=self.request.user).exists():
            raise ValidationError("You already have a profile.")
        serializer.save(user=self.request.user)

class CompanyReviewViewSet(viewsets.ModelViewSet):
    serializer_class = CompanyReviewSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = CompanyReviewFilter

    def get_queryset(self):
        company_pk = self.kwargs.get("company_pk")
        return CompanyReview.objects.filter(company_id=company_pk)

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        company_pk = self.kwargs.get("company_pk")

        # Validate company existence
        company = get_object_or_404(Company, company_id=company_pk)

        # Prevent company owner from reviewing own company
        if company.user == self.request.user:
            raise PermissionDenied("You cannot post review for your own company")

        # Save the review with current user & company
        serializer.save(user=self.request.user, company=company)

class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = NotificationFilter

    def get_queryset(self):
        # Skip logic during Swagger schema generation
        if getattr(self, "swagger_fake_view", False):
            return Notification.objects.none()

        company_pk = self.kwargs.get('company_pk')

        # Check if company exists
        try:
            company = Company.objects.get(company_id=company_pk)
        except Company.DoesNotExist:
            raise NotFound("Company does not exist.")

        role = getattr(self.request.user, 'role', None)

        # Admins can see all
        if role == 'admin':
            return Notification.objects.filter(company=company)

        # Recruiters only see their own company's notifications
        if role == 'recruiter':
            if company.user != self.request.user:
                raise PermissionDenied("You cannot access notifications for another company.")
            return Notification.objects.filter(company=company)

        # Users have no access
        raise PermissionDenied("You do not have permission to access this request.")

    def create(self, request, *args, **kwargs):
        raise MethodNotAllowed('POST')

    @action(detail=True, methods=["patch"], url_path="mark-as-read")
    def mark_as_read(self, request, company_pk=None, pk=None):
        """Custom route to mark a notification as read"""

        # Ensure company exists
        company = get_object_or_404(Company, company_id=company_pk)

        role = getattr(request.user, 'role', None)

        # Admins can mark any company's notifications
        if role == 'admin':
            notification = get_object_or_404(Notification, pk=pk, company=company)

        # Recruiters can only mark their own company's notifications
        elif role == 'recruiter':
            if company.user != request.user:
                raise PermissionDenied("You cannot mark notifications for another company.")
            notification = get_object_or_404(Notification, pk=pk, company=company)

        # user role cannot mark notifications
        else:
            raise PermissionDenied("You do not have permission to perform this action.")

        if not notification.is_read:
            notification.is_read = True
            notification.save(update_fields=["is_read"])

        serializer = self.get_serializer(notification)
        return Response(serializer.data, status=status.HTTP_200_OK)

def home(request):
    return JsonResponse(
        {
            "message": "Job Board API is live 🚀",
            "docs": "/api/docs/",
            "api_base": "/api/"
        },
        json_dumps_params={"ensure_ascii": False}
    )
