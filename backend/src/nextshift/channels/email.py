"""Amazon SES v2 sender for milestone transcripts and certificates."""
from typing import Any

import boto3


class EmailSender:
    def __init__(self, client: Any = None, from_address: str = "nextshift@example.com") -> None:
        self._client = client or boto3.client("sesv2")
        self._from = from_address

    def send(self, to: str, subject: str, html: str) -> str:
        response = self._client.send_email(
            FromEmailAddress=self._from,
            Destination={"ToAddresses": [to]},
            Content={
                "Simple": {
                    "Subject": {"Data": subject},
                    "Body": {"Html": {"Data": html}},
                }
            },
        )
        return response["MessageId"]
