from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Presentation, PresentationDay, PresentationJuror, SessionLog, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ['email']
    list_display = ['email', 'first_name', 'last_name', 'nationality', 'cedula', 'role', 'status', 'is_staff']
    list_filter = ['role', 'status', 'nationality', 'is_staff', 'is_superuser']
    search_fields = ['email', 'first_name', 'last_name']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'nationality', 'cedula', 'phone', 'semester')}),
        ('Roles & status', {'fields': ('role', 'status')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name', 'nationality', 'cedula', 'role', 'status'),
        }),
    )


class PresentationJurorInline(admin.TabularInline):
    model = PresentationJuror
    extra = 0
    fields = ('juror', 'individual_score', 'notified', 'notified_at', 'confirmed_attendance', 'attended')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Presentation)
class PresentationAdmin(admin.ModelAdmin):
    list_display = ['project', 'day', 'tutor', 'start_time', 'order']
    list_filter = ['day']
    inlines = [PresentationJurorInline]


@admin.register(PresentationJuror)
class PresentationJurorAdmin(admin.ModelAdmin):
    list_display = ['presentation', 'juror', 'individual_score', 'notified', 'confirmed_attendance', 'attended']
    list_filter = ['notified', 'confirmed_attendance', 'attended']
    search_fields = ['juror__email', 'presentation__project__title']


@admin.register(PresentationDay)
class PresentationDayAdmin(admin.ModelAdmin):
    list_display = ['date', 'semester', 'notes', 'created_by', 'created_at']
    list_filter = ['semester']


@admin.register(SessionLog)
class SessionLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'device', 'browser', 'ip_address', 'is_active', 'created_at', 'last_active_at']
    list_filter = ['is_active', 'device', 'browser']
    search_fields = ['user__email', 'ip_address']
    readonly_fields = ['session_key', 'created_at', 'last_active_at']
