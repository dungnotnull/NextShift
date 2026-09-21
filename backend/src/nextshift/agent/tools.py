"""Agent tools (Strands @tool). Pure logic lives in domain modules."""
import uuid
from datetime import date

from strands import tool

from nextshift.agent.store import Store
from nextshift.domain.matching import match_score, skill_gap, transferable_skills
from nextshift.domain.profiling import score
from nextshift.domain.models import LessonProgress, Pathway
from nextshift.domain.scheduler import advance, due_lessons

STORE = Store()


@tool
def save_profile(worker_id: str, answers: list[int], skills: dict[str, int]) -> dict:
    """Persist the worker's intake results after the 10-question profile
    (items in order: concern x2, control x2, curiosity x2, confidence x2,
    anxiety x2, each 1-5) and their self-reported skills (name -> level 1-5).
    Stores tone and advances the stage to contemplation."""
    try:
        profile = score(answers)
    except ValueError as exc:
        return {"error": f"invalid profile answers: {exc}"}
    STORE.save_profile(worker_id=worker_id, skills=skills,
                       tone=profile.tone, ttm_stage="contemplation")
    return {"saved": True, "tone": profile.tone,
            "caas": profile.caas, "ai_anxiety": profile.ai_anxiety}


@tool
def match_role(worker_id: str, company_id: str = "") -> dict:
    """Rank internal role matches for the worker: transferable skills first,
    then gaps. Use this before suggesting any pathway."""
    worker = STORE.get_worker(worker_id)
    if worker is None:
        return {"error": "worker not found"}
    roles = STORE.list_roles(company_id or worker.company_id)
    results = []
    for role in roles:
        if role.affected:
            continue
        current = worker.skills or {}
        results.append({
            "role_id": role.role_id,
            "title": role.title,
            "match_score": round(match_score(current, role.required_skills), 2),
            "transferable_skills": transferable_skills(current, role.required_skills),
            "skill_gap": skill_gap(current, role.required_skills),
        })
    results.sort(key=lambda r: r["match_score"], reverse=True)
    return {"matches": results[:3]}


@tool
def get_progress(worker_id: str) -> dict:
    """Return the worker's pathway completion and lessons due today."""
    pathway = STORE.get_pathway(worker_id)
    if pathway is None:
        return {"enrolled": False}
    progress = STORE.list_progress(worker_id)
    done = [p.lesson_id for p in progress if p.correct_streak >= 1]
    return {
        "enrolled": True,
        "target_role_id": pathway.target_role_id,
        "completion": pathway.completion(done),
        "due_today": [p.lesson_id for p in due_lessons(progress, date.today())][:3],
    }


@tool
def next_lesson(worker_id: str) -> dict:
    """Fetch the next due lesson as a multiple-choice retrieval question."""
    lessons = STORE.load_lessons()
    progress = STORE.list_progress(worker_id)
    if not progress:
        pathway = STORE.get_pathway(worker_id)
        if pathway is None:
            return {"error": "no pathway enrolled"}
        first = pathway.lesson_ids[0]
        lesson = lessons.get(first, {})
        return {"lesson_id": first, "question": lesson.get("question"),
                "options": lesson.get("options")}
    due = due_lessons(progress, date.today())
    if not due:
        return {"done_for_today": True}
    lesson = lessons.get(due[0].lesson_id, {})
    return {"lesson_id": due[0].lesson_id, "question": lesson.get("question"),
            "options": lesson.get("options")}


@tool
def submit_answer(worker_id: str, lesson_id: str, answer_index: int) -> dict:
    """Grade an answer and schedule the next review (1/3/7 day spacing)."""
    lessons = STORE.load_lessons()
    lesson = lessons.get(lesson_id)
    if lesson is None:
        return {"error": "unknown lesson"}
    correct = answer_index == lesson["answer_index"]
    progress = STORE.list_progress(worker_id)
    existing = next((p for p in progress if p.lesson_id == lesson_id), None)
    base = existing or LessonProgress(lesson_id, lesson["skill"])
    updated = advance(base, correct, date.today())
    STORE.put_progress(worker_id, updated)
    return {"correct": correct, "explanation": lesson.get("explanation", ""),
            "correct_streak": updated.correct_streak}


@tool
def enroll_pathway(worker_id: str, target_role_id: str) -> dict:
    """Enroll the worker in a pathway toward an internal role (TTM: action)."""
    lessons = STORE.load_lessons()
    lesson_ids = [lid for lid, l in lessons.items() if target_role_id in l["role_ids"]]
    if not lesson_ids:
        return {"error": "no lessons for role"}
    STORE.save_pathway(Pathway(
        pathway_id=f"pw-{uuid.uuid4().hex[:8]}",
        worker_id=worker_id,
        target_role_id=target_role_id,
        lesson_ids=lesson_ids,
    ))
    STORE.set_ttm_stage(worker_id, "action")  # commitment made (TTM)
    return {"enrolled": True, "target_role_id": target_role_id,
            "lesson_count": len(lesson_ids)}


@tool
def escalate_human(worker_id: str, reason: str) -> dict:
    """Escalate to the human HR partner queue. Use for crisis or complaints."""
    STORE.put_event(worker_id, "escalation", reason)
    return {"escalated": True,
            "message": "Your HR partner will reach out within one business day."}
