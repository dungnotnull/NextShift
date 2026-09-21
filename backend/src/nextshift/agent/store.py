"""DynamoDB data access for the agent tools. Thin by design."""
import json
import os
import time

import boto3
from boto3.dynamodb.conditions import Key

from nextshift.domain.models import LessonProgress, Pathway, RoleProfile, Worker


class Store:
    def __init__(self, dynamodb=None) -> None:
        self._dynamodb = dynamodb or boto3.resource("dynamodb")
        self._tables = {
            "workers": self._dynamodb.Table(os.environ.get("WORKERS_TABLE", "nextshift-workers")),
            "pathways": self._dynamodb.Table(os.environ.get("PATHWAYS_TABLE", "nextshift-pathways")),
            "progress": self._dynamodb.Table(os.environ.get("PROGRESS_TABLE", "nextshift-progress")),
            "roles": self._dynamodb.Table(os.environ.get("ROLES_TABLE", "nextshift-roles")),
        }

    def get_worker(self, worker_id: str) -> Worker | None:
        item = self._tables["workers"].get_item(Key={"worker_id": worker_id}).get("Item")
        if not item:
            return None
        try:
            return Worker(
                worker_id=item["worker_id"],
                phone=item["phone"],
                name=item.get("name", ""),
                current_role=item.get("current_role", ""),
                company_id=item.get("company_id", ""),
                opted_in=bool(item.get("opted_in", False)),
                ttm_stage=item.get("ttm_stage", "precontemplation"),
                skills={k: int(v) for k, v in (item.get("skills") or {}).items()},
            )
        except (KeyError, ValueError):
            return None  # corrupt record (e.g. bad phone) — treat as missing

    def list_roles(self, company_id: str) -> list[RoleProfile]:
        resp = self._tables["roles"].query(
            IndexName="company-index",
            KeyConditionExpression=Key("company_id").eq(company_id))
        return [RoleProfile(
            role_id=i["role_id"], title=i["title"], affected=i.get("affected", False),
            required_skills={k: int(v) for k, v in i.get("required_skills", {}).items()},
        ) for i in resp.get("Items", [])]

    def save_pathway(self, p: Pathway) -> None:
        self._tables["pathways"].put_item(Item={
            "pathway_id": p.pathway_id, "worker_id": p.worker_id,
            "target_role_id": p.target_role_id, "lesson_ids": p.lesson_ids,
        })

    def get_pathway(self, worker_id: str) -> Pathway | None:
        resp = self._tables["pathways"].query(
            KeyConditionExpression=Key("worker_id").eq(worker_id))
        items = resp.get("Items", [])
        if not items:
            return None
        i = items[0]
        return Pathway(pathway_id=i["pathway_id"], worker_id=i["worker_id"],
                       target_role_id=i["target_role_id"], lesson_ids=i["lesson_ids"])

    def list_progress(self, worker_id: str) -> list[LessonProgress]:
        resp = self._tables["progress"].query(
            KeyConditionExpression=Key("worker_id").eq(worker_id))
        return [LessonProgress(i["lesson_id"], i["skill"],
                               int(i.get("correct_streak", 0)), i.get("due_date", ""))
                for i in resp.get("Items", [])]

    def put_progress(self, worker_id: str, p: LessonProgress) -> None:
        self._tables["progress"].put_item(Item={
            "worker_id": worker_id, "lesson_id": p.lesson_id, "skill": p.skill,
            "correct_streak": p.correct_streak, "due_date": p.due_date,
        })

    def put_event(self, worker_id: str, type_: str, detail: str) -> None:
        events = self._dynamodb.Table(os.environ.get("EVENTS_TABLE", "nextshift-events"))
        events.put_item(Item={
            "worker_id": worker_id, "ts": str(time.time()),
            "type": type_, "detail": detail,
            "expiration_date": int(time.time()) + 365 * 86400,
        })

    def load_lessons(self) -> dict:
        """Lessons are a static bundle stored in the roles table as JSON."""
        item = self._tables["roles"].get_item(Key={"role_id": "LESSONS",
                                                   "company_id": "GLOBAL"}).get("Item")
        payload = item.get("payload") if item else None
        return json.loads(payload) if payload else {}

    def list_enrolled_workers(self) -> list:
        """Workers having a pathway (demo scale: scan pathway table)."""
        resp = self._tables["pathways"].scan(ProjectionExpression="worker_id")
        ids = [i["worker_id"] for i in resp.get("Items", [])]
        workers = []
        for wid in ids:
            w = self.get_worker(wid)
            if w:
                workers.append(w)
        return workers
