from nextshift.domain.matching import match_score, skill_gap, transferable_skills

CURRENT = {"wms_software": 3, "safety_protocols": 4, "scanning": 4}
TARGET = {"wms_software": 3, "safety_protocols": 4, "robot_monitoring": 3}


def test_transferable_skills_meet_or_exceed():
    assert transferable_skills(CURRENT, TARGET) == ["safety_protocols", "wms_software"]


def test_skill_gap_only_reports_missing():
    gap = skill_gap(CURRENT, TARGET)
    assert gap == {"robot_monitoring": 3}


def test_match_score_fraction_of_requirements_met():
    assert match_score(CURRENT, TARGET) == 2 / 3


def test_match_score_empty_target_is_zero():
    assert match_score({}, {}) == 0.0


def test_extra_current_skills_ignored():
    assert skill_gap({"scanning": 5}, {"wms": 2}) == {"wms": 2}
    assert match_score({"scanning": 5}, {"wms": 2}) == 0.0
    assert transferable_skills({"scanning": 5}, {"wms": 2}) == []
