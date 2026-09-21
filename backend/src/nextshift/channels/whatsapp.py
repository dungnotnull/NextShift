"""AWS End User Messaging Social (WhatsApp) sender.

Free-form messages are only allowed inside the 24h Meta conversation
window, tracked via a consent record created when the worker messages us.
Outside it we fall back to a pre-approved template (Meta policy).
"""
import json
from typing import Any

import boto3

DEFAULT_TEMPLATE = "nextshift_invite"
DEFAULT_LANG = "en_US"


class WhatsAppSender:
    def __init__(self, client: Any = None, phone_id: str = "",
                 template_name: str = DEFAULT_TEMPLATE,
                 template_lang: str = DEFAULT_LANG) -> None:
        self._client = client or boto3.client("socialmessaging")
        self._phone_id = phone_id
        self._template_name = template_name
        self._template_lang = template_lang

    def _send(self, message: dict[str, Any]) -> str:
        response = self._client.send_whatsapp_message(
            originationPhoneNumberId=self._phone_id,
            message=json.dumps(message).encode(),
            metaApiVersion="v20.0",
        )
        return response["messageId"]

    def send_text(self, consent: dict[str, Any] | None,
                  to: str, body: str) -> str:
        """Send free-form if consented, else the invite template."""
        if consent and consent.get("user_consents"):
            return self._send({
                "messaging_product": "whatsapp",
                "to": to,
                "type": "text",
                "text": {"body": body},
            })
        return self._send({
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": self._template_name,
                "language": {"code": self._template_lang},
            },
        })

    def send_interactive(self, consent: dict[str, Any] | None, to: str,
                         body: str, button_label: str) -> str:
        """Two-way prompt with a single tap button (nudge default, Thaler & Sunstein)."""
        if consent and consent.get("user_consents"):
            return self._send({
                "messaging_product": "whatsapp",
                "to": to,
                "type": "interactive",
                "interactive": {
                    "type": "button",
                    "body": {"text": body},
                    "action": {"buttons": [{
                        "type": "reply",
                        "reply": {"id": "nextshift_affirm", "title": button_label[:20]},
                    }]},
                },
            })
        return self.send_text(consent, to, body)
