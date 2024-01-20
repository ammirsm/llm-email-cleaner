from retriever.services import GmailLoader

GMAIL = "gmail"


class EmailAccountTypes(object):
    definition = {
        GMAIL: {
            "name": "Gmail",
            "scopes": ["https://www.googleapis.com/auth/gmail.readonly"],
            "loader_class": GmailLoader,
        }
    }

    @classmethod
    def get(cls, service):
        return cls.definition.get(service)

    @classmethod
    def get_choices(cls):
        return [(k, v["name"]) for k, v in cls.definition.items()]
