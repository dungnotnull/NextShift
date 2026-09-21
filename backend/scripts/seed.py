"""Load seed data into DynamoDB. Run: python scripts/seed.py"""
import json
import os
import sys
from pathlib import Path

import boto3

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nextshift.domain.impact_map import parse_impact_map  # noqa: E402

SEED_DIR = Path(__file__).parent.parent / "seed"


def main() -> None:
    dynamodb = boto3.resource("dynamodb")
    workers = dynamodb.Table(os.environ.get("WORKERS_TABLE", "nextshift-workers"))
    roles = dynamodb.Table(os.environ.get("ROLES_TABLE", "nextshift-roles"))

    csv_text = (SEED_DIR / "impact_map.csv").read_text(encoding="utf-8")
    data = json.loads((SEED_DIR / "roles.json").read_text(encoding="utf-8"))
    lessons = json.loads((SEED_DIR / "lessons.json").read_text(encoding="utf-8"))

    seeded, skipped = parse_impact_map(csv_text, company_id=data["company_id"])
    for w in seeded:
        workers.put_item(Item={
            "worker_id": w.worker_id, "phone": w.phone, "name": w.name,
            "current_role": w.current_role, "company_id": w.company_id,
            "opted_in": False, "ttm_stage": "precontemplation",
            "skills": data["worker_skills"].get(w.worker_id, {}),
        })
    for r in data["roles"]:
        roles.put_item(Item={
            "role_id": r["role_id"], "company_id": data["company_id"],
            "title": r["title"], "affected": r["affected"],
            "required_skills": r["required_skills"],
        })
    roles.put_item(Item={
        "role_id": "LESSONS", "company_id": "GLOBAL",
        "payload": json.dumps(lessons),
    })
    print(f"Seed complete: {len(seeded)} workers ({skipped} skipped), "
          f"{len(data['roles'])} roles, {len(lessons)} lessons.")


if __name__ == "__main__":
    main()
