

from django.urls import path
from accounts.views import (
    RegisterView,
    LoginView,
    RequestResetCodeView,
    VerifyResetCodeView,
    ResetPasswordView,
    GoogleAuthView,
)
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('password-reset/request/', RequestResetCodeView.as_view(), name='password_reset_request'),
    path('password-reset/verify/', VerifyResetCodeView.as_view(), name='password_reset_verify'),
    path('password-reset/confirm/', ResetPasswordView.as_view(), name='password_reset_confirm'),
    path('google/', GoogleAuthView.as_view(), name='google_auth'),
]