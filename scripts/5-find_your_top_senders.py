# initiate django

import django
from retriever.models import EmailAccount, EmailMessageSender, EmailMessage
import re

django.setup()

# Select the email account
email_account = EmailAccount.objects.first()

email_senders = email_account.email_senders.all().values("email").distinct()

email_messages = email_account.email_messages.all()
