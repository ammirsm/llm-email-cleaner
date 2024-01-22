from core.settings import GMAIL_CREDS_PATH, GMAIL_TOKEN_PATH
from django.test import TestCase

from retriever.constants import GMAIL
from retriever.models import EmailMessage


class GmailReaderTest(TestCase):
    def test_gmail_reader(self):
        # GIVEN config/credentials.json to dict
        import json

        with open(GMAIL_CREDS_PATH) as f:
            creds = json.load(f)

        with open(GMAIL_TOKEN_PATH) as f:
            token = json.load(f)

        # WHEN create new EmailAccount object
        from retriever.models import EmailAccount

        email_account = EmailAccount.objects.create(
            email="amir@amir.com", creds=creds, token=token, service_type=GMAIL
        )
        self.assertIsNotNone(email_account)

        # WHEN load email messages
        email_account.load_ids_to_email_messages()

        # WHEN load full data
        for message in email_account.email_messages.all():
            message.load_full_data()

        # THEN we should be able to load emails.
        self.assertIsNotNone(EmailMessage.objects.filter(email_account=email_account))
