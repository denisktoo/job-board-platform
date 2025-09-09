from django.shortcuts import render
from .serializer import (
    UserSerializer, CompanySerializer, CategorySerializer, JobSerializer
    , ApplicationSerializer, RegisterSerializer
)
from rest_framework import viewsets, generics
from .models import User, Company, Category, Job, Application
from rest_framework.permissions import AllowAny
from .permissions import IsAdminUser, IsApplicantOrAdminUser, IsRecruiterOrAdminUser
from rest_framework.exceptions import MethodNotAllowed

class UserViewSets(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]

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

class JobViewSets(viewsets.ModelViewSet):
    serializer_class = JobSerializer
    permission_classes = [IsRecruiterOrAdminUser]

    def get_queryset(self):
        company_pk = self.kwargs.get('company_pk')
        return Job.objects.filter(company_id=company_pk)
    
    def perform_create(self, serializer):
        company_pk = self.kwargs.get('company_pk')
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

class UserApplicationsViewSet(viewsets.ModelViewSet):
    serializer_class = ApplicationSerializer
    permission_classes = [IsApplicantOrAdminUser]

    def get_queryset(self):
        user_pk = self.kwargs.get('user_pk')

        # Admins can view any user's application
        if getattr(self.request.user, 'role', None) == 'admin':
            return Application.objects.filter(user_id=user_pk)
        
        # Regular users can only manage their own application
        return Application.objects.filter(user_id=self.request.user)
    
    def perform_create(self, serializer):
        raise MethodNotAllowed('POST')

class CompanyJobApplicationsViewSet(viewsets.ModelViewSet):
    serializer_class = ApplicationSerializer
    permission_classes = [IsRecruiterOrAdminUser]

    def get_queryset(self):
        company_pk = self.kwargs.get('company_pk')
        job_pk = self.kwargs.get('job_pk')
        company_applications = Application.objects.filter(job_id=job_pk, job__company_id=company_pk)

        # Ensure the Recruiter only sees their company's jobs
        if getattr(self.request.user, 'role', None) == 'recruiter':
            company_applications = company_applications.filter(job__company__user=self.request.user)
        return company_applications

    def create(self, request, *args, **kwargs):
        raise MethodNotAllowed('POST')
    
    def destroy(self, request, *args, **kwargs):
        raise MethodNotAllowed('DELETE')

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
