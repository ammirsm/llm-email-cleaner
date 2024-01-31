from django.db import models


class EmailMessageSenderManager(models.Manager):
    # add custom annotation to base queryset
    def get_queryset(self):
        """
        - Add number of emails sent by this sender to the queryset
        - Add number of Items in the EmailMessageSender table with the same `email` field
        :return:
        """

        return (
            super()
            .get_queryset()
            .annotate(
                number_of_emails=models.Count("email_messages"),
            )
        )
