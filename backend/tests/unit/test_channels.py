from botocore.stub import Stubber

from nextshift.channels.sms_rcs import SmsRcsSender
from nextshift.channels.email import EmailSender


def test_sms_send_uses_origination_identity():
    s = SmsRcsSender()
    with Stubber(s._client) as stub:
        stub.add_response(
            "send_text_message",
            {"MessageId": "sms-1"},
            expected_params={
                "OriginationIdentity": "pool-abc",
                "DestinationPhoneNumber": "+15550001111",
                "MessageBody": "Your invite",
            },
        )
        assert s.send(to="+15550001111", body="Your invite",
                      origination="pool-abc") == "sms-1"
        stub.assert_no_pending_responses()


def test_email_send_ses_v2():
    e = EmailSender()
    with Stubber(e._client) as stub:
        stub.add_response(
            "send_email",
            {"MessageId": "ses-1"},
            expected_params={
                "FromEmailAddress": "nextshift@example.com",
                "Destination": {"ToAddresses": ["maria@example.com"]},
                "Content": {
                    "Simple": {
                        "Subject": {"Data": "Your NextShift certificate"},
                        "Body": {"Html": {"Data": "<h1>Congratulations</h1>"}},
                    }
                },
            },
        )
        assert e.send(to="maria@example.com",
                      subject="Your NextShift certificate",
                      html="<h1>Congratulations</h1>") == "ses-1"
        stub.assert_no_pending_responses()
