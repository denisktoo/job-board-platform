import django_filters
from .models import (
    Application, Job, Profile, CompanyReview, Notification,
    Company, Category, User, Conversation, Message
)
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
        fields = ['company', 'user', 'rating']

class NotificationFilter(django_filters.FilterSet):
    receiver = django_filters.UUIDFilter(field_name='receiver__user_id', lookup_expr='exact')
    type = django_filters.CharFilter(field_name='type', lookup_expr='iexact')
    is_read = django_filters.BooleanFilter(field_name='is_read')
  
    class Meta:
        model = Notification
        fields = ['receiver', 'type', 'is_read']

class CompanyFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name='name', lookup_expr='icontains')
    location = django_filters.CharFilter(field_name='location', lookup_expr='icontains')
    industry = django_filters.CharFilter(field_name='industry', lookup_expr='icontains')

    class Meta:
        model = Company
        fields = ['name', 'location', 'industry']

class CategoryFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name='name', lookup_expr='icontains')

    class Meta:
        model = Category
        fields = ['name']

class UserFilter(django_filters.FilterSet):
    username = django_filters.CharFilter(field_name='username', lookup_expr='icontains')
    email = django_filters.CharFilter(field_name='email', lookup_expr='icontains')
    role = django_filters.CharFilter(field_name='role', lookup_expr='iexact')

    class Meta:
        model = User
        fields = ['username', 'email', 'role']

class ConversationFilter(django_filters.FilterSet):
    participant = django_filters.UUIDFilter(method='filter_by_participant')

    def filter_by_participant(self, queryset, name, value):
        return queryset.filter(participants__user_id=value)

    class Meta:
        model = Conversation
        fields = ['participant']

class MessageFilter(django_filters.FilterSet):
    sender = django_filters.UUIDFilter(field_name='sender__user_id', lookup_expr='exact')
    receiver = django_filters.UUIDFilter(field_name='receiver__user_id', lookup_expr='exact')
    conversation = django_filters.NumberFilter(field_name='conversation_id', lookup_expr='exact')
    read = django_filters.BooleanFilter(field_name='read')

    class Meta:
        model = Message
        fields = ['sender', 'receiver', 'conversation', 'read']
