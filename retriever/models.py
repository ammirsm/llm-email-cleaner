# Create your models here.
from core.base.models import BaseData
from django.db import models


class EmailAccount(BaseData):
    email = models.CharField(max_length=255)
    creds = models.JSONField(null=True, blank=True)
    token = models.JSONField(null=True, blank=True)


class EmailMessage(BaseData):
    external_id = models.CharField(max_length=255, null=True, blank=True)
    thread_id = models.CharField(max_length=255, null=True)
    snippet = models.TextField(null=True, blank=True)
    internal_date = models.CharField(max_length=255, null=True, blank=True)
    label_ids = models.JSONField(null=True, blank=True)
    history_id = models.CharField(max_length=255, null=True, blank=True)
    subject = models.CharField(max_length=255, null=True, blank=True)
    sender = models.CharField(max_length=255, null=True, blank=True)
    recipient = models.CharField(max_length=255, null=True, blank=True)
    copy = models.TextField(null=True, blank=True)
    email_account = models.ForeignKey(
        "EmailAccount", on_delete=models.CASCADE, related_name="email_messages", null=True
    )
    body = models.TextField(null=True, blank=True)
