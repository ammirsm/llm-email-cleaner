from django.contrib import admin

from .models import EmailAccount, EmailMessage


class EmailAccountAdmin(admin.ModelAdmin):
    list_display = ("email", "service_type")
    search_fields = ("email",)


admin.site.register(EmailAccount, EmailAccountAdmin)


class EmailMessageAdmin(admin.ModelAdmin):
    list_display = ("external_id", "subject", "sender", "recipient")
    search_fields = ("subject", "sender", "recipient")


admin.site.register(EmailMessage, EmailMessageAdmin)
