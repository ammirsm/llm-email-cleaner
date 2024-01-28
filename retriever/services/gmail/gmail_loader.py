__all__ = ["GmailLoader"]

# inspired by https://github.com/run-llama/llama-hub/tree/956aa44b6dfa3e085b9b9a80c3caec0144b1bbbf/llama_hub/gmail

import base64
import email
import json
from typing import Any, Dict, List, Optional, Tuple, Union

from core.settings import SCOPES
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import Resource, build
from llama_index.readers.base import BaseReader


class GmailLoader(BaseReader):
    def __init__(
        self,
        query: Optional[str] = None,
        results_per_page: Optional[int] = 10,
        use_iterative_parser: Optional[bool] = False,
        max_results: Optional[int] = 10,
        creds: Optional[Dict[str, Any]] = None,
        token: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the GmailReader with optional query parameters.

        :param query: The query string to filter emails.
        :param results_per_page: Number of results to return per page.
        :param use_iterative_parser: Flag to use the iterative parser for email bodies.
        :param max_results: Maximum number of results to fetch.
        """
        self.query = query
        self.results_per_page = results_per_page
        self.use_iterative_parser = use_iterative_parser
        self.max_results = max_results
        self.service = None
        self.creds_json = creds
        self.token = token

    def load_data(self) -> list[dict[str, Any]]:
        """
        Load emails from the user's Gmail account based on the specified query.

        :return: A list of Document objects representing the emails.
        """
        self.service = self.service or self._build_service()
        messages = self._search_messages()
        return messages

    def load_message_ids(self) -> list[dict[str, Any]]:
        """
        Load emails from the user's Gmail account based on the specified query.
        :return:
        """
        self.service = self.service or self._build_service()
        return self._search_messages_id()

    def load_full_data(self, message_id: str) -> dict[str, Any]:
        self.service = self.service or self._build_service()
        return self._get_message_data(message={"id": message_id})

    def get_token(self):
        credentials, token = self._get_credentials()
        return token

    def _build_service(self) -> Resource:
        """
        Build and return the Gmail API service resource.

        :return: The Gmail API service resource.
        """
        credentials, _ = self._get_credentials()
        return build("gmail", "v1", credentials=credentials)

    def _get_credentials(self) -> tuple[Credentials | None | Any, dict[str, Any] | Any]:
        """
        Retrieve user credentials from storage or initiate the authorization flow.

        :return: The obtained user credentials.
        """
        creds = None
        if self.token:
            creds = Credentials.from_authorized_user_info(self.token, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_config(self.creds_json, SCOPES)
                creds = flow.run_local_server(port=8080)

            self.token = json.loads(creds.to_json())

        return creds, self.token

    def _search_messages_id(self) -> List[Dict[str, Any]]:
        """
        Search for messages in the user's Gmail account based on the set query.

        :return: A list of message data dictionaries.
        """
        results = (
            self.service.users()
            .messages()
            .list(userId="me", q=self.query, maxResults=int(self.results_per_page))
            .execute()
        )

        messages = results.get("messages", [])
        self._paginate_messages(messages, results)

        return messages

    def _search_messages(self) -> List[Dict[str, Any]]:
        """
        Search for messages in the user's Gmail account based on the set query.

        :return: A list of message data dictionaries.
        """
        results = (
            self.service.users()
            .messages()
            .list(userId="me", q=self.query, maxResults=int(self.results_per_page))
            .execute()
        )

        messages = results.get("messages", [])
        self._paginate_messages(messages, results)

        return self._process_messages(messages)

    def _paginate_messages(self, messages: List[Dict[str, Any]], results: Dict[str, Any]) -> None:
        """
        Paginate through message search results and append them to the messages list.

        :param messages: The current list of messages.
        :param results: The current page of search results.
        """
        while "nextPageToken" in results and len(messages) < self.max_results:
            page_token = results["nextPageToken"]
            results = (
                self.service.users()
                .messages()
                .list(userId="me", q=self.query, pageToken=page_token, maxResults=int(self.results_per_page))
                .execute()
            )
            messages.extend(results.get("messages", []))

    def _process_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process and parse each message in the list of messages.

        :param messages: The list of messages to process.
        :return: A list of dictionaries with detailed message information.
        """
        result = []
        for message in messages:
            try:
                message_data = self._get_message_data(message)
                if message_data:
                    result.append(message_data)
            except Exception as e:
                raise Exception(f"Can't get message data: {e}")

        return result

    def _get_message_data(self, message: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """
        Retrieve and parse data for a single message.

        :param message: A dictionary representing a Gmail message.
        :return: A dictionary with the message's details, or None if unable to parse.
        """
        message_id = message["id"]
        message_data = self.service.users().messages().get(userId="me", id=message_id, format="raw").execute()

        parser = self._extract_message_body_iterative if self.use_iterative_parser else self._extract_message_body
        body, subject, sender, recipient, copy = parser(message_data)

        if not body:
            return None

        # https://developers.google.com/gmail/api/reference/rest/v1/users.messages
        return {
            "id": message_data.get("id", None),
            "threadId": message_data.get("threadId", None),
            "snippet": message_data.get("snippet", None),
            "internalDate": message_data.get("internalDate", None),
            "body": body,
            "labelIds": message_data.get("labelIds", None),
            "historyId": message_data.get("historyId", None),
            "subject": subject,
            "sender": sender,
            "recipient": recipient,
            "copy": copy,
        }

    def _remove_message_with_id(self, message_id: str) -> None:
        """
        Remove a message from the user's Gmail account.

        :param message_id: The ID of the message to remove.
        """
        self.service.users().messages().delete(userId="me", id=message_id).execute()

    def _extract_message_body_iterative(
        self, message: Dict[str, Any], is_top_level: bool = True
    ) -> Union[Dict[str, Any], str]:
        """
        Iteratively extract the body and other details from a message.

        :param message: The message to parse.
        :param is_top_level: Whether this is the top level of the message (controls parsing logic).
        :return: A dictionary with the email's details, or the body text if not top level.
        """
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
    def _extract_message_body(
        message: Dict[str, str]
    ) -> Tuple[str, Optional[str], Optional[str], Optional[str], Optional[str]]:
        """
        Extract the body and other details from a message.

        :param message: The message to parse.
        :return: A tuple containing the body, subject, sender, recipient, and copy of the message.
        """
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

            return body.decode("utf-8", errors="replace"), subject, sender, recipient, copy
        except Exception as e:
            raise Exception("Can't parse message body" + str(e))
