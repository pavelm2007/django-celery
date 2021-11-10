from date_range_filter import DateRangeFilter
from django.contrib import admin

from notifications.models import Notification


@admin.register(Notification)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('receiver', 'type_notify', 'is_sent', 'count_attempts', 'created_at',)
    list_filter = (
        'type_notify',
        ('created_at', DateRangeFilter),
    )
    search_fields = ('customer__user__first_name', 'customer__user__last_name')
    actions_on_top = False
    actions_on_bottom = True
