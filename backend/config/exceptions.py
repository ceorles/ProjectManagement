"""
One error shape for the whole API.

Every failed request returns:

    {"error": {"code": "...", "message": "...", "fields": {"field": ["..."]}}}

`code` is stable and machine-readable, `message` is safe to show to a user,
and `fields` is only present for validation errors.
"""
from django.core.exceptions import PermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import ProtectedError
from django.http import Http404
from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.views import exception_handler


class ApiError(exceptions.APIException):
    """Business-rule failure with a stable error code."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_code = 'invalid_request'

    def __init__(self, message, code=None, status_code=None):
        super().__init__(detail=message, code=code or self.default_code)
        if status_code is not None:
            self.status_code = status_code


class ConflictError(ApiError):
    status_code = status.HTTP_409_CONFLICT
    default_code = 'conflict'


def _flatten(detail):
    """Turn DRF's nested error detail into {field: [messages]}."""
    if isinstance(detail, dict):
        fields = {}
        for key, value in detail.items():
            if isinstance(value, dict):
                for sub_key, sub_value in _flatten(value).items():
                    fields[f'{key}.{sub_key}'] = sub_value
            elif isinstance(value, (list, tuple)):
                messages = []
                for item in value:
                    if isinstance(item, (dict, list, tuple)):
                        for nested in _flatten(item).values():
                            messages.extend(nested)
                    else:
                        messages.append(str(item))
                fields[key] = messages
            else:
                fields[key] = [str(value)]
        return fields
    if isinstance(detail, (list, tuple)):
        return {'non_field_errors': [str(item) for item in detail]}
    return {'non_field_errors': [str(detail)]}


def _first_message(fields):
    for key in ('non_field_errors', 'detail'):
        if fields.get(key):
            return fields[key][0]
    for messages in fields.values():
        if messages:
            return messages[0]
    return 'The submitted data is not valid.'


def api_exception_handler(exc, context):
    if isinstance(exc, DjangoValidationError):
        exc = exceptions.ValidationError(
            exc.message_dict if hasattr(exc, 'error_dict') else exc.messages
        )
    if isinstance(exc, ProtectedError):
        exc = ConflictError(
            'This cannot be deleted because other records (such as seats or past '
            'reservations) still depend on it. Take it out of service instead.',
            code='in_use',
        )

    response = exception_handler(exc, context)
    if response is None:
        return None  # unexpected error: let Django produce the 500

    if isinstance(exc, exceptions.ValidationError):
        fields = _flatten(exc.detail)
        general = fields.pop('non_field_errors', None)
        message = general[0] if general else _first_message(fields)
        payload = {'code': 'validation_error', 'message': message}
        if fields:
            payload['fields'] = fields
    elif isinstance(exc, Http404):
        payload = {'code': 'not_found', 'message': 'The requested record was not found.'}
    elif isinstance(exc, PermissionDenied):
        payload = {
            'code': 'permission_denied',
            'message': 'You do not have permission to perform this action.',
        }
    else:
        detail = getattr(exc, 'detail', None)
        code = getattr(detail, 'code', None) or getattr(exc, 'default_code', 'error')
        if isinstance(detail, dict):
            # e.g. SimpleJWT's InvalidToken: {"detail": ..., "code": ...}
            code = str(detail.get('code', code))
            message = str(detail.get('detail', 'The request could not be processed.'))
        else:
            message = str(detail) if detail is not None else 'The request could not be processed.'
        payload = {'code': code, 'message': message}

    response.data = {'error': payload}
    return response
