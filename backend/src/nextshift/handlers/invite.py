"""Lambda: HR-triggered SMS invites (SMS is the no-app baseline channel).

Event shape: {"company_name": str, "workers": [{"worker_id", "phone", "name"}]}
"""
import os

from nextshift.channels.sms_rcs import SmsRcsSender

SMS_POOL_ID = os.environ.get("SMS_POOL_ID", "")

INVITE_TEMPLATE = (
    "Hi {name}, {company} is investing in new roles as automation grows. "
    "NextShift helps you get there, free, on your phone. Reply on WhatsApp "
    "to {wa_number} with 'START' or reply YES here."
)


def handler(event, context):
    sender = SmsRcsSender()
    results = []
    for w in event.get("workers", []):
        text = INVITE_TEMPLATE.format(
            name=w["name"].split()[0],
            company=event.get("company_name", "your company"),
            wa_number=os.environ.get("WA_DISPLAY_NUMBER", "our WhatsApp number"))
        results.append(sender.send(to=w["phone"], body=text,
                                   origination=SMS_POOL_ID))
    return {"invited": len(results), "message_ids": results}
