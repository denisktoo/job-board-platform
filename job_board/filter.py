import django_filters
from .models import Application, Job, Profile, CompanyReview, Notification
from django.utils import timezone

class JobFilter(django_filters.FilterSet):
    employment_type = django_filters.CharFilter(field_name='employment_type', lookup_expr='iexact')
    deadline = django_filters.BooleanFilter(method='filter_active_jobs')

    def filter_active_jobs(self, queryset, name, value):
        if value:
            return queryset.filter(deadline__gte=timezone.now())
        return queryset

    class Meta:
        model = Job
        fields = ['employment_type', 'deadline', 'category', 'company']

class ApplicationFilter(django_filters.FilterSet):
    # check if resume and cover_letter exists
    resume = django_filters.BooleanFilter(method='filter_has_resume')
    cover_letter = django_filters.BooleanFilter(method='filter_has_cover_letter')

    def filter_has_resume(self, queryset, name, value):
        if value:
            return queryset.exclude(resume__isnull=True).exclude(resume='')
        return queryset

    def filter_has_cover_letter(self, queryset, name, value):
        if value:
            return queryset.exclude(cover_letter__isnull=True).exclude(cover_letter='')
        return queryset

    class Meta:
        model = Application
        fields = ['status', 'job', 'user']

class ProfileFilter(django_filters.FilterSet):
    location = django_filters.CharFilter(field_name='location', lookup_expr='icontains')
    skills = django_filters.CharFilter(field_name='skills', lookup_expr='icontains')
    experience = django_filters.CharFilter(field_name='experience', lookup_expr='icontains')

    class Meta:
        model = Profile
        fields = ['location', 'skills', 'experience']

class CompanyReviewFilter(django_filters.FilterSet):
    company = django_filters.NumberFilter(field_name='company_id', lookup_expr='exact')
    user = django_filters.NumberFilter(field_name='user_id', lookup_expr='exact')
    rating_min = django_filters.NumberFilter(field_name='rating', lookup_expr='gte')
    rating_max = django_filters.NumberFilter(field_name='rating', lookup_expr='lte')

    class Meta:
        model = CompanyReview
        fields = {'company', 'user', 'rating'}

class NotificationFilter(django_filters.FilterSet):
    user = django_filters.NumberFilter(field_name='user_id', lookup_expr='exact')
    company = django_filters.NumberFilter(field_name='company_id', lookup_expr='exact')
    is_read = django_filters.BooleanFilter(field_name='is_read')
  
    class Meta:
        model = Notification
        fields = ['user', 'company', 'is_read']