import json

from nextshift.channels.inbound import parse_whatsapp_sns_event
from nextshift.domain.models import Channel


def _sns_body_with(meta_value: dict) -> dict:
    return {"Records": [{"Sns": {"Message": json.dumps({
        "version": "1.0",
        "whatsappBusinessAccountId": "waba-1",
        "whatsapp": meta_value,
    })}}]}


META_MESSAGE = {
    "entry": [{
        "changes": [{
            "value": {
                "messages": [{
                    "from": "+15550001111",
                    "id": "wamid.INBOUND1",
                    "type": "text",
                    "text": {"body": "yes, I'm in"},
                }],
                "contacts": [{"profile": {"name": "Maria"}}],
            },
        }],
    }],
}


def test_parses_text_message():
    msg = parse_whatsapp_sns_event(_sns_body_with(META_MESSAGE))
    assert msg.channel is Channel.WHATSAPP
    assert msg.phone == "+15550001111"
    assert msg.text == "yes, I'm in"
    assert msg.message_id == "wamid.INBOUND1"


def test_returns_none_for_status_events():
    body = _sns_body_with({"entry": [{"changes": [{"value": {"statuses": [
        {"id": "wamid.X", "status": "delivered"}]}}]}]})
    assert parse_whatsapp_sns_event(body) is None


INTERACTIVE_MESSAGE = {
    "entry": [{
        "changes": [{
            "value": {
                "messages": [{
                    "from": "+15550001111",
                    "id": "wamid.BUTTON1",
                    "type": "interactive",
                    "interactive": {"button_reply": {"id": "nextshift_affirm",
                                                     "title": "Yes, let's start"}},
                }],
            },
        }],
    }],
}


def test_parses_interactive_button_reply():
    msg = parse_whatsapp_sns_event(_sns_body_with(INTERACTIVE_MESSAGE))
    assert msg is not None
    assert msg.text == "Yes, let's start"
    assert msg.message_id == "wamid.BUTTON1"


def test_message_without_phone_returns_none():
    body = _sns_body_with({"entry": [{"changes": [{"value": {
        "messages": [{"from": "", "id": "w1", "type": "text",
                      "text": {"body": "hi"}}]}}]}]})
    assert parse_whatsapp_sns_event(body) is None
