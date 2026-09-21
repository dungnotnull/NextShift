"""Scoring for the 10-item intake questionnaire.

Items 1-8 map to the four CAAS adapt-abilities (Savickas & Porfeli, 2012);
items 9-10 map to the AIAS job-replacement anxiety dimension
(Wang & Wang, 2022). Likert scale 1-5 per item.
"""
from nextshift.domain.models import Profiling

DIMENSIONS = ["concern", "control", "curiosity", "confidence", "anxiety"]

ITEMS = [
    ("concern", "I have thought about how my job might change in the next few years."),
    ("concern", "I have a plan for my next career step."),
    ("control", "I believe my choices shape my career future."),
    ("control", "I take initiative at work instead of waiting to be told."),
    ("curiosity", "I like learning how new tools and machines work."),
    ("curiosity", "I explore what other roles exist inside my company."),
    ("confidence", "I believe I can learn the skills for a new role."),
    ("confidence", "I solve problems at work without giving up quickly."),
    ("anxiety", "I worry that machines or AI will take over my job."),
    ("anxiety", "When I hear about AI at work, I feel uneasy."),
]


def score(answers: list[int]) -> Profiling:
    if len(answers) != len(ITEMS):
        raise ValueError(f"expected {len(ITEMS)} answers, got {len(answers)}")
    dims: dict[str, list[int]] = {d: [] for d in DIMENSIONS}
    for (dim, _), ans in zip(ITEMS, answers, strict=True):
        dims[dim].append(ans)
    caas = {d: round(sum(v) / len(v)) for d, v in dims.items() if d != "anxiety"}
    anxiety = round(sum(dims["anxiety"]) / len(dims["anxiety"]))
    return Profiling(caas=caas, ai_anxiety=anxiety, tone=_tone(caas, anxiety))


def _tone(caas: dict[str, int], anxiety: int) -> str:
    if anxiety >= 4:
        return "reassure"
    if anxiety <= 2 and caas.get("confidence", 0) >= 4:
        return "push"
    return "balanced"
