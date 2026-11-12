from django.db.models import Q
from django.utils.dateparse import parse_date
from rest_framework import generics

from config.permissions import IsAdmin

from .models import ActivityLog
from .serializers import ActivityLogSerializer


class ActivityLogListView(generics.ListAPIView):
    """Admin-only audit trail with filtering by category, date and free text."""

    serializer_class = ActivityLogSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        queryset = ActivityLog.objects.select_related('actor')
        params = self.request.query_params

        category = params.get('category')
        if category:
            queryset = queryset.filter(category=category)

        search = params.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(description__icontains=search)
                | Q(actor__first_name__icontains=search)
                | Q(actor__last_name__icontains=search)
                | Q(actor__email__icontains=search)
            )

        date_from = parse_date(params.get('date_from', '') or '')
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        date_to = parse_date(params.get('date_to', '') or '')
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)

        return queryset
