"""Refresh-token cookie helpers.

The refresh token is delivered only as an HttpOnly cookie scoped to
`/api/auth/`, so page JavaScript can never read it and it is not sent with
ordinary API calls.
"""
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken


def issue_tokens(user):
    refresh = RefreshToken.for_user(user)
    return refresh, str(refresh.access_token)


def set_refresh_cookie(response, refresh):
    lifetime = settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME']
    response.set_cookie(
        settings.REFRESH_COOKIE_NAME,
        str(refresh),
        max_age=int(lifetime.total_seconds()),
        httponly=True,
        secure=settings.REFRESH_COOKIE_SECURE,
        samesite=settings.REFRESH_COOKIE_SAMESITE,
        path=settings.REFRESH_COOKIE_PATH,
    )


def clear_refresh_cookie(response):
    response.delete_cookie(
        settings.REFRESH_COOKIE_NAME,
        path=settings.REFRESH_COOKIE_PATH,
        samesite=settings.REFRESH_COOKIE_SAMESITE,
    )
