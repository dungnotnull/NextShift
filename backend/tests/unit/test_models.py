import pytest

from nextshift.domain.models import Channel, TtmStage, Worker


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
