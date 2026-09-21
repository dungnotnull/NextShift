"""Lambda behind API Gateway: GET /workers, POST /impact-map, POST /invite."""
import json
import os

import boto3
from boto3.dynamodb.conditions import Attr

from nextshift.domain.impact_map import parse_impact_map

dynamodb = boto3.resource("dynamodb")
workers_table = dynamodb.Table(os.environ.get("WORKERS_TABLE", "nextshift-workers"))
pathways_table = dynamodb.Table(os.environ.get("PATHWAYS_TABLE", "nextshift-pathways"))
progress_table = dynamodb.Table(os.environ.get("PROGRESS_TABLE", "nextshift-progress"))
lambda_client = boto3.client("lambda")
COMPANY_ID = os.environ.get("COMPANY_ID", "velocity")
INVITE_FUNCTION = os.environ.get("INVITE_FUNCTION", "nextshift-invite")


def enrich_workers(workers: list[dict], pathways: list[dict],
                   progress: list[dict]) -> list[dict]:
    """Attach pathway target and completion to each worker row.

    A lesson counts as done when correct_streak >= 1 (retrieval passed
    at least once); only lessons inside the worker's pathway count.
    """
    done_by_worker: dict[str, set[str]] = {}
    for p in progress:
        if int(p.get("correct_streak", 0)) >= 1:
            done_by_worker.setdefault(p["worker_id"], set()).add(p["lesson_id"])
    pathway_by_worker: dict[str, dict] = {}
    for pw in pathways:
        pathway_by_worker.setdefault(pw["worker_id"], pw)

    rows = []
    for w in workers:
        item = dict(w)
        pw = pathway_by_worker.get(w["worker_id"])
        if pw:
            lesson_ids = list(pw.get("lesson_ids", []))
            done = done_by_worker.get(w["worker_id"], set()) & set(lesson_ids)
            item["target_role_id"] = pw.get("target_role_id")
            item["pathway_size"] = len(lesson_ids)
            item["pathway_completion"] = (
                round(len(done) / len(lesson_ids), 2) if lesson_ids else 0.0)
        else:
            item["target_role_id"] = None
            item["pathway_completion"] = None
            item["pathway_size"] = 0
        rows.append(item)
    return rows


def handler(event, context):
    method = event.get("requestContext", {}).get("http", {}).get("method", "")
    path = event.get("rawPath", "")
    body = json.loads(event.get("body") or "{}")

    if path == "/workers" and method == "GET":
        resp = workers_table.scan(FilterExpression=Attr("company_id").eq(COMPANY_ID))
        workers = resp.get("Items", [])
        pathways = pathways_table.scan().get("Items", [])
        progress = progress_table.scan().get("Items", [])
        rows = enrich_workers(workers, pathways, progress)
        return {"statusCode": 200, "body": json.dumps(rows, default=str)}

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
                "company_name": os.environ.get("COMPANY_NAME", "Velocity Logistics"),
                "workers": body.get("workers", []),
            }).encode())
        return {"statusCode": 202, "body": json.dumps({"invite_queued": True})}

    return {"statusCode": 404, "body": json.dumps({"error": f"unknown route {method} {path}"})}
