from nextshift.domain.impact_map import parse_impact_map

CSV = """worker_id,name,phone,current_role
w-001,Maria Silva,+15550001111,warehouse_associate
w-002,John Okafor,+15550002222,inventory_clerk
"""


def test_parse_rows_to_workers():
    workers = parse_impact_map(CSV, company_id="velocity")
    assert len(workers) == 2
    assert workers[0].name == "Maria Silva"
    assert workers[0].company_id == "velocity"


def test_skips_malformed_rows():
    csv = "worker_id,name,phone,current_role\nw-001,Maria,555,bad\nw-002,John,+15550002222,ok\n"
    workers = parse_impact_map(csv, company_id="velocity")
    assert [w.worker_id for w in workers] == ["w-002"]
