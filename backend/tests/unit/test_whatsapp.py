import json

from botocore.stub import Stubber

from nextshift.channels.whatsapp import WhatsAppSender


def _stub_ok(stubber: Stubber) -> None:
    stubber.add_response(
        "send_whatsapp_message",
        {"messageId": "wamid.TEST1"},
        expected_params={
            "originationPhoneNumberId": "wa-phone-123",
            "message": json.dumps({
                "messaging_product": "whatsapp",
                "to": "+15550001111",
                "type": "text",
                "text": {"body": "hello"},
            }).encode(),
            "metaApiVersion": "v20.0",
        },
    )


def test_send_text_freeform_when_consented():
    sender = WhatsAppSender(phone_id="wa-phone-123")
    with Stubber(sender._client) as stub:
        _stub_ok(stub)
        msg_id = sender.send_text(consent={"user_consents": True},
                                  to="+15550001111", body="hello")
        stub.assert_no_pending_responses()
    assert msg_id == "wamid.TEST1"


def test_send_text_template_when_no_consent():
    sender = WhatsAppSender(phone_id="wa-phone-123", template_name="nextshift_invite",
                            template_lang="en_US")
    expected_message = {
        "messaging_product": "whatsapp",
        "to": "+15550001111",
        "type": "template",
        "template": {"name": "nextshift_invite", "language": {"code": "en_US"}},
    }
    with Stubber(sender._client) as stub:
        stub.add_response(
            "send_whatsapp_message",
            {"messageId": "wamid.TPL1"},
            expected_params={
                "originationPhoneNumberId": "wa-phone-123",
                "message": json.dumps(expected_message).encode(),
                "metaApiVersion": "v20.0",
            },
        )
        msg_id = sender.send_text(consent=None, to="+15550001111", body="ignored outside window")
        stub.assert_no_pending_responses()
    assert msg_id == "wamid.TPL1"
