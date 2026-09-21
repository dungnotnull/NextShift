"""SMS and RCS share SendTextMessage; RCS is selected by passing an
RCS agent ARN as the origination identity (AWS End User Messaging)."""
from typing import Any

import boto3


class SmsRcsSender:
    def __init__(self, client: Any = None) -> None:
        self._client = client or boto3.client("pinpoint-sms-voice-v2")

    def send(self, to: str, body: str, origination: str) -> str:
        """origination: SMS pool/number id, or RCS agent ARN for rich delivery."""
        response = self._client.send_text_message(
            OriginationIdentity=origination,
            DestinationPhoneNumber=to,
            MessageBody=body,
        )
        return response["MessageId"]
