


from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from django.conf import settings
from accounts.serializers import GoogleAuthSerializer


import random
from django.core.mail import send_mail
from django.conf import settings
from accounts.models import PasswordResetCode
from accounts.serializers import (
    RegisterSerializer,
    LoginSerializer,
    RequestResetCodeSerializer,
    VerifyResetCodeSerializer,
    ResetPasswordSerializer,
)



from django.contrib.auth import authenticate, get_user_model
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.serializers import RegisterSerializer, LoginSerializer

User = get_user_model()


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        tokens = get_tokens_for_user(user)
        return Response({
            'user': {
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            },
            'tokens': tokens,
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        user = authenticate(request, username=email, password=password)
        if user is None:
            return Response({'detail': 'Invalid email or password'}, status=status.HTTP_401_UNAUTHORIZED)
        tokens = get_tokens_for_user(user)
        return Response({
            'user': {
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            },
            'tokens': tokens,
        }, status=status.HTTP_200_OK)



class RequestResetCodeView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RequestResetCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        user = User.objects.get(email=email)

        code = str(random.randint(100000, 999999))
        PasswordResetCode.objects.create(user=user, code=code)

        send_mail(
            subject='Your Veltrix password reset code',
            message=f'Your verification code is {code}. It expires in 10 minutes.',
            from_email=None,
            recipient_list=[email],
        )

        return Response({'detail': 'Reset code sent to your email'}, status=status.HTTP_200_OK)


class VerifyResetCodeView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyResetCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        code = serializer.validated_data['code']

        try:
            user = User.objects.get(email=email)
            reset_code = PasswordResetCode.objects.filter(
                user=user, code=code, is_used=False
            ).latest('created_at')
        except (User.DoesNotExist, PasswordResetCode.DoesNotExist):
            return Response({'detail': 'Invalid code'}, status=status.HTTP_400_BAD_REQUEST)

        if reset_code.is_expired():
            return Response({'detail': 'Code has expired'}, status=status.HTTP_400_BAD_REQUEST)

        reset_code.is_verified = True
        reset_code.save()

        return Response({'detail': 'Code verified'}, status=status.HTTP_200_OK)


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        try:
            user = User.objects.get(email=email)
            reset_code = PasswordResetCode.objects.filter(
                user=user, is_verified=True, is_used=False
            ).latest('created_at')
        except (User.DoesNotExist, PasswordResetCode.DoesNotExist):
            return Response({'detail': 'No verified reset request found'}, status=status.HTTP_400_BAD_REQUEST)

        if reset_code.is_expired():
            return Response({'detail': 'Reset session has expired'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(password)
        user.save()

        reset_code.is_used = True
        reset_code.save()

        return Response({'detail': 'Password reset successful'}, status=status.HTTP_200_OK)



class GoogleAuthView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = GoogleAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        credential = serializer.validated_data['credential']

        try:
            idinfo = id_token.verify_oauth2_token(
                credential, google_requests.Request(), settings.GOOGLE_CLIENT_ID
            )
        except ValueError:
            return Response({'detail': 'Invalid Google token'}, status=status.HTTP_400_BAD_REQUEST)

        email = idinfo.get('email')
        first_name = idinfo.get('given_name', '')
        last_name = idinfo.get('family_name', '')

        user, created = User.objects.get_or_create(
            email=email,
            defaults={'first_name': first_name, 'last_name': last_name},
        )

        if created:
            user.set_unusable_password()
            user.save()

        tokens = get_tokens_for_user(user)
        return Response({
            'user': {
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            },
            'tokens': tokens,
        }, status=status.HTTP_200_OK)