from .models import (
    User, Company, Category, Job, Application, Profile, CompanyReview, Notification
)
from rest_framework import serializers

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['user_id', 'username', 'first_name', 'last_name', 'email', 'password', 'phone_number', 'role', 'created_at']

class CompanySerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = Company
        fields = ['company_id', 'user', 'name', 'email', 'phone_number', 'description', 'location', 'website', 'industry']

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['category_id', 'name', 'description']

class JobSerializer(serializers.ModelSerializer):
    company = CompanySerializer(read_only=True)
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())

    class Meta:
        model = Job
        fields = ['job_id', 'title', 'description', 'company', 'category', 'location', 'salary', 'created_at', 'deadline', 'employment_type']

class ApplicationSerializer(serializers.ModelSerializer):
    job = JobSerializer(read_only=True)
    user = UserSerializer(read_only=True)

    class Meta:
        model = Application
        fields = ['application_id', 'user', 'job', 'cover_letter', 'resume', 'status', 'applied_at']

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['user_id', 'username', 'first_name', 'last_name', 'email', 'phone_number', 'password', 'role']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Profile
        fields = ['profile_id', 'user', 'bio', 'linkedin_url', 'portfolio_url', 'created_at', 'location', 'skills', 'experience', 'github_url']

class CompanyReviewSerializer(serializers.ModelSerializer):
    company = CompanySerializer(read_only=True)
    user = UserSerializer(read_only=True)

    class Meta:
        model = CompanyReview
        fields = ['review_id', 'company', 'user', 'rating', 'comment', 'created_at']

class NotificationSerializer(serializers.ModelSerializer):
    company = CompanySerializer(read_only=True)
    user = UserSerializer(read_only=True)

    class Meta:
        model = Notification
        fields = ['notification_id', 'company', 'user', 'type', 'content', 'is_read', 'created_at']
