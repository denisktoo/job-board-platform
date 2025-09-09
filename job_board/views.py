from django.shortcuts import render
from .serializer import (
    UserSerializer, CompanySerializer, CategorySerializer, JobSerializer
    , ApplicationSerializer, RegisterSerializer
)
from rest_framework import viewsets, generics
from .models import User, Company, Category, Job, Application
from rest_framework.permissions import AllowAny

class UserViewSets(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class CompanyViewSets(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer

class CategoryViewSets(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class JobViewSets(viewsets.ModelViewSet):
    queryset = Job.objects.all()
    serializer_class = JobSerializer

class ApplicationViewSets(viewsets.ModelViewSet):
    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
