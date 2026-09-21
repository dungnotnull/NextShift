import pytest

from nextshift.domain.models import Channel, Pathway, TtmStage, Worker


def test_worker_defaults():
    w = Worker(worker_id="w-001", phone="+15550001111", name="Maria Silva",
               current_role="warehouse_associate", company_id="velocity")
    assert w.opted_in is False
    assert w.ttm_stage is TtmStage.PRECONTEMPLATION


def test_channel_enum_values():
    assert Channel.WHATSAPP.value == "whatsapp"
    assert Channel.SMS.value == "sms"
    assert Channel.RCS.value == "rcs"
    assert Channel.EMAIL.value == "email"


def test_worker_rejects_bad_phone():
    with pytest.raises(ValueError):
        Worker(worker_id="w-001", phone="555", name="X",
               current_role="r", company_id="velocity")


def test_pathway_completion_empty_lesson_ids():
    assert Pathway("pw", "w", "r", []).completion(["L1"]) == 0.0


def test_pathway_completion_partial_and_duplicates():
    p = Pathway("pw", "w", "r", ["L1", "L2", "L3"])
    assert p.completion(["L1", "L1", "L2"]) == 2 / 3


def test_phone_digit_boundaries():
    assert Worker(worker_id="w", phone="+" + "1" * 10, name="n",
                  current_role="r", company_id="c").phone == "+" + "1" * 10
    assert Worker(worker_id="w", phone="+" + "1" * 15, name="n",
                  current_role="r", company_id="c").phone == "+" + "1" * 15
    with pytest.raises(ValueError):
        Worker(worker_id="w", phone="+" + "1" * 16, name="n",
               current_role="r", company_id="c")
