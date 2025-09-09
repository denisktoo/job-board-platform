from django.urls import path, include
from rest_framework import routers
from rest_framework_nested.routers import NestedDefaultRouter
from .views import (
    UserViewSets, CompanyViewSets, CategoryViewSets, JobViewSets, JobApplicationViewSets
    , RegisterView, UserApplicationsViewSet, CompanyJobApplicationsViewSet
)

router = routers.DefaultRouter()
router.register(r'users', UserViewSets, basename='user')
router.register(r'companies', CompanyViewSets, basename='company')
router.register(r'jobs', JobViewSets, basename='job')
router.register(r'categories', CategoryViewSets, basename='category')

company_router = NestedDefaultRouter(router, r'companies', lookup='company')
company_router.register(r'jobs', JobViewSets, basename='company-jobs')

company_job_apps = NestedDefaultRouter(company_router, r'jobs', lookup='job')
company_job_apps.register(r'applications', CompanyJobApplicationsViewSet, basename='company-jobs')

job_router = NestedDefaultRouter(router, r'jobs', lookup='job')
job_router.register(r'applications', JobApplicationViewSets, basename='job-applications')

user_router = NestedDefaultRouter(router, r'users', lookup='user')
user_router.register(r'applications', UserApplicationsViewSet, basename='user-applications')

urlpatterns =[
    path('', include(router.urls)),
    path('', include(company_router.urls)),
    path('', include(company_job_apps.urls)),
    path('', include(job_router.urls)),
    path('', include(user_router.urls)),
    path('register/', RegisterView.as_view(), name='register'),
]
