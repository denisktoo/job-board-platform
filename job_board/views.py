from django.shortcuts import render
from .serializer import (
    UserSerializer, CompanySerializer, CategorySerializer, JobSerializer
    , ApplicationSerializer, RegisterSerializer
)
from rest_framework import viewsets, generics
from .models import User, Company, Category, Job, Application
from rest_framework.permissions import AllowAny
from .permissions import IsAdminUser, IsApplicantOrAdminUser, IsRecruiterOrAdminUser, IsApplicantOrAdmin
from rest_framework.exceptions import MethodNotAllowed, ValidationError, NotFound, PermissionDenied

class UserViewSets(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsApplicantOrAdmin]

    def get_queryset(self):
        role = getattr(self.request.user, 'role', None)
        if role == 'admin':
            return User.objects.all()
        # Applicants can only see themselves
        return User.objects.filter(user_id=self.request.user.user_id)

class UserApplicationsViewSet(viewsets.ModelViewSet):
    serializer_class = ApplicationSerializer
    permission_classes = [IsApplicantOrAdminUser]

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
        return serializer.save(user=self.request.user)

class CategoryViewSets(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminUser]

class PublicJobViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = JobSerializer
    queryset = Job.objects.all()

class JobViewSets(viewsets.ModelViewSet):
    serializer_class = JobSerializer
    permission_classes = [IsRecruiterOrAdminUser]

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
        return serializer.save(company_id=company_pk)

class JobApplicationViewSets(viewsets.ModelViewSet):
    serializer_class = ApplicationSerializer
    permission_classes = [IsApplicantOrAdminUser]

    def get_queryset(self):
        job_pk = self.kwargs.get('job_pk')
        return Application.objects.filter(job_id=job_pk)
    
    def perform_create(self, serializer):
        job_pk = self.kwargs.get('job_pk')
        return serializer.save(user=self.request.user, job_id=job_pk)

class CompanyJobApplicationsViewSet(viewsets.ModelViewSet):
    serializer_class = ApplicationSerializer
    permission_classes = [IsRecruiterOrAdminUser]

    def get_queryset(self):
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
            raise NotFound("Job does not exist under this company.")

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
