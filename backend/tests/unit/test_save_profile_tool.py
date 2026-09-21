import pytest

from nextshift.agent import tools


class FakeStore:
    def __init__(self):
        self.saved = None

    def save_profile(self, worker_id, skills, tone, ttm_stage):
        self.saved = (worker_id, skills, tone, ttm_stage)


def test_save_profile_scores_and_persists(monkeypatch):
    fake = FakeStore()
    monkeypatch.setattr(tools, "STORE", fake)
    result = tools.save_profile._tool_func(
        worker_id="w-001",
        answers=[3, 3, 3, 3, 3, 3, 3, 3, 5, 5],
        skills={"scanning": 4})
    assert result["saved"] is True
    assert result["tone"] == "reassure"          # anxiety 5 -> reassure
    assert fake.saved == ("w-001", {"scanning": 4}, "reassure", "contemplation")


def test_save_profile_rejects_bad_answers(monkeypatch):
    fake = FakeStore()
    monkeypatch.setattr(tools, "STORE", fake)
    result = tools.save_profile._tool_func(worker_id="w-001", answers=[3] * 9, skills={})
    assert "error" in result
    assert fake.saved is None
