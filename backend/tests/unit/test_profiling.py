import pytest

from nextshift.domain.profiling import score, ITEMS, DIMENSIONS


def test_ten_items_defined():
    assert len(ITEMS) == 10
    assert DIMENSIONS == ["concern", "control", "curiosity", "confidence", "anxiety"]


def test_score_averages_two_items_per_dimension():
    # items ordered: concern x2, control x2, curiosity x2, confidence x2, anxiety x2
    answers = [5, 5, 3, 3, 2, 2, 4, 4, 1, 1]
    p = score(answers)
    assert p.caas == {"concern": 5, "control": 3, "curiosity": 2, "confidence": 4}
    assert p.ai_anxiety == 1


def test_high_anxiety_gets_reassure_tone():
    p = score([3, 3, 3, 3, 3, 3, 3, 3, 5, 5])
    assert p.tone == "reassure"


def test_confident_low_anxiety_gets_push_tone():
    p = score([4, 4, 4, 4, 4, 4, 5, 5, 1, 1])
    assert p.tone == "push"


def test_middle_gets_balanced():
    p = score([3] * 10)
    assert p.tone == "balanced"


def test_rejects_wrong_answer_count():
    with pytest.raises(ValueError):
        score([3] * 9)


def test_rejects_out_of_range_answers():
    with pytest.raises(ValueError):
        score([0] * 10)
    with pytest.raises(ValueError):
        score([6] * 10)
