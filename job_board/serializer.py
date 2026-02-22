from .models import (
    User, Company, Category, Job, Application, Profile, CompanyReview, Conversation, Message, Notification, MessageHistory
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
        fields = ['job_id', 'title', 'description', 'company', 'category', 'location', 'salary', 'created_at', 'deadline', 'is_active', 'employment_type']

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

class ConversationSerializer(serializers.ModelSerializer):
    participants = UserSerializer(many=True, read_only=True)
    participant_ids = serializers.PrimaryKeyRelatedField(
        source='participants',
        queryset=User.objects.all(),
        many=True,
        write_only=True,
        required=False
    )

    class Meta:
        model = Conversation
        fields = ['conversation_id', 'participants', 'participant_ids', 'created_at']

class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    conversation = ConversationSerializer(read_only=True)
    conversation_id = serializers.PrimaryKeyRelatedField(source='conversation', queryset=Conversation.objects.all(), write_only=True, required=False)
    parent_message_id = serializers.PrimaryKeyRelatedField(source='parent_message', queryset=Message.objects.all(), write_only=True, required=False, allow_null=True)
    parent_message = serializers.PrimaryKeyRelatedField(read_only=True)
    receiver = UserSerializer(read_only=True)
    edit_history = serializers.SerializerMethodField()

    def get_edit_history(self, obj):
        history_qs = obj.edit_history.all()
        return MessageHistorySerializer(history_qs, many=True).data

    class Meta:
        model = Message
        fields = [
            'message_id', 'conversation', 'conversation_id',
            'parent_message', 'parent_message_id',
            'sender', 'receiver',
            'content', 'read', 'edited', 'created_at', 'edit_history'
        ]

class MessageHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageHistory
        fields = ['message_history_id', 'old_content', 'edited_at']

class ThreadedMessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    receiver = UserSerializer(read_only=True)
    replies = serializers.SerializerMethodField()

    def get_replies(self, obj):
        children = getattr(obj, '_threaded_replies', None)
        if children is None:
            children = obj.replies.select_related('sender', 'receiver').order_by('created_at')
        return ThreadedMessageSerializer(children, many=True, context=self.context).data

    class Meta:
        model = Message
        fields = ['message_id', 'parent_message', 'sender', 'receiver', 'content', 'read', 'edited', 'created_at', 'replies']

class UnreadInboxMessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source='sender.username', read_only=True)

    class Meta:
        model = Message
        fields = ['message_id', 'conversation_id', 'sender_id', 'sender_username', 'content', 'created_at', 'read']

class NotificationSerializer(serializers.ModelSerializer):
    receiver = UserSerializer(read_only=True)
    message = MessageSerializer(read_only=True)

    class Meta:
        model = Notification
        fields = ['notification_id', 'receiver', 'message', 'type', 'is_read', 'created_at']
