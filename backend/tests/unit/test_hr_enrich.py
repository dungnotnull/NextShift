from nextshift.handlers.hr_api import enrich_workers


WORKERS = [
    {"worker_id": "w-001", "name": "Maria Silva", "ttm_stage": "action"},
    {"worker_id": "w-002", "name": "John Okafor", "ttm_stage": "precontemplation"},
]

PATHWAYS = [
    {"worker_id": "w-001", "pathway_id": "pw-1",
     "target_role_id": "robot_fleet_operator",
     "lesson_ids": ["L1", "L2", "L3"]},
]

PROGRESS = [
    {"worker_id": "w-001", "lesson_id": "L1", "correct_streak": 2},
    {"worker_id": "w-001", "lesson_id": "L2", "correct_streak": 1},
    {"worker_id": "w-001", "lesson_id": "L9", "correct_streak": 3},  # not in pathway
    {"worker_id": "w-001", "lesson_id": "L3", "correct_streak": 0},  # attempted, not done
]


def test_worker_with_pathway_gets_completion():
    rows = enrich_workers(WORKERS, PATHWAYS, PROGRESS)
    maria = rows[0]
    assert maria["target_role_id"] == "robot_fleet_operator"
    assert maria["pathway_size"] == 3
    assert maria["pathway_completion"] == round(2 / 3, 2)


def test_worker_without_pathway_gets_nulls():
    rows = enrich_workers(WORKERS, PATHWAYS, PROGRESS)
    john = rows[1]
    assert john["target_role_id"] is None
    assert john["pathway_completion"] is None
    assert john["pathway_size"] == 0


def test_decimal_streaks_are_coerced():
    from decimal import Decimal
    progress = [{"worker_id": "w-001", "lesson_id": "L1",
                 "correct_streak": Decimal(1)}]
    rows = enrich_workers(WORKERS, PATHWAYS, progress)
    assert rows[0]["pathway_completion"] == round(1 / 3, 2)


def test_empty_inputs_return_workers_with_nulls():
    rows = enrich_workers(WORKERS, [], [])
    assert len(rows) == 2
    assert all(r["pathway_completion"] is None for r in rows)
