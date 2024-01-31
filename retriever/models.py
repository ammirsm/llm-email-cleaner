# Create your models here.
from core.base.models import BaseData
from django.db import models

from retriever.constants import EmailAccountTypes
from retriever.managers import EmailMessageSenderManager


class EmailAccount(BaseData):
    email = models.CharField(max_length=5000)
    creds = models.JSONField(null=True, blank=True)
    token = models.JSONField(null=True, blank=True)
    # Field for the showing it is using which service (Gmail, Outlook, etc.)
    service_type = models.CharField(max_length=5000, null=True, blank=True, choices=EmailAccountTypes.get_choices())

    def get_loader_class(self, results_per_page=10, max_results=10):
        loader = EmailAccountTypes.get(self.service_type)["loader_class"](
            creds=self.creds,
            token=self.token,
            results_per_page=results_per_page,
            max_results=max_results,
        )
        self.token = loader.get_token()
        self.save()
        return loader

    def _load_ids_with_loader(self, results_per_page=10, max_results=10):
        loader = self.get_loader_class(results_per_page=results_per_page, max_results=max_results)
        return loader.load_message_ids()

    def load_ids_to_email_messages(self, results_per_page=10, max_results=10):
        data = self._load_ids_with_loader(results_per_page=results_per_page, max_results=max_results)
        email_messages = []

        for d in data:
            email_messages.append(EmailMessage(external_id=d["id"], thread_id=d["threadId"], email_account=self))
            print("add", d["id"])

        # bulk create email messages
        EmailMessage.objects.bulk_create(email_messages)

    def remove_token(self):
        self.token = None
        self.save()


class EmailMessage(BaseData):
    external_id = models.CharField(max_length=5000, null=True, blank=True)
    thread_id = models.CharField(max_length=5000, null=True)
    snippet = models.TextField(null=True, blank=True)
    internal_date = models.CharField(max_length=5000, null=True, blank=True)
    label_ids = models.JSONField(null=True, blank=True)
    history_id = models.CharField(max_length=5000, null=True, blank=True)
    subject = models.CharField(max_length=5000, null=True, blank=True)
    sender = models.CharField(max_length=5000, null=True, blank=True)
    recipient = models.CharField(max_length=5000, null=True, blank=True)
    copy = models.TextField(null=True, blank=True)
    email_account = models.ForeignKey(
        "EmailAccount", on_delete=models.CASCADE, related_name="email_messages", null=True
    )
    body = models.TextField(null=True, blank=True)
    email_sender = models.ForeignKey(
        "EmailMessageSender", on_delete=models.CASCADE, related_name="email_messages", null=True
    )

    def load_full_data(self):
        loader = self.email_account.get_loader_class()
        data = loader.load_full_data(message_id=self.external_id)
        data.pop("id", None)
        data.pop("threadId", None)
        self.snippet = data.get("snippet", None)
        self.internal_date = data.get("internalDate", None)
        self.label_ids = data.get("labelIds", None)
        self.history_id = data.get("historyId", None)
        self.subject = data.get("subject", None)
        self.sender = data.get("sender", None)
        self.recipient = data.get("recipient", None)
        self.copy = data.get("copy", None)
        self.body = data.get("body", None)
        self.save()


class EmailMessageSender(BaseData):
    name = models.CharField(max_length=5000, null=True, blank=True)
    email = models.CharField(max_length=5000, null=True, blank=True)
    email_account = models.ForeignKey(
        "EmailAccount", on_delete=models.CASCADE, related_name="email_message_senders", null=True
    )

    objects = EmailMessageSenderManager()

    def __str__(self):
        return f"{self.email}"
