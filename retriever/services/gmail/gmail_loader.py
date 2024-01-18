__all__ = ["GmailReader"]
# inspired by https://github.com/run-llama/llama-hub/tree/956aa44b6dfa3e085b9b9a80c3caec0144b1bbbf/llama_hub/gmail

import base64
import email
import os
from typing import List, Optional

from core.settings import GMAIL_CREDS_PATH, GMAIL_TOKEN_PATH, SCOPES
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from llama_index import Document
from llama_index.readers.base import BaseReader


class GmailReader(BaseReader):
    def __init__(
        self,
        query: Optional[str] = None,
        results_per_page: Optional[int] = 10,
        use_iterative_parser: Optional[bool] = False,
        max_results: Optional[int] = 10,
    ):
        self.query = query
        self.results_per_page = results_per_page
        self.use_iterative_parser = use_iterative_parser
        self.max_results = max_results
        self.service = None

    def load_data(self) -> List[Document]:
        """Load emails from the user's account."""
        self.service = self.service or self._build_service()
        messages = self._search_messages()
        return messages

    def _build_service(self):
        """Build the Gmail API service."""
        credentials = self._get_credentials()
        return build("gmail", "v1", credentials=credentials)

    @staticmethod
    def _get_credentials():
        """Get valid user credentials from storage."""
        creds = None
        if os.path.exists(GMAIL_TOKEN_PATH):
            creds = Credentials.from_authorized_user_file(GMAIL_TOKEN_PATH, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(GMAIL_CREDS_PATH, SCOPES)
                creds = flow.run_local_server(port=8080)
            with open(GMAIL_TOKEN_PATH, "w") as token:
                token.write(creds.to_json())

        return creds

    def _search_messages(self):
        """Search messages based on the query."""
        results = (
            self.service.users()
            .messages()
            .list(userId="me", q=self.query, maxResults=int(self.results_per_page))
            .execute()
        )

        messages = results.get("messages", [])
        self._paginate_messages(messages, results)

        return self._process_messages(messages)

    def _paginate_messages(self, messages, results):
        """Handle message pagination."""
        while "nextPageToken" in results and len(messages) < self.max_results:
            page_token = results["nextPageToken"]
            results = (
                self.service.users()
                .messages()
                .list(userId="me", q=self.query, pageToken=page_token, maxResults=int(self.results_per_page))
                .execute()
            )
            messages.extend(results.get("messages", []))

    def _process_messages(self, messages):
        """Process and parse messages."""
        result = []
        for message in messages:
            try:
                message_data = self._get_message_data(message)
                if message_data:
                    result.append(message_data)
            except Exception as e:
                raise Exception(f"Can't get message data: {e}")

        return result

    def _get_message_data(self, message):
        """Get data from a single message."""
        message_id = message["id"]
        message_data = self.service.users().messages().get(userId="me", id=message_id, format="raw").execute()

        parser = self._extract_message_body_iterative if self.use_iterative_parser else self._extract_message_body
        body, subject, sender, recipient, copy = parser(message_data)

        if not body:
            return None

        # https://developers.google.com/gmail/api/reference/rest/v1/users.messages
        return {
            "id": message_data["id"],
            "threadId": message_data["threadId"],
            "snippet": message_data["snippet"],
            "internalDate": message_data["internalDate"],
            "body": body,
            "labelIds": message_data["labelIds"],
            "historyId": message_data["historyId"],
            "subject": subject,
            "sender": sender,
            "recipient": recipient,
            "copy": copy,
        }

    def _extract_message_body_iterative(self, message: dict, is_top_level=True):
        if is_top_level and "raw" in message:
            body = base64.urlsafe_b64decode(message["raw"].encode("utf-8"))
            mime_msg = email.message_from_bytes(body)
        else:
            mime_msg = message

        subject, sender, recipient, copy = None, None, None, None

        # Extract email details at the top level
        if is_top_level:
            subject = mime_msg["Subject"]
            sender = mime_msg["From"]
            recipient = mime_msg["To"]
            copy = mime_msg["Cc"]

        body_text = ""
        if mime_msg.get_content_type() == "text/plain":
            plain_text = mime_msg.get_payload(decode=True)
            charset = mime_msg.get_content_charset("utf-8")
            body_text = plain_text.decode(charset)

        elif mime_msg.get_content_maintype() == "multipart":
            for part in mime_msg.get_payload():
                body_text += self._extract_message_body_iterative(part, is_top_level=False)

        if is_top_level:
            return subject, sender, recipient, body_text, copy
        else:
            return body_text

    @staticmethod
    def _extract_message_body(message: dict):
        from bs4 import BeautifulSoup

        try:
            body = base64.urlsafe_b64decode(message["raw"].encode("utf-8"))
            mime_msg = email.message_from_bytes(body)

            # If the message body contains HTML, parse it with BeautifulSoup
            if "text/html" in mime_msg:
                soup = BeautifulSoup(body, "html.parser")
                body = soup.get_text()

            subject = mime_msg["Subject"]
            sender = mime_msg["From"]
            recipient = mime_msg["To"]
            copy = mime_msg["Cc"]

            return body.decode("utf-8"), subject, sender, recipient, copy
        except Exception as e:
            raise Exception("Can't parse message body" + str(e))
