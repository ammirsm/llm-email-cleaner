from core.settings import GMAIL_CREDS_PATH
from django.test import TestCase

from retriever.constants import GMAIL


class GmailReaderTest(TestCase):
    def test_gmail_reader(self):
        # GIVEN config/credentials.json to dict
        import json

        with open(GMAIL_CREDS_PATH) as f:
            creds = json.load(f)

        # WHEN create new EmailAccount object
        from retriever.models import EmailAccount

        email_account = EmailAccount.objects.create(
            email="amir@amir.com", creds=creds, token=None, service_type=GMAIL
        )
        self.assertIsNotNone(email_account)

        # THEN we should be able to load emails.
        loader = email_account.get_loader_class(max_results=500)

        # load data from GmailReader
        data = loader.load_data()
        self.assertIsNotNone(data)
