from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ('last_name', 'first_name')
    list_display = ('email', 'first_name', 'last_name', 'role', 'student_id', 'is_active')
    list_filter = ('role', 'is_active')
    search_fields = ('email', 'first_name', 'last_name', 'student_id')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal details', {'fields': ('first_name', 'last_name', 'phone')}),
        ('Role', {'fields': ('role', 'can_manage_resources')}),
        ('Student details', {'fields': ('student_id', 'program', 'year_level')}),
        ('Access', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups',
                               'user_permissions')}),
        ('Dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'role', 'password1', 'password2'),
        }),
    )
