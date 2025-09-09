from django.urls import path, include
from rest_framework import routers
from rest_framework_nested.routers import NestedDefaultRouter
from .views import (
    UserViewSets, CompanyViewSets, CategoryViewSets, JobViewSets, ApplicationViewSets
    , RegisterView
)

router = routers.DefaultRouter()
router.register(r'users', UserViewSets, basename='user')
router.register(r'companies', CompanyViewSets, basename='company')
router.register(r'categories', CategoryViewSets, basename='category')

jobs_router = NestedDefaultRouter(router, r'companies', lookup='company')
jobs_router.register(r'jobs', JobViewSets, basename='company-jobs')

applications_router = NestedDefaultRouter(jobs_router, r'jobs', lookup='job')
applications_router.register(r'applications', ApplicationViewSets, basename='job-applications')

urlpatterns =[
    path('', include(router.urls)),
    path('', include(jobs_router.urls)),
    path('', include(applications_router.urls)),
    path('register/', RegisterView.as_view(), name='register'),
]
