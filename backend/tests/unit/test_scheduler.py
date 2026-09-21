from datetime import date

from nextshift.domain.scheduler import advance, due_lessons
from nextshift.domain.models import LessonProgress


def test_correct_answer_advances_spacing():
    p = LessonProgress(lesson_id="L1", skill="robot_monitoring", correct_streak=0)
    nxt = advance(p, correct=True, today=date(2026, 10, 1))
    assert nxt.correct_streak == 1
    assert nxt.due_date == "2026-10-02"          # +1 day


def test_spacing_grows_1_3_7():
    p = LessonProgress(lesson_id="L1", skill="s", correct_streak=2)
    nxt = advance(p, correct=True, today=date(2026, 10, 1))
    assert nxt.due_date == "2026-10-08"          # index capped at 7


def test_wrong_answer_resets_to_next_day():
    p = LessonProgress(lesson_id="L1", skill="s", correct_streak=3, due_date="2026-10-01")
    nxt = advance(p, correct=False, today=date(2026, 10, 1))
    assert nxt.correct_streak == 0
    assert nxt.due_date == "2026-10-02"


def test_due_lessons_sorted_oldest_first():
    items = [
        LessonProgress("L2", "s", 1, "2026-10-01"),
        LessonProgress("L1", "s", 1, "2026-09-28"),
        LessonProgress("L3", "s", 1, "2026-10-03"),
    ]
    assert [p.lesson_id for p in due_lessons(items, today=date(2026, 10, 2))] == ["L1", "L2"]


def test_empty_due_date_never_due():
    assert due_lessons([LessonProgress("L9", "s", 0, "")], today=date(2026, 10, 2)) == []
