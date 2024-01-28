from advanced_filters.admin import AdminAdvancedFiltersMixin
from django.contrib import admin

from .models import EmailAccount, EmailMessage
from .tasks import fill_full_data


class EmailAccountAdmin(admin.ModelAdmin):
    list_display = ("email", "service_type")
    search_fields = ("email",)


admin.site.register(EmailAccount, EmailAccountAdmin)


class EmailMessageAdmin(AdminAdvancedFiltersMixin, admin.ModelAdmin):
    list_display = ("external_id", "subject", "sender", "recipient")
    search_fields = ("subject", "sender", "recipient")
    # list_filter = ("subject",)
    sortable_by = ("subject",)

    actions = ["run_load_full_data"]

    advanced_filter_fields = (
        "subject",
        "sender",
        "recipient",
    )

    def run_load_full_data(self, request, queryset):
        for obj in queryset:
            fill_full_data.delay(obj.id, "EmailMessage")

    run_load_full_data.short_description = "Load full data for selected EmailMessages"


admin.site.register(EmailMessage, EmailMessageAdmin)
