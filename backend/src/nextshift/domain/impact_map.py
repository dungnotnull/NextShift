"""Parse the HR Automation Impact Map CSV into Worker records."""
import csv
import io

from nextshift.domain.models import Worker


def parse_impact_map(csv_text: str, company_id: str) -> list[Worker]:
    workers: list[Worker] = []
    for row in csv.DictReader(io.StringIO(csv_text)):
        try:
            workers.append(Worker(
                worker_id=row["worker_id"].strip(),
                phone=row["phone"].strip(),
                name=row["name"].strip(),
                current_role=row["current_role"].strip(),
                company_id=company_id,
            ))
        except ValueError:
            continue  # skip malformed rows (e.g. non E.164 phone)
    return workers
