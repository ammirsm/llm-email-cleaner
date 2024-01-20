from core.settings import GMAIL_CREDS_PATH
from django.test import TestCase


class GmailReaderTest(TestCase):
    def test_gmail_reader(self):
        # read config/credentials.json to dict
        import json

        from retriever.services import GmailReader

        with open(GMAIL_CREDS_PATH) as f:
            creds = json.load(f)

        # create new EmailAccount object
        from retriever.models import EmailAccount

        email_account = EmailAccount.objects.create(email="amir@amir.com", creds=creds, token=None)
        self.assertIsNotNone(email_account)

        # create new GmailReader object
        gmail_reader = GmailReader(creds=creds)

        # set token to EmailAccount object
        email_account.token = gmail_reader.get_token()
        email_account.save()

        gmail_reader = GmailReader(creds=email_account.creds, token=email_account.token)

        # load data from GmailReader
        data = gmail_reader.load_data()
        self.assertIsNotNone(data)
