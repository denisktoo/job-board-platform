from django.db import models
import uuid
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class User(AbstractUser):
    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    username = models.CharField(max_length=150, null=False, unique=True, db_index=True)
    first_name = models.CharField(max_length=150, null=False)
    last_name = models.CharField(max_length=150, null=False)
    email = models.EmailField(unique=True, null=False, db_index=True)
    password = models.CharField(max_length=128)
    phone_number = models.CharField(max_length=20, null=True)

    ROLE_CHOICES = [
        ('user', 'User'),
        ('recruiter', 'Recruiter'),
        ('admin', 'Admin'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, null=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return self.email
    
class Company(models.Model):
    company_id = models.AutoField(primary_key=True)
    user = models.ForeignKey('User', on_delete=models.CASCADE, db_index=True, related_name="companies")
    name = models.CharField(max_length=255, null=False, db_index=True)
    email = models.EmailField(unique=True, null=False, db_index=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    website = models.URLField(blank=True, null=True)
    industry = models.CharField(max_length=100, null=True, blank=True, db_index=True)

    def __str__(self):
        return self.name
    
class Category(models.Model):
    category_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True, null=False, db_index=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Job(models.Model):
    job_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255, null=False, db_index=True)
    description = models.TextField(blank=True, null=True)
    company = models.ForeignKey('Company', on_delete=models.CASCADE, db_index=True, related_name="jobs")
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True, db_index=True, related_name="jobs")
    location = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    deadline = models.DateTimeField(db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    EMPLOYMENT_CHOICES = [
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('internship', 'Internship'),
        ('contract', 'Contract'),
    ]
    employment_type = models.CharField(max_length=30, choices=EMPLOYMENT_CHOICES, null=False, db_index=True)

    def save(self, *args, **kwargs):
        # Set location to company's location if not specified
        if not self.location and self.company_id:
            self.location = self.company.location

        # Auto-deactivate if deadline is passed
        if self.deadline.date() < timezone.now().date():
            self.is_active = False

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} @ {self.company.name} located at {self.location}."

class Application(models.Model):
    application_id = models.AutoField(primary_key=True)
    user = models.ForeignKey('User', on_delete=models.CASCADE, db_index=True, related_name="applications")
    job = models.ForeignKey('Job', on_delete=models.CASCADE, db_index=True, related_name="applications")
    applied_at = models.DateTimeField(auto_now_add=True, db_index=True)
    cover_letter = models.FileField(upload_to='cover_letter/', null=True, blank=True)
    resume = models.FileField(upload_to='resume/', null=True, blank=True)

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    is_completed = models.BooleanField(default=False, db_index=True)

    class Meta:
        unique_together = ('user', 'job')

    def save(self, *args, **kwargs):
        self.is_completed = bool(self.resume and self.cover_letter)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.job.title} ({self.status})"
    
class Profile(models.Model):
    profile_id = models.AutoField(primary_key=True)
    user = models.OneToOneField('User', on_delete=models.CASCADE, related_name="profile")
    bio = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    skills = models.TextField(blank=True, null=True)
    experience = models.TextField(blank=True, null=True)
    linkedin_url = models.URLField(blank=True, null=True)
    github_url = models.URLField(blank=True, null=True)
    portfolio_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Profile of {self.user.username}"


class CompanyReview(models.Model):
    review_id = models.AutoField(primary_key=True)
    company = models.ForeignKey('Company', on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name="company_reviews")
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('company', 'user')

    def __str__(self):
        return f"{self.company.name} review by {self.user.username} ({self.rating}/5)"