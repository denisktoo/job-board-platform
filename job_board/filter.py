import django_filters
from .models import Application, Job
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
