from advanced_filters.admin import AdminAdvancedFiltersMixin
from django.contrib import admin
from django.db import models

from .models import EmailAccount, EmailMessage, EmailMessageSender
from .tasks import fill_full_data


class EmailAccountAdmin(admin.ModelAdmin):
    list_display = ("email", "service_type")
    search_fields = ("email",)


admin.site.register(EmailAccount, EmailAccountAdmin)


class EmailMessageAdmin(AdminAdvancedFiltersMixin, admin.ModelAdmin):
    list_display = ("external_id", "subject", "email_sender", "recipient")
    search_fields = ("subject", "sender", "recipient")
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


class EmailMessageSenderAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "email_account", "number_of_emails")
    search_fields = ("name", "email")
    list_filter = ("email_account",)

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .annotate(
                number_of_emails=models.Count("email_messages"),
            )
        )

    def number_of_emails(self, obj):
        return obj.number_of_emails

    number_of_emails.admin_order_field = "number_of_emails"


admin.site.register(EmailMessageSender, EmailMessageSenderAdmin)
