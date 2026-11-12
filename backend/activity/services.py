from .models import ActivityLog


def _client_ip(request):
    if request is None:
        return None
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip() or None
    return request.META.get('REMOTE_ADDR') or None


def log_activity(action, description, *, actor=None, target=None, request=None):
    """
    Record an audit entry.

    `action` is "<category>.<verb>", for example "reservation.cancelled".
    `target` is the model instance the action was performed on, if any.
    """
    category = action.split('.', 1)[0]
    if actor is not None and not getattr(actor, 'is_authenticated', False):
        actor = None
    return ActivityLog.objects.create(
        actor=actor,
        category=category,
        action=action,
        description=description[:255],
        target_type=target._meta.model_name if target is not None else '',
        target_id=target.pk if target is not None else None,
        ip_address=_client_ip(request),
    )
