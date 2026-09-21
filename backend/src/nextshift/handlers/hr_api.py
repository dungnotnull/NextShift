"""Lambda behind API Gateway: GET /workers, POST /impact-map, POST /invite."""
import json
import os

import boto3
from boto3.dynamodb.conditions import Attr

from nextshift.domain.impact_map import parse_impact_map

dynamodb = boto3.resource("dynamodb")
workers_table = dynamodb.Table(os.environ.get("WORKERS_TABLE", "nextshift-workers"))
lambda_client = boto3.client("lambda")
COMPANY_ID = os.environ.get("COMPANY_ID", "velocity")
INVITE_FUNCTION = os.environ.get("INVITE_FUNCTION", "nextshift-invite")


def handler(event, context):
    method = event.get("requestContext", {}).get("http", {}).get("method", "")
    path = event.get("rawPath", "")
    body = json.loads(event.get("body") or "{}")

    if path == "/workers" and method == "GET":
        resp = workers_table.scan(FilterExpression=Attr("company_id").eq(COMPANY_ID))
        return {"statusCode": 200, "body": json.dumps(resp.get("Items", []), default=str)}

    if path == "/impact-map" and method == "POST":
        workers, skipped = parse_impact_map(body.get("csv", ""), company_id=COMPANY_ID)
        with workers_table.batch_writer() as batch:
            for w in workers:
                batch.put_item(Item={
                    "worker_id": w.worker_id, "phone": w.phone, "name": w.name,
                    "current_role": w.current_role, "company_id": w.company_id,
                    "opted_in": False, "ttm_stage": "precontemplation",
                })
        return {"statusCode": 200,
                "body": json.dumps({"ingested": len(workers), "skipped": skipped})}

    if path == "/invite" and method == "POST":
        lambda_client.invoke(
            FunctionName=INVITE_FUNCTION,
            InvocationType="Event",
            Payload=json.dumps({
                "company_id": COMPANY_ID,
                "workers": body.get("workers", []),
            }).encode())
        return {"statusCode": 202, "body": json.dumps({"invite_queued": True})}

    return {"statusCode": 404, "body": json.dumps({"error": f"unknown route {method} {path}"})}
