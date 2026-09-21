from nextshift.domain.impact_map import parse_impact_map

CSV = """worker_id,name,phone,current_role
w-001,Maria Silva,+15550001111,warehouse_associate
w-002,John Okafor,+15550002222,inventory_clerk
"""


def test_parse_rows_to_workers():
    workers, skipped = parse_impact_map(CSV, company_id="velocity")
    assert len(workers) == 2
    assert workers[0].name == "Maria Silva"
    assert workers[0].company_id == "velocity"
    assert skipped == 0


def test_skips_malformed_rows_and_counts_them():
    csv = ("worker_id,name,phone,current_role\n"
           "w-001,Maria,555,bad\n"
           "w-002,John,+15550002222,ok\n"
           ",NoId,+15550003333,ok\n")
    workers, skipped = parse_impact_map(csv, company_id="velocity")
    assert [w.worker_id for w in workers] == ["w-002"]
    assert skipped == 2


def test_wrong_header_returns_empty():
    workers, skipped = parse_impact_map("a,b,c,d\n1,2,3,4", company_id="velocity")
    assert workers == []
    assert skipped == 0


def test_short_rows_are_skipped_not_crashing():
    csv = "worker_id,name,phone,current_role\nw-001\nw-002,John,+15550002222,ok\n"
    workers, skipped = parse_impact_map(csv, company_id="velocity")
    assert [w.worker_id for w in workers] == ["w-002"]
    assert skipped == 1
