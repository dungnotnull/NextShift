"""Core dataclasses shared across NextShift modules."""
from dataclasses import dataclass
from enum import Enum


class Channel(str, Enum):
    WHATSAPP = "whatsapp"
    SMS = "sms"
    RCS = "rcs"
    EMAIL = "email"


class TtmStage(str, Enum):
    """Transtheoretical Model stages (Prochaska & DiClemente, 1983)."""
    PRECONTEMPLATION = "precontemplation"
    CONTEMPLATION = "contemplation"
    PREPARATION = "preparation"
    ACTION = "action"


def _validate_e164(phone: str) -> str:
    if not (phone.startswith("+") and phone[1:].isdigit() and 10 <= len(phone[1:]) <= 15):
        raise ValueError(f"phone must be E.164, got: {phone}")
    return phone


@dataclass
class Worker:
    worker_id: str
    phone: str
    name: str
    current_role: str
    company_id: str
    opted_in: bool = False
    ttm_stage: TtmStage = TtmStage.PRECONTEMPLATION
    skills: dict[str, int] | None = None

    def __post_init__(self) -> None:
        _validate_e164(self.phone)


@dataclass
class RoleProfile:
    role_id: str
    title: str
    affected: bool                     # True = being automated
    required_skills: dict[str, int]    # skill -> required level 1-5


@dataclass
class Pathway:
    pathway_id: str
    worker_id: str
    target_role_id: str
    lesson_ids: list[str]

    def completion(self, done_lesson_ids: list[str]) -> float:
        if not self.lesson_ids:
            return 0.0
        done = set(done_lesson_ids) & set(self.lesson_ids)
        return len(done) / len(self.lesson_ids)


@dataclass
class Profiling:
    caas: dict[str, int]               # concern/control/curiosity/confidence, 1-5
    ai_anxiety: int                    # 1-5, AIAS job-replacement dimension
    tone: str                          # reassure | balanced | push


@dataclass
class LessonProgress:
    lesson_id: str
    skill: str
    correct_streak: int = 0
    due_date: str = ""                 # ISO date


@dataclass
class InboundMessage:
    channel: Channel
    phone: str
    text: str
    message_id: str
