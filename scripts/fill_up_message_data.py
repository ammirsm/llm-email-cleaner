import django
from retriever.tasks import fill_full_data
from retriever.models import EmailAccount

django.setup()

EMAIL_ADDRESS = "example@gmail.com"

email_account = EmailAccount.objects.get(email=EMAIL_ADDRESS)

email_messages = email_account.emailmessage_set.filter(subject__isnull=True)

for i in email_messages:
    fill_full_data.delay(i.id, "EmailMessage")
