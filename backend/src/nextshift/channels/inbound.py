"""Parse inbound EUM Social SNS events into InboundMessage.

Event shape: SNS record Message is JSON containing an AWS event header
plus the Meta webhook payload. We search for the first `messages` array
so the parser tolerates header variations.
"""
import json
from typing import Any

from nextshift.domain.models import Channel, InboundMessage


def _find_messages(node: Any) -> list[dict] | None:
    if isinstance(node, dict):
        if isinstance(node.get("messages"), list) and node["messages"]:
            return node["messages"]
        for value in node.values():
            found = _find_messages(value)
            if found:
                return found
    elif isinstance(node, list):
        for item in node:
            found = _find_messages(item)
            if found:
                return found
    return None


def parse_whatsapp_sns_event(event: dict) -> InboundMessage | None:
    try:
        body = json.loads(event["Records"][0]["Sns"]["Message"])
    except (KeyError, IndexError, json.JSONDecodeError):
        return None
    messages = _find_messages(body)
    if not messages:
        return None  # status/delivery event, not an inbound user message
    m = messages[0]
    if m.get("type") == "interactive":
        reply = m.get("interactive") or {}
        button = reply.get("button_reply") or {}
        phone = m.get("from", "")
        if not phone:
            return None
        return InboundMessage(
            channel=Channel.WHATSAPP,
            phone=phone,
            text=button.get("title", ""),
            message_id=m.get("id", ""),
        )
    if m.get("type") != "text":
        return None
    phone = m.get("from", "")
    if not phone:
        return None
    text = (m.get("text") or {}).get("body", "")
    return InboundMessage(
        channel=Channel.WHATSAPP,
        phone=phone,
        text=text,
        message_id=m.get("id", ""),
    )
