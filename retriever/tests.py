# Create your tests here.

from django.test import TestCase


class GmailReaderTest(TestCase):
    def test_gmail_reader(self):
        from retriever.services import GmailReader

        gmail_reader = GmailReader()
        data = gmail_reader.load_data()
        self.assertIsNotNone(data)
