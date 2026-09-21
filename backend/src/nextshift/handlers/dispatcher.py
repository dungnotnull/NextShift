"""Lambda: EventBridge daily run.

1. Send each enrolled worker their due lesson (WhatsApp if consented, SMS fallback).
2. On 100% pathway completion, send the SES milestone email + RCS/SMS card.
"""
import logging
import os
from datetime import date

import boto3

from nextshift.agent.store import Store
from nextshift.channels.email import EmailSender
from nextshift.channels.sms_rcs import SmsRcsSender
from nextshift.channels.whatsapp import WhatsAppSender
from nextshift.domain.scheduler import due_lessons

dynamodb = boto3.resource("dynamodb")
consent_table = dynamodb.Table(os.environ.get("CONSENT_TABLE", "nextshift-consent"))
store = Store(dynamodb=dynamodb)

CERT_TEMPLATE = """<h1>Congratulations, {name}!</h1>
<p>You completed the <b>{role}</b> learning pathway on NextShift.</p>
<p>Your verified transcript is attached to your profile. Tap below to apply:</p>
<p><a href="{apply_url}">Apply for the {role} role</a></p>
<p>Skills demonstrated: {skills}</p>
"""


def handler(event, context):
    sent, milestones = 0, 0
    workers = store.list_enrolled_workers()
    lessons = store.load_lessons()
    for worker in workers:
        try:
            progress = store.list_progress(worker.worker_id)
            pathway = store.get_pathway(worker.worker_id)
            if pathway is None:
                continue

            done = [p.lesson_id for p in progress if p.correct_streak >= 1]
            if pathway.completion(done) >= 1.0:
                if store.milestone_sent(worker.worker_id):
                    continue
                _send_milestone(worker, pathway)
                store.mark_milestone(worker.worker_id)
                milestones += 1
                continue

            consent = consent_table.get_item(Key={"phone": worker.phone}).get("Item")
            due = due_lessons(progress, date.today())
            if due:
                lesson = lessons.get(due[0].lesson_id, {})
                _deliver(worker, consent, lesson)
                sent += 1
            else:
                pending = [lid for lid in pathway.lesson_ids if lid not in done]
                if pending:
                    lesson = lessons.get(pending[0], {})
                    _deliver(worker, consent, lesson)
                    sent += 1
        except Exception:
            logging.exception("dispatcher failed for worker %s", worker.worker_id)
    return {"lessons_sent": sent, "milestones": milestones}


def _deliver(worker, consent, lesson) -> None:
    body = (f"Today's 2-minute lesson:\n{lesson.get('question', '')}\n"
            + "\n".join(f"{i+1}. {o}" for i, o in enumerate(lesson.get("options", [])))
            + "\n\nReply with the number of your answer.")
    if consent and consent.get("user_consents"):
        WhatsAppSender(phone_id=os.environ.get("WA_PHONE_ID", "")).send_text(
            consent=consent, to=worker.phone, body=body)
    else:
        SmsRcsSender().send(to=worker.phone, body=body,
                            origination=os.environ.get("SMS_POOL_ID", ""))


def _send_milestone(worker, pathway) -> None:
    roles = store.list_roles(worker.company_id)
    role = next((r for r in roles if r.role_id == pathway.target_role_id), None)
    title = role.title if role else pathway.target_role_id
    apply_url = os.environ.get("HR_APPLY_URL", "https://hr.velocity.example/apply")
    EmailSender(from_address=os.environ.get("SES_FROM", "")).send(
        to=f"{worker.worker_id}@workers.velocity-logistics.example",
        subject="Your NextShift certificate is ready",
        html=CERT_TEMPLATE.format(
            name=worker.name.split()[0], role=title,
            apply_url=apply_url,
            skills=", ".join(pathway.lesson_ids)))
    # RCS card (spec journey step 7): rich channel for the interview tap;
    # falls back to SMS pool when no RCS agent ARN is configured.
    SmsRcsSender().send(
        to=worker.phone,
        body=(f"Congratulations {worker.name.split()[0]}! You completed the {title} "
              f"pathway. Book your interview: {apply_url}"),
        origination=os.environ.get("RCS_AGENT_ARN") or os.environ.get("SMS_POOL_ID", ""))
