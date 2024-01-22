# initiate django

import json

import django
from core.settings import GMAIL_CREDS_PATH, GMAIL_TOKEN_PATH
from retriever.constants import GMAIL
from retriever.models import EmailAccount

django.setup()


EMAIL_ADDRESS = "example@gmail.com"

with open(GMAIL_CREDS_PATH) as f:
    creds = json.load(f)

with open(GMAIL_TOKEN_PATH) as f:
    token = json.load(f)


email_account = EmailAccount.objects.create(email=EMAIL_ADDRESS, creds=creds, token=token, service_type=GMAIL)
