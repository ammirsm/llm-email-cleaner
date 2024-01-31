# initiate django

import django
from retriever.models import EmailAccount, EmailMessageSender, EmailMessage
import re

django.setup()

# Select the email account
email_account = EmailAccount.objects.first()

# Load list of email senders
email_senders = email_account.email_messages.all().values_list("sender", flat=True).distinct()

senders = []

# Create email senders
for email_sender in email_senders:
    if email_sender is None:
        continue

    # most of the time email senders are like this: "Sender Name <sender@example>"
    pattern = r"(.*?)\s*<(.*)>"
    match = re.match(pattern, email_sender)
    sender_name = ""
    email_address = ""

    if match:
        # Extract the sender name
        sender_name = match.group(1).strip()
        # Extract the email address
        email_address = match.group(2).strip()

    senders.append(
        EmailMessageSender(
            name=sender_name,
            email=email_address,
            email_account=email_account,
        )
    )

# bulk create email senders
EmailMessageSender.objects.bulk_create(senders)

# Update email messages with email senders
email_senders = EmailMessageSender.objects.all()

for email_sender in email_senders:
    email_messages = EmailMessage.objects.filter(sender=f"{email_sender.name} <{email_sender.email}>")
    email_messages.update(email_sender=email_sender)
