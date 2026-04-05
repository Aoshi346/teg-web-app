from django.contrib import admin
from .models import SessionLog

@admin.register(SessionLog)
class SessionLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'device', 'browser', 'ip_address', 'is_active', 'created_at', 'last_active_at']
    list_filter = ['is_active', 'device', 'browser']
    search_fields = ['user__email', 'ip_address']
    readonly_fields = ['session_key', 'created_at', 'last_active_at']
