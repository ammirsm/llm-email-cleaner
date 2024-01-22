# initiate django

import os

import django
from retriever.models import EmailAccount

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

django.setup()

EMAIL_ADDRESS = "example@gmail.com"


email_account = EmailAccount.objects.filter()[0]

email_messages = email_account.email_messages.filter(subject__isnull=True)

for email_message in email_messages:
    email_message.load_full_data()
    print(email_message.subject)
