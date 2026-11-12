"""Registration, login, session restore, logout and the user's own profile."""
from datetime import datetime, timedelta
from datetime import timezone as dt_timezone

from django.conf import settings
from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from activity.services import log_activity

from .models import User
from .serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    ProfileUpdateSerializer,
    RegisterSerializer,
    UserSerializer,
)
from .tokens import clear_refresh_cookie, issue_tokens, set_refresh_cookie

# A refresh token is replaced once it is older than this, so an active user's
# session keeps sliding forward without writing a new token on every refresh.
REFRESH_REISSUE_AFTER = timedelta(days=1)


def _session_response(user, *, refresh=None, http_status=status.HTTP_200_OK):
    """Build the {access, user} body and attach the refresh cookie."""
    if refresh is None:
        refresh, access = issue_tokens(user)
        response = Response({'access': access, 'user': UserSerializer(user).data}, status=http_status)
        set_refresh_cookie(response, refresh)
        return response
    return Response(
        {'access': str(refresh.access_token), 'user': UserSerializer(user).data},
        status=http_status,
    )


class PublicEndpointMixin:
    """
    For endpoints that are called without an access token. DRF downgrades a
    401 to 403 when a view has no authenticator to name in the
    WWW-Authenticate header, so the scheme is declared here.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def get_authenticate_header(self, request):
        return 'Bearer realm="api"'


class CookieAuthMixin:
    """
    Endpoints that act on the refresh cookie require a custom header. A plain
    cross-site form post cannot add it, and a cross-site script request that
    does is stopped by the CORS preflight.
    """

    def require_ajax(self, request):
        if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
            raise PermissionDenied('This request must be sent by the application.')


class RegisterView(PublicEndpointMixin, APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'register'

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        log_activity(
            'user.registered', f'{user.full_name} registered a student account.',
            actor=user, target=user, request=request,
        )
        return _session_response(user, http_status=status.HTTP_201_CREATED)


class LoginView(PublicEndpointMixin, APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'login'

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email'].strip().lower()
        password = serializer.validated_data['password']

        user = authenticate(request, username=email, password=password)
        if user is None:
            # authenticate() also returns None for deactivated accounts; tell
            # those users apart only when the password was actually correct.
            candidate = User.objects.filter(email__iexact=email).first()
            if candidate and not candidate.is_active and candidate.check_password(password):
                raise PermissionDenied(
                    'This account has been deactivated. Please contact the library.'
                )
            raise AuthenticationFailed('Incorrect email or password.', code='invalid_credentials')

        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        log_activity('auth.login', f'{user.full_name} signed in.', actor=user, request=request)
        return _session_response(user)


class RefreshView(PublicEndpointMixin, CookieAuthMixin, APIView):
    """Exchange the refresh cookie for a new access token (used on page load)."""

    def post(self, request):
        self.require_ajax(request)
        raw = request.COOKIES.get(settings.REFRESH_COOKIE_NAME)
        if not raw:
            raise AuthenticationFailed('You are not signed in.', code='no_session')
        try:
            refresh = RefreshToken(raw)
            user = User.objects.get(pk=refresh['user_id'])
        except (TokenError, User.DoesNotExist, KeyError):
            response = Response(
                {'error': {'code': 'session_expired',
                           'message': 'Your session has expired. Please sign in again.'}},
                status=status.HTTP_401_UNAUTHORIZED,
            )
            clear_refresh_cookie(response)
            return response

        if not user.is_active:
            response = Response(
                {'error': {'code': 'account_disabled',
                           'message': 'This account has been deactivated.'}},
                status=status.HTTP_401_UNAUTHORIZED,
            )
            clear_refresh_cookie(response)
            return response

        issued_at = datetime.fromtimestamp(refresh['iat'], tz=dt_timezone.utc)
        if timezone.now() - issued_at > REFRESH_REISSUE_AFTER:
            return _session_response(user)  # issues and sets a fresh cookie
        return _session_response(user, refresh=refresh)


class LogoutView(PublicEndpointMixin, CookieAuthMixin, APIView):

    def post(self, request):
        self.require_ajax(request)
        raw = request.COOKIES.get(settings.REFRESH_COOKIE_NAME)
        if raw:
            try:
                refresh = RefreshToken(raw)
                user = User.objects.filter(pk=refresh['user_id']).first()
                refresh.blacklist()
                if user:
                    log_activity('auth.logout', f'{user.full_name} signed out.',
                                 actor=user, request=request)
            except TokenError:
                pass  # already expired or revoked: nothing left to invalidate
        response = Response(status=status.HTTP_204_NO_CONTENT)
        clear_refresh_cookie(response)
        return response


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        serializer = ProfileUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        log_activity('user.profile_updated', f'{request.user.full_name} updated their profile.',
                     actor=request.user, target=request.user, request=request)
        return Response(UserSerializer(request.user).data)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save(update_fields=['password'])
        log_activity('user.password_changed', f'{request.user.full_name} changed their password.',
                     actor=request.user, target=request.user, request=request)
        return Response({'message': 'Your password has been changed.'})
