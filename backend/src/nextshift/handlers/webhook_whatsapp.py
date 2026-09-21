"""Lambda: SNS subscription for inbound WhatsApp events.

Flow: parse -> mark consent -> look up worker -> invoke AgentCore
(with stable per-worker session) -> guardrail -> reply.
"""
import hashlib
import json
import os

import boto3
from boto3.dynamodb.conditions import Key

from nextshift.channels.inbound import parse_whatsapp_sns_event
from nextshift.channels.whatsapp import WhatsAppSender

agentcore = boto3.client("bedrock-agentcore")
dynamodb = boto3.resource("dynamodb")
consent_table = dynamodb.Table(os.environ.get("CONSENT_TABLE", "nextshift-consent"))
workers_table = dynamodb.Table(os.environ.get("WORKERS_TABLE", "nextshift-workers"))

AGENT_RUNTIME_ARN = os.environ.get("AGENT_RUNTIME_ARN", "")


def session_id_for(worker_id: str) -> str:
    """Stable per-worker session across channels (>= 33 chars per API)."""
    digest = hashlib.sha1(worker_id.encode()).hexdigest()
    return f"nextshift-{digest}"[:48].ljust(33, "0")


def _find_worker_by_phone(phone: str) -> dict | None:
    resp = workers_table.query(
        IndexName="phone-index",
        KeyConditionExpression=Key("phone").eq(phone))
    items = resp.get("Items", [])
    return items[0] if items else None


def handler(event, context):
    msg = parse_whatsapp_sns_event(event)
    if msg is None:
        return {"skipped": True}

    # Inbound user message opens the 24h window -> consent
    consent_table.put_item(Item={"phone": msg.phone, "user_consents": True})
    worker = _find_worker_by_phone(msg.phone)
    if worker is None or not AGENT_RUNTIME_ARN:
        WhatsAppSender(phone_id=os.environ.get("WA_PHONE_ID", "")).send_text(
            consent={"user_consents": True}, to=msg.phone,
            body="Thanks for reaching NextShift! Your HR team will enroll you shortly.")
        return {"ok": True}

    # Note: the installed botocore bedrock-agentcore model uses lowerCamelCase
    # member names (agentRuntimeArn, payload, runtimeSessionId); verified
    # against operation_model input_shape members.
    resp = agentcore.invoke_agent_runtime(
        agentRuntimeArn=AGENT_RUNTIME_ARN,
        payload=json.dumps({
            "prompt": msg.text,
            "worker_id": worker["worker_id"],
            "worker_name": worker.get("name", "friend"),
            "tone": worker.get("tone", "balanced"),
            "stage": worker.get("ttm_stage", "contemplation"),
        }).encode(),
        runtimeSessionId=session_id_for(worker["worker_id"]),
    )
    body = json.loads(resp["response"].read().decode())
    reply = body.get("reply", "")
    WhatsAppSender(phone_id=os.environ.get("WA_PHONE_ID", "")).send_text(
        consent={"user_consents": True}, to=msg.phone, body=reply)
    return {"ok": True, "reply": reply}
