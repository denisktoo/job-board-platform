from django.shortcuts import render
from .serializer import (
    UserSerializer, CompanySerializer, CategorySerializer, JobSerializer
    , ApplicationSerializer, RegisterSerializer, ProfileSerializer, CompanyReviewSerializer
)
from rest_framework import viewsets, generics
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from .models import User, Company, Category, Job, Application, Profile, CompanyReview
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
from .filter import ApplicationFilter, JobFilter

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

    def get_queryset(self):
        user = self.request.user
        if user.role == "admin":
            return Profile.objects.all()
        return Profile.objects.filter(user=user)

    def perform_create(self, serializer):
        # Ensure one profile per user
        if Profile.objects.filter(user=self.request.user).exists():
            raise ValidationError("You already have a profile.")
        serializer.save(user=self.request.user)

class CompanyReviewViewSet(viewsets.ModelViewSet):
    serializer_class = CompanyReviewSerializer

    def get_queryset(self):
        company_pk = self.kwargs.get("company_pk")
        return CompanyReview.objects.filter(company_id=company_pk)

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [IsApplicantOrAdminUser()]

    def perform_create(self, serializer):
        company_pk = self.kwargs.get("company_pk")
        serializer.save(user=self.request.user, company_id=company_pk)
