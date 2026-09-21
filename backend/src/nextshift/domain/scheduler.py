"""Spaced repetition scheduler (Cepeda et al., 2006: 1/3/7 day intervals)."""
from datetime import date, timedelta

from nextshift.domain.models import LessonProgress

SPACING_DAYS = [1, 3, 7]


def advance(p: LessonProgress, correct: bool, today: date) -> LessonProgress:
    if not correct:
        return LessonProgress(p.lesson_id, p.skill, 0, (today + timedelta(days=1)).isoformat())
    idx = min(p.correct_streak, len(SPACING_DAYS) - 1)
    return LessonProgress(p.lesson_id, p.skill, p.correct_streak + 1,
                          (today + timedelta(days=SPACING_DAYS[idx])).isoformat())


def due_lessons(items: list[LessonProgress], today: date) -> list[LessonProgress]:
    due = [p for p in items if p.due_date and date.fromisoformat(p.due_date) <= today]
    return sorted(due, key=lambda p: p.due_date)
