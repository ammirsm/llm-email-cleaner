# initiate django

import django
from retriever.models import EmailAccount

django.setup()

EMAIL_ADDRESS = "example@gmail.com"


email_account = EmailAccount.objects.get(email=EMAIL_ADDRESS)

email_account.load_ids_to_email_messages()
