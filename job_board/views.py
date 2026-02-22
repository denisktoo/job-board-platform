from django.shortcuts import render
from .serializer import (
    UserSerializer, CompanySerializer, CategorySerializer, JobSerializer
    , ApplicationSerializer, RegisterSerializer, ProfileSerializer
    , CompanyReviewSerializer, NotificationSerializer, MessageSerializer
    , ConversationSerializer, MessageHistorySerializer, ThreadedMessageSerializer
    , UnreadInboxMessageSerializer
)
from rest_framework import viewsets, generics, status
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from .models import (
    User, Company, Category, Job, Application, Profile, CompanyReview, Notification, Message, Conversation,
    MessageHistory
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from .permissions import (
    IsAdminUser, IsApplicantOrAdminUser, IsRecruiterOrAdminUser, IsApplicantOrAdmin,
    IsOwnerOrAdmin, IsParticipantOrAdmin
)
from rest_framework.exceptions import (
    MethodNotAllowed, ValidationError, NotFound, PermissionDenied
)
from .tasks import (
    send_company_registration_confirmation_email, send_job_application_confirmation_email
    , send_job_registration_confirmation_email
)
from rest_framework.parsers import MultiPartParser, FormParser
from .filter import (
    ApplicationFilter, JobFilter, ProfileFilter, NotificationFilter, CompanyReviewFilter,
    CompanyFilter, CategoryFilter, UserFilter, ConversationFilter, MessageFilter
)
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.db import transaction
from django.db.models import Prefetch

class UserViewSets(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsApplicantOrAdmin]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = UserFilter
    search_fields = ['username', 'email', 'first_name', 'last_name']

    def get_queryset(self):
        # Skip logic during Swagger schema generation
        if getattr(self, "swagger_fake_view", False):
            return User.objects.none()

        role = getattr(self.request.user, 'role', None)
        if role == 'admin':
            return User.objects.all()
        # Applicants can only see themselves
        return User.objects.filter(user_id=self.request.user.user_id)

class UserApplicationsViewSet(viewsets.ModelViewSet):
    serializer_class = ApplicationSerializer
    permission_classes = [IsApplicantOrAdminUser]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = ApplicationFilter
    search_fields = ['user__username', 'job__title']

    def get_queryset(self):
        role = getattr(self.request.user, 'role', None)
        if role == 'admin':
            return Application.objects.all()
        if role == 'user':
            return Application.objects.filter(user=self.request.user)
        return Application.objects.none()

    def create(self, request, *args, **kwargs):
        raise MethodNotAllowed('POST')

    # def destroy(self, request, *args, **kwargs):
    #     raise MethodNotAllowed('DELETE')

class CompanyViewSets(viewsets.ModelViewSet):
    # queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [IsRecruiterOrAdminUser]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = CompanyFilter
    search_fields = ['name', 'industry', 'location']

    def get_queryset(self):
        user = self.request.user

        # Public users → can see all companies
        if not user.is_authenticated:
            return Company.objects.all()

        # Admin → can see all companies
        if user.role == "admin":
            return Company.objects.all()

        # Recruiter → can ONLY see their own companies
        if user.role == "recruiter":
            return Company.objects.filter(user=user)

        # Others → default public view
        return Company.objects.all()

    def perform_create(self, serializer):
        company = serializer.save(user=self.request.user)

        # Call Celery task after saving
        # Only call Celery after DB commit
        # transaction.on_commit(lambda: send_company_registration_confirmation_email.delay(
        #     company.email,
        #     company.name,
        #     company.location,
        #     company.industry
        # ))

        return company

class CategoryViewSets(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = CategoryFilter
    search_fields = ['name']

# @method_decorator(cache_page(60 * 15), name="list")
# @method_decorator(cache_page(60 * 15), name="retrieve")
class PublicJobViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = JobFilter
    search_fields = ['title', 'company__name', 'location']
    ordering_fields = ['salary', 'created_at', 'deadline'] 

class JobViewSets(viewsets.ModelViewSet):
    serializer_class = JobSerializer
    permission_classes = [IsRecruiterOrAdminUser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = JobFilter
    search_fields = ['title', 'company__name', 'location']
    ordering_fields = ['salary', 'created_at', 'deadline'] 

    def get_queryset(self):
        company_pk = self.kwargs.get('company_pk')
        if company_pk:
            # Nested route: /companies/{company_pk}/jobs/
            return Job.objects.filter(company_id=company_pk)

        # Flat route: /jobs/
        return Job.objects.all()
    
    def perform_create(self, serializer):
        company_pk = self.kwargs.get('company_pk')

        if not company_pk:
            raise ValidationError("Jobs must be created under a company.")

        company = get_object_or_404(Company, company_id=company_pk)

        if company.user != self.request.user:
            raise PermissionDenied("You are not authorized to post jobs for this company.")

        job = serializer.save(company=company)

        # transaction.on_commit(lambda: send_job_registration_confirmation_email.delay(
        #     company.user.email,
        #     company.user.first_name,
        #     job.title,
        #     job.employment_type,
        #     job.created_at,
        #     job.deadline
        # ))

        return job

class JobApplicationViewSets(viewsets.ModelViewSet):
    serializer_class = ApplicationSerializer
    permission_classes = [IsApplicantOrAdminUser]
    parser_classes = (MultiPartParser, FormParser)
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = ApplicationFilter
    search_fields = ['user__username', 'job__title']

    def get_queryset(self):
        job_pk = self.kwargs.get('job_pk')
        return Application.objects.filter(job_id=job_pk)
    
    def perform_create(self, serializer):
        job_pk = self.kwargs.get('job_pk')
        user = self.request.user

        # Check if user already applied for this job
        if Application.objects.filter(user=user, job_id=job_pk).exists():
            raise ValidationError("You have already submitted this application.")
    
        application =  serializer.save(user=self.request.user, job_id=job_pk)

        # Call Celery task after saving
        # transaction.on_commit(lambda: send_job_application_confirmation_email.delay(
        #     application.user.email,
        #     application.user.first_name,
        #     application.job.title,
        #     application.job.company.name,
        #     application.status,
        #     application.applied_at
        # ))

        return application

class CompanyJobApplicationsViewSet(viewsets.ModelViewSet):
    serializer_class = ApplicationSerializer
    permission_classes = [IsRecruiterOrAdminUser]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = ApplicationFilter
    search_fields = ['user__username', 'job__title']

    def get_queryset(self):
        # Skip logic during Swagger schema generation
        if getattr(self, "swagger_fake_view", False):
            return Company.objects.none()

        company_pk = self.kwargs.get('company_pk')
        job_pk = self.kwargs.get('job_pk')

        # Check if company exists
        try:
            company = Company.objects.get(company_id=company_pk)
        except Company.DoesNotExist:
            raise NotFound("Company does not exist.")

        # Check if job exists under this company
        try:
            job = Job.objects.get(job_id=job_pk, company=company)
        except Job.DoesNotExist:
            raise NotFound(f"This job does not exist under {company.name} company.")

        # Restrict recruiter to only their own company
        role = getattr(self.request.user, 'role', None)
        if role == 'recruiter' and job.company.user != self.request.user:
            raise PermissionDenied("You cannot access applications for another company.")

        # Return all applications for the job (admins or allowed recruiter)
        return Application.objects.filter(job=job)

    def create(self, request, *args, **kwargs):
        raise MethodNotAllowed('POST')

    def destroy(self, request, *args, **kwargs):
        raise MethodNotAllowed('DELETE')

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Logout successful"}, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)

class ProfileViewSet(viewsets.ModelViewSet):
    serializer_class = ProfileSerializer
    permission_classes = [IsOwnerOrAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ProfileFilter

    def get_queryset(self):
        # Swagger compatibility
        if getattr(self, "swagger_fake_view", False):
            return Profile.objects.none()

        user = self.request.user

        # Admin sees all profiles
        if getattr(user, 'role', None) == 'admin':
            return Profile.objects.all()

        # Everyone else sees ONLY their own profile
        return Profile.objects.filter(user=user)

    def perform_create(self, serializer):
        # Ensure one profile per user
        if Profile.objects.filter(user=self.request.user).exists():
            raise ValidationError("You already have a profile.")
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def me(self, request):
        profile = Profile.objects.get(user=request.user)
        serializer = self.get_serializer(profile)
        return Response(serializer.data)

class CompanyReviewViewSet(viewsets.ModelViewSet):
    serializer_class = CompanyReviewSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = CompanyReviewFilter

    def get_queryset(self):
        company_pk = self.kwargs.get("company_pk")
        return CompanyReview.objects.filter(company_id=company_pk)

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        company_pk = self.kwargs.get("company_pk")

        # Validate company existence
        company = get_object_or_404(Company, company_id=company_pk)

        # Prevent company owner from reviewing own company
        if company.user == self.request.user:
            raise PermissionDenied("You cannot post review for your own company")

        # Save the review with current user & company
        serializer.save(user=self.request.user, company=company)

class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    permission_classes = [IsParticipantOrAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ConversationFilter

    def get_queryset(self):
        user = self.request.user
        return (
            Conversation.objects
            .filter(participants=user)
            .prefetch_related(
                'participants',
                Prefetch(
                    'messages',
                    queryset=Message.objects.select_related('sender', 'receiver', 'parent_message').order_by('created_at')
                )
            )
            .order_by('-created_at')
        )

    def perform_create(self, serializer):
        participants = serializer.validated_data.get('participants', [])

        if not participants:
            raise ValidationError("At least one participant (receiver) must be provided when creating a conversation.")

        conversation = serializer.save()

        participant_ids = {self.request.user.user_id}
        participant_ids.update(user.user_id for user in participants)

        conversation.participants.set(User.objects.filter(user_id__in=participant_ids))

class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [IsParticipantOrAdmin]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = MessageFilter
    search_fields = ['content', 'sender__username', 'receiver__username']

    def get_queryset(self):
        user = self.request.user
        conversation_pk = self.kwargs.get('conversation_pk')

        if not conversation_pk:
            raise NotFound("Conversation context is required.")

        queryset = (
            Message.objects
            .filter(conversation__participants=user)
            .select_related('sender', 'receiver', 'conversation', 'parent_message')
            .prefetch_related(
                'edit_history',
                Prefetch('replies', queryset=Message.objects.select_related('sender', 'receiver').order_by('created_at'))
            )
            .order_by('created_at')
        )

        return queryset.filter(conversation_id=conversation_pk)
    
    def perform_create(self, serializer):
        conversation_pk = self.kwargs.get('conversation_pk')

        if not conversation_pk:
            raise ValidationError("Conversation context is required.")

        conversation = get_object_or_404(Conversation, pk=conversation_pk)

        parent_message = serializer.validated_data.get('parent_message')

        # Ensure user is a participant of the conversation
        if self.request.user not in conversation.participants.all():
            raise PermissionDenied("You cannot send messages to a conversation you are not part of.")

        if parent_message and parent_message.conversation_id != conversation.conversation_id:
            raise ValidationError("Reply message must belong to the same conversation.")

        receiver = (
            conversation.participants
            .exclude(user_id=self.request.user.user_id)
            .order_by('user_id')
            .first()
        ) or self.request.user

        serializer.save(
            sender=self.request.user,
            receiver=receiver,
            conversation=conversation
        )

    def perform_update(self, serializer):
        message = self.get_object()
        role = getattr(self.request.user, 'role', None)

        if role != 'admin' and message.sender != self.request.user:
            raise PermissionDenied("You can only edit your own messages.")

        serializer.save()

    @action(detail=True, methods=['get'], url_path='history')
    def history(self, request, pk=None):
        message = self.get_object()
        history_queryset = message.edit_history.all()
        serializer = MessageHistorySerializer(history_queryset, many=True)
        return Response(serializer.data)

    def _get_recursive_replies(self, parent_message):
        replies = list(
            Message.objects
            .filter(parent_message=parent_message)
            .select_related('sender', 'receiver', 'parent_message')
            .order_by('created_at')
        )

        for reply in replies:
            reply._threaded_replies = self._get_recursive_replies(reply)

        return replies

    @action(detail=True, methods=['get'], url_path='thread')
    def thread(self, request, pk=None):
        root_message = self.get_object()
        root_message._threaded_replies = self._get_recursive_replies(root_message)
        serializer = ThreadedMessageSerializer(root_message)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='inbox/unread')
    def unread_inbox(self, request):
        conversation_pk = self.kwargs.get('conversation_pk')

        if not conversation_pk:
            raise NotFound("Conversation context is required.")

        unread_messages = (
            Message.unread_messages
            .unread_for_user(request.user)
            .filter(conversation_id=conversation_pk)
            .select_related('sender')
            .only(
                'message_id',
                'conversation_id',
                'sender_id',
                'sender__username',
                'content',
                'created_at',
                'read',
            )
            .order_by('-created_at')
        )

        serializer = UnreadInboxMessageSerializer(unread_messages, many=True)
        return Response(serializer.data)

class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = NotificationFilter

    def get_queryset(self):
        # Skip logic during Swagger schema generation
        if getattr(self, "swagger_fake_view", False):
            return Notification.objects.none()

        role = getattr(self.request.user, 'role', None)

        # Admins can see all notifications
        if role == 'admin':
            return Notification.objects.all()

        # Authenticated non-admin users only see notifications addressed to them
        if self.request.user and self.request.user.is_authenticated:
            return Notification.objects.filter(receiver=self.request.user)

        raise PermissionDenied("You do not have permission to access this request.")

    def create(self, request, *args, **kwargs):
        raise MethodNotAllowed('POST')

    @action(detail=True, methods=["patch"], url_path="mark-as-read")
    def mark_as_read(self, request, company_pk=None, pk=None):
        """Custom route to mark a notification as read"""

        role = getattr(request.user, 'role', None)

        # Admins can mark any notification
        if role == 'admin':
            notification = get_object_or_404(Notification, pk=pk)

        # Non-admins can mark only their own notifications
        elif request.user and request.user.is_authenticated:
            notification = get_object_or_404(Notification, pk=pk, receiver=request.user)

        else:
            raise PermissionDenied("You do not have permission to perform this action.")

        if not notification.is_read:
            notification.is_read = True
            notification.save(update_fields=["is_read"])

        serializer = self.get_serializer(notification)
        return Response(serializer.data, status=status.HTTP_200_OK)

def home(request):
    return JsonResponse(
        {
            "message": "Job Board API is live 🚀",
            "docs": "/api/docs/",
            "api_base": "/api/"
        },
        json_dumps_params={"ensure_ascii": False}
    )

class DeleteUserViewSet(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        request.user.delete()
        return Response({"message": "User account deleted successfully."}, status=status.HTTP_200_OK)
