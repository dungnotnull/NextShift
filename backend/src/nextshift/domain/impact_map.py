"""Parse the HR Automation Impact Map CSV into Worker records.

Returns (workers, skipped_count) so the HR API can surface how many
rows were rejected (bad phone, missing fields, wrong header).
"""
import csv
import io

from nextshift.domain.models import Worker

REQUIRED_COLUMNS = {"worker_id", "name", "phone", "current_role"}


def _clean(row: dict, field: str) -> str:
    value = row.get(field)
    return value.strip() if isinstance(value, str) else ""


def parse_impact_map(csv_text: str, company_id: str) -> tuple[list[Worker], int]:
    workers: list[Worker] = []
    skipped = 0
    reader = csv.DictReader(io.StringIO(csv_text))
    if not REQUIRED_COLUMNS <= set(reader.fieldnames or []):
        return [], 0  # wrong header: nothing ingested, nothing counted as skipped rows
    for row in reader:
        try:
            worker = Worker(
                worker_id=_clean(row, "worker_id"),
                phone=_clean(row, "phone"),
                name=_clean(row, "name"),
                current_role=_clean(row, "current_role"),
                company_id=company_id,
            )
            if not worker.worker_id or not worker.name:
                raise ValueError("missing required field value")
            workers.append(worker)
        except ValueError:
            skipped += 1
    return workers, skipped
