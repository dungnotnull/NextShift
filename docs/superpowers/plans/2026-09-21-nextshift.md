# NextShift Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build NextShift — an agentic AI career companion that converts AI-displacement risk into internal advancement for frontline workers, delivered over WhatsApp (primary), SMS/RCS, and email, per the spec at `docs/superpowers/specs/2026-09-21-nextshift-design.md`.

**Architecture:** Serverless event-driven system on AWS. Inbound WhatsApp events flow EUM Social -> SNS -> Lambda, which invokes a Bedrock AgentCore Runtime agent (Strands SDK) whose per-worker `runtimeSessionId` gives cross-channel continuity. Pure-Python domain logic (matching, scheduling, profiling, guardrails) is TDD'ed with zero AWS dependency. CDK provisions DynamoDB, SNS, EventBridge, API Gateway, and Lambda. A Next.js HR dashboard manages the fictional company's Automation Impact Map.

**Tech Stack:** Python 3.12 (pytest, boto3, strands-agents, bedrock-agentcore SDK), AWS CDK (Python), Next.js 14 (TypeScript), DynamoDB, Amazon SES v2, AWS EUM Social (`socialmessaging` client), AWS EUM SMS/RCS (`pinpoint-sms-voice-v2` client), Bedrock AgentCore (Runtime + Memory).

**Verified API facts (do not re-guess):**

- WhatsApp send: `boto3.client('socialmessaging').send_whatsapp_message(originationPhoneNumberId=<phone_id>, message=<meta_json_bytes>, metaApiVersion='v20.0')` returns `messageId`. Message body is Meta Cloud API JSON (`{"messaging_product": "whatsapp", "to": "+1...", "type": "text", "text": {"body": "..."}}`). Template messages required outside the 24h window.
- SMS/RCS send: `boto3.client('pinpoint-sms-voice-v2').send_text_message(originationIdentity=<pool_id_or_rcs_agent_arn>, destinationPhoneNumber=..., messageBody=...)`.
- Agent invoke: `boto3.client('bedrock-agentcore').invoke_agent_runtime(agentRuntimeArn=..., payload=..., runtimeSessionId=...)` — VERIFIED during Task 11: the bedrock-agentcore botocore model uses lowerCamelCase member names (unlike pinpoint-sms-voice-v2 which is PascalCase). runtimeSessionId must be >= 33 chars. Always check a service's member-name style with `client.meta.service_model.operation_model(...).input_shape.members` before writing boto3 kwargs.
- AgentCore SDK: `pip install bedrock-agentcore` -> `from bedrock_agentcore import BedrockAgentCoreApp`; `@app.entrypoint`; deploy with starter toolkit CLI (`pip install "bedrock-agentcore[cli]"` -> `agentcore deploy`).
- AgentCore Memory: `MemoryClient().create_memory_and_wait(name, strategies=[...])`; `MemorySessionManager(memory_id, region).create_memory_session(actor_id, session_id)`; `session.add_turns([ConversationalMessage(text, MessageRole.USER)])`; `session.search_long_term_memories(query, namespace_path, top_k)`.

**Conventions:**

- All commands run from repo root (`D:\awscdspartnerHackathon`), bash syntax.
- Test command: `python -m pytest <path> -v`. Working Python: `backend/.venv`.
- Commit after every green test run. Conventional commits (`feat:`, `test:`, `chore:`, `docs:`).
- Git note: user deferred `git init` to execution time — Task 0 does it.

---

## File Structure (locked)

```
backend/
  pyproject.toml
  src/nextshift/
    domain/models.py          # dataclasses: Worker, RoleProfile, Pathway, Profiling, LessonProgress, InboundMessage
    domain/matching.py        # skill gap / transferable / match score
    domain/scheduler.py       # spaced repetition + due lessons
    domain/profiling.py       # CAAS/AIAS scoring -> tone
    domain/guardrails.py      # forbidden claims + crisis escalation
    domain/impact_map.py      # CSV -> workers + roles
    channels/whatsapp.py      # EUM Social sender (consent + template fallback)
    channels/sms_rcs.py       # pinpoint-sms-voice-v2 sender (SMS pool or RCS agent ARN)
    channels/email.py         # SES v2 sender
    channels/inbound.py       # SNS event -> InboundMessage parser
    handlers/webhook_whatsapp.py  # Lambda: SNS inbound -> agent -> reply
    handlers/invite.py        # Lambda: HR-triggered SMS invites
    handlers/dispatcher.py    # Lambda: daily lessons + milestones
    handlers/hr_api.py        # Lambda: GET /workers, POST /impact-map
    agent/entrypoint.py       # AgentCore Runtime entrypoint (Strands)
    agent/tools.py            # 5 agent tools
    agent/prompts.py          # system prompt (SDT/TTM/growth mindset)
    agent/memory.py           # Memory bootstrap + wrappers
  tests/unit/                 # one test file per domain/channel module
  scripts/create_memory.py    # one-time AgentCore Memory creation
  scripts/seed.py             # load seed data into DynamoDB
  seed/impact_map.csv
  seed/roles.json
  seed/lessons.json
infra/
  app.py
  requirements.txt
  nextshift/stack_core.py     # tables, SNS, SES
  nextshift/stack_messaging.py# lambdas, EventBridge, API Gateway
frontend/
  package.json
  tsconfig.json
  next.config.js
  src/app/page.tsx            # HR dashboard single page
  src/lib/api.ts
docs/superpowers/specs/2026-09-21-nextshift-design.md
docs/superpowers/plans/2026-09-21-nextshift.md   # this file
```

---

### Task 0: Bootstrap repo + Python project

**Files:**
- Create: `.gitignore`, `backend/pyproject.toml`, `backend/src/nextshift/__init__.py`, `backend/tests/__init__.py`, `backend/tests/unit/__init__.py`

- [ ] **Step 1: Initialize git**

Note: deferred until now per user instruction; required for all later commit steps.

```bash
cd /d/awscdspartnerHackathon && git init
```

Expected: `Initialized empty Git repository`

- [ ] **Step 2: Create .gitignore**

`.gitignore`:

```
__pycache__/
*.pyc
.venv/
node_modules/
.next/
dist/
cdk.out/
.env
*.whl
.DS_Store
```

- [ ] **Step 3: Create pyproject.toml**

`backend/pyproject.toml`:

```toml
[project]
name = "nextshift"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "boto3>=1.35",
    "strands-agents>=0.2",
    "bedrock-agentcore>=0.1",
]

[project.optional-dependencies]
dev = ["pytest>=8", "pytest-cov"]

[build-system]
requires = ["setuptools>=69"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["src"]
```

- [ ] **Step 4: Create package skeleton + smoke test**

Create empty `backend/src/nextshift/__init__.py`, `backend/tests/__init__.py`, `backend/tests/unit/__init__.py`.

`backend/tests/unit/test_smoke.py`:

```python
def test_package_imports():
    import nextshift  # noqa: F401
```

- [ ] **Step 5: Create venv, install, run smoke test**

```bash
cd backend && python -m venv .venv && source .venv/Scripts/activate && pip install -e ".[dev]" && python -m pytest tests/unit/test_smoke.py -v
```

Expected: `1 passed`

- [ ] **Step 6: Commit**

```bash
cd /d/awscdspartnerHackathon && git add .gitignore backend && git commit -m "chore: bootstrap python project skeleton"
```

---

### Task 1: Domain models

**Files:**
- Create: `backend/src/nextshift/domain/__init__.py`, `backend/src/nextshift/domain/models.py`
- Test: `backend/tests/unit/test_models.py`

- [ ] **Step 1: Write the failing test**

`backend/tests/unit/test_models.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && source .venv/Scripts/activate && python -m pytest tests/unit/test_models.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'nextshift.domain'`

- [ ] **Step 3: Write minimal implementation**

`backend/src/nextshift/domain/__init__.py` — empty file.

`backend/src/nextshift/domain/models.py`:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m pytest tests/unit/test_models.py -v
```

Expected: `3 passed`

- [ ] **Step 5: Commit**

```bash
cd /d/awscdspartnerHackathon && git add backend && git commit -m "feat: domain models with E.164 validation and TTM stages"
```

---

### Task 2: Skill-gap matching engine

Research applied: Arntz et al. (2016) task-level decomposition — surface transferable skills first, gaps second (growth-mindset framing per Dweck, 2006).

**Files:**
- Create: `backend/src/nextshift/domain/matching.py`
- Test: `backend/tests/unit/test_matching.py`

- [ ] **Step 1: Write the failing test**

`backend/tests/unit/test_matching.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/unit/test_matching.py -v
```

Expected: FAIL — `No module named 'nextshift.domain.matching'`

- [ ] **Step 3: Write minimal implementation**

`backend/src/nextshift/domain/matching.py`:

```python
"""Skill matching per task-level decomposition (Arntz et al., 2016, OECD)."""


def transferable_skills(current: dict[str, int], target: dict[str, int]) -> list[str]:
    """Skills that already meet or exceed the target requirement."""
    return sorted(s for s in target if current.get(s, 0) >= target[s])


def skill_gap(current: dict[str, int], target: dict[str, int]) -> dict[str, int]:
    """Missing skill levels keyed by skill name."""
    return {s: req - current.get(s, 0) for s, req in target.items()
            if req > current.get(s, 0)}


def match_score(current: dict[str, int], target: dict[str, int]) -> float:
    """Fraction of target skill requirements already met (0.0-1.0)."""
    if not target:
        return 0.0
    met = sum(1 for s in target if current.get(s, 0) >= target[s])
    return met / len(target)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m pytest tests/unit/test_matching.py -v
```

Expected: `4 passed`

- [ ] **Step 5: Commit**

```bash
git add backend && git commit -m "feat: skill-gap matching engine"
```

---

### Task 3: Spaced-repetition scheduler

Research applied: Cepeda et al. (2006) spacing intervals 1/3/7 days; Roediger & Karpicke (2006) retrieval-first; Dunlosky et al. (2013) high-utility techniques only.

**Files:**
- Create: `backend/src/nextshift/domain/scheduler.py`
- Test: `backend/tests/unit/test_scheduler.py`

- [ ] **Step 1: Write the failing test**

`backend/tests/unit/test_scheduler.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/unit/test_scheduler.py -v
```

Expected: FAIL — `No module named 'nextshift.domain.scheduler'`

- [ ] **Step 3: Write minimal implementation**

`backend/src/nextshift/domain/scheduler.py`:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m pytest tests/unit/test_scheduler.py -v
```

Expected: `4 passed`

- [ ] **Step 5: Commit**

```bash
git add backend && git commit -m "feat: spaced-repetition scheduler with 1/3/7 day intervals"
```

---

### Task 4: Profiling scorer (CAAS + AIAS)

Research applied: Savickas & Porfeli (2012) four adapt-abilities; Wang & Wang (2022) job-replacement anxiety dimension predicts motivated learning; tone adapts per Self-Determination Theory (Deci & Ryan, 2000).

**Files:**
- Create: `backend/src/nextshift/domain/profiling.py`
- Test: `backend/tests/unit/test_profiling.py`

- [ ] **Step 1: Write the failing test**

`backend/tests/unit/test_profiling.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/unit/test_profiling.py -v
```

Expected: FAIL — `No module named 'nextshift.domain.profiling'`

- [ ] **Step 3: Write minimal implementation**

`backend/src/nextshift/domain/profiling.py`:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m pytest tests/unit/test_profiling.py -v
```

Expected: `6 passed`

- [ ] **Step 5: Commit**

```bash
git add backend && git commit -m "feat: CAAS+AIAS 10-item profiling with tone selection"
```

---

### Task 5: Guardrails

Research applied: Bai et al. (2022) Constitutional AI — explicit written constitution checked mechanically; population is emotionally vulnerable.

**Files:**
- Create: `backend/src/nextshift/domain/guardrails.py`
- Test: `backend/tests/unit/test_guardrails.py`

- [ ] **Step 1: Write the failing test**

`backend/tests/unit/test_guardrails.py`:

```python
from nextshift.domain.guardrails import check_output, SAFE_FALLBACK


def test_clean_output_passes():
    r = check_output("Your next lesson on safety protocols is ready.")
    assert r.allowed and not r.escalation


def test_job_guarantee_is_blocked():
    r = check_output("Complete this course and I guarantee you the job.")
    assert not r.allowed
    assert r.claims_found


def test_crisis_keyword_escalates():
    r = check_output("I want to end my life.")
    assert r.escalation


def test_safe_fallback_is_never_blocked():
    r = check_output(SAFE_FALLBACK)
    assert r.allowed and not r.escalation
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/unit/test_guardrails.py -v
```

Expected: FAIL — `No module named 'nextshift.domain.guardrails'`

- [ ] **Step 3: Write minimal implementation**

`backend/src/nextshift/domain/guardrails.py`:

```python
"""Output constitution for a vulnerable population (Bai et al., 2022)."""
from dataclasses import dataclass, field

FORBIDDEN_CLAIMS = [
    "guarantee you the job",
    "guaranteed job",
    "promise you a position",
    "you will definitely be hired",
    "you will definitely get the job",
]

CRISIS_KEYWORDS = [
    "end my life",
    "kill myself",
    "suicide",
    "want to die",
    "can't go on",
    "hurt myself",
]

SAFE_FALLBACK = (
    "I want to be careful here: I can support your learning journey, "
    "but I can't make promises about hiring. If you're feeling overwhelmed, "
    "you can talk to your HR partner anytime. Shall we continue with your lesson?"
)


@dataclass
class GuardrailResult:
    allowed: bool = True
    escalation: bool = False
    claims_found: list[str] = field(default_factory=list)


def check_output(text: str) -> GuardrailResult:
    lowered = text.lower()
    claims = [c for c in FORBIDDEN_CLAIMS if c in lowered]
    crisis = any(k in lowered for k in CRISIS_KEYWORDS)
    return GuardrailResult(
        allowed=not claims,
        escalation=crisis,
        claims_found=claims,
    )
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m pytest tests/unit/test_guardrails.py -v
```

Expected: `4 passed`

- [ ] **Step 5: Commit**

```bash
git add backend && git commit -m "feat: output guardrails with crisis escalation"
```

---

### Task 6: WhatsApp channel adapter

Research applied: Castleman & Page (2015) — messaging channel efficacy for vulnerable populations. AWS pattern from aws-samples/sample-rest-frontend-for-end-user-messaging (consent table + 24h window + template fallback).

**Files:**
- Create: `backend/src/nextshift/channels/__init__.py`, `backend/src/nextshift/channels/whatsapp.py`
- Test: `backend/tests/unit/test_whatsapp.py`

- [ ] **Step 1: Write the failing test**

`backend/tests/unit/test_whatsapp.py`:

```python
import json

from botocore.stub import Stubber

from nextshift.channels.whatsapp import WhatsAppSender


def _stub_ok(stubber: Stubber) -> None:
    stubber.add_response(
        "send_whatsapp_message",
        {"messageId": "wamid.TEST1"},
        expected_params={
            "originationPhoneNumberId": "wa-phone-123",
            "message": json.dumps({
                "messaging_product": "whatsapp",
                "to": "+15550001111",
                "type": "text",
                "text": {"body": "hello"},
            }).encode(),
            "metaApiVersion": "v20.0",
        },
    )


def test_send_text_freeform_when_consented():
    sender = WhatsAppSender(phone_id="wa-phone-123")
    with Stubber(sender._client) as stub:
        _stub_ok(stub)
        msg_id = sender.send_text(consent={"user_consents": True},
                                  to="+15550001111", body="hello")
        stub.assert_no_pending_responses()
    assert msg_id == "wamid.TEST1"


def test_send_text_template_when_no_consent():
    sender = WhatsAppSender(phone_id="wa-phone-123", template_name="nextshift_invite",
                            template_lang="en_US")
    expected_message = {
        "messaging_product": "whatsapp",
        "to": "+15550001111",
        "type": "template",
        "template": {"name": "nextshift_invite", "language": {"code": "en_US"}},
    }
    with Stubber(sender._client) as stub:
        stub.add_response(
            "send_whatsapp_message",
            {"messageId": "wamid.TPL1"},
            expected_params={
                "originationPhoneNumberId": "wa-phone-123",
                "message": json.dumps(expected_message).encode(),
                "metaApiVersion": "v20.0",
            },
        )
        msg_id = sender.send_text(consent=None, to="+15550001111", body="ignored outside window")
        stub.assert_no_pending_responses()
    assert msg_id == "wamid.TPL1"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/unit/test_whatsapp.py -v
```

Expected: FAIL — `No module named 'nextshift.channels'`

- [ ] **Step 3: Write minimal implementation**

`backend/src/nextshift/channels/__init__.py` — empty file.

`backend/src/nextshift/channels/whatsapp.py`:

```python
"""AWS End User Messaging Social (WhatsApp) sender.

Free-form messages are only allowed inside the 24h Meta conversation
window, tracked via a consent record created when the worker messages us.
Outside it we fall back to a pre-approved template (Meta policy).
"""
import json
from typing import Any

import boto3

DEFAULT_TEMPLATE = "nextshift_invite"
DEFAULT_LANG = "en_US"


class WhatsAppSender:
    def __init__(self, client: Any = None, phone_id: str = "",
                 template_name: str = DEFAULT_TEMPLATE,
                 template_lang: str = DEFAULT_LANG) -> None:
        self._client = client or boto3.client("socialmessaging")
        self._phone_id = phone_id
        self._template_name = template_name
        self._template_lang = template_lang

    def _send(self, message: dict[str, Any]) -> str:
        response = self._client.send_whatsapp_message(
            originationPhoneNumberId=self._phone_id,
            message=json.dumps(message).encode(),
            metaApiVersion="v20.0",
        )
        return response["messageId"]

    def send_text(self, consent: dict[str, Any] | None,
                  to: str, body: str) -> str:
        """Send free-form if consented, else the invite template."""
        if consent and consent.get("user_consents"):
            return self._send({
                "messaging_product": "whatsapp",
                "to": to,
                "type": "text",
                "text": {"body": body},
            })
        return self._send({
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": self._template_name,
                "language": {"code": self._template_lang},
            },
        })

    def send_interactive(self, consent: dict[str, Any] | None, to: str,
                         body: str, button_label: str) -> str:
        """Two-way prompt with a single tap button (nudge default, Thaler & Sunstein)."""
        if consent and consent.get("user_consents"):
            return self._send({
                "messaging_product": "whatsapp",
                "to": to,
                "type": "interactive",
                "interactive": {
                    "type": "button",
                    "body": {"text": body},
                    "action": {"buttons": [{
                        "type": "reply",
                        "reply": {"id": "nextshift_affirm", "title": button_label[:20]},
                    }]},
                },
            })
        return self.send_text(consent, to, body)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m pytest tests/unit/test_whatsapp.py -v
```

Expected: `2 passed`

- [ ] **Step 5: Commit**

```bash
git add backend && git commit -m "feat: WhatsApp sender with consent and template fallback"
```

---

### Task 7: SMS/RCS + email adapters

**Files:**
- Create: `backend/src/nextshift/channels/sms_rcs.py`, `backend/src/nextshift/channels/email.py`
- Test: `backend/tests/unit/test_channels.py`

- [ ] **Step 1: Write the failing test**

`backend/tests/unit/test_channels.py`:

```python
from botocore.stub import Stubber

from nextshift.channels.sms_rcs import SmsRcsSender
from nextshift.channels.email import EmailSender


def test_sms_send_uses_origination_identity():
    s = SmsRcsSender()
    with Stubber(s._client) as stub:
        stub.add_response(
            "send_text_message",
            {"messageId": "sms-1"},
            expected_params={
                "originationIdentity": "pool-abc",
                "destinationPhoneNumber": "+15550001111",
                "messageBody": "Your invite",
            },
        )
        assert s.send(to="+15550001111", body="Your invite",
                      origination="pool-abc") == "sms-1"
        stub.assert_no_pending_responses()


def test_email_send_ses_v2():
    e = EmailSender()
    with Stubber(e._client) as stub:
        stub.add_response(
            "send_email",
            {"MessageId": "ses-1"},
            expected_params={
                "FromEmailAddress": "nextshift@example.com",
                "Destination": {"ToAddresses": ["maria@example.com"]},
                "Content": {
                    "Simple": {
                        "Subject": {"Data": "Your NextShift certificate"},
                        "Body": {"Html": {"Data": "<h1>Congratulations</h1>"}},
                    }
                },
            },
        )
        assert e.send(to="maria@example.com",
                      subject="Your NextShift certificate",
                      html="<h1>Congratulations</h1>") == "ses-1"
        stub.assert_no_pending_responses()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/unit/test_channels.py -v
```

Expected: FAIL — `No module named 'nextshift.channels.sms_rcs'`

- [ ] **Step 3: Write minimal implementation**

`backend/src/nextshift/channels/sms_rcs.py`:

```python
"""SMS and RCS share SendTextMessage; RCS is selected by passing an
RCS agent ARN as the origination identity (AWS End User Messaging).

NOTE: boto3 requires PascalCase (or snake_case) kwargs here — camelCase
like originationIdentity raises ParamValidationError. Response key is
PascalCase MessageId (discovered during Task 7 execution).
"""
from typing import Any

import boto3


class SmsRcsSender:
    def __init__(self, client: Any = None) -> None:
        self._client = client or boto3.client("pinpoint-sms-voice-v2")

    def send(self, to: str, body: str, origination: str) -> str:
        """origination: SMS pool/number id, or RCS agent ARN for rich delivery."""
        response = self._client.send_text_message(
            OriginationIdentity=origination,
            DestinationPhoneNumber=to,
            MessageBody=body,
        )
        return response["MessageId"]
```

`backend/src/nextshift/channels/email.py`:

```python
"""Amazon SES v2 sender for milestone transcripts and certificates."""
from typing import Any

import boto3


class EmailSender:
    def __init__(self, client: Any = None, from_address: str = "nextshift@example.com") -> None:
        self._client = client or boto3.client("sesv2")
        self._from = from_address

    def send(self, to: str, subject: str, html: str) -> str:
        response = self._client.send_email(
            FromEmailAddress=self._from,
            Destination={"ToAddresses": [to]},
            Content={
                "Simple": {
                    "Subject": {"Data": subject},
                    "Body": {"Html": {"Data": html}},
                }
            },
        )
        return response["MessageId"]
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m pytest tests/unit/test_channels.py -v
```

Expected: `2 passed`

- [ ] **Step 5: Commit**

```bash
git add backend && git commit -m "feat: SMS/RCS and SES email senders"
```

---

### Task 8: Inbound event parser (WhatsApp SNS -> InboundMessage)

The EUM Social event = AWS event header + Meta webhook JSON, delivered to SNS. Exact header nesting can vary; the parser locates the Meta `messages` array defensively and must be validated against a captured real event (Step 5).

**Files:**
- Create: `backend/src/nextshift/channels/inbound.py`
- Test: `backend/tests/unit/test_inbound.py`

- [ ] **Step 1: Write the failing test**

`backend/tests/unit/test_inbound.py`:

```python
from nextshift.channels.inbound import parse_whatsapp_sns_event
from nextshift.domain.models import Channel


def _sns_body_with(meta_value: dict) -> dict:
    return {"Records": [{"Sns": {"Message": __import__("json").dumps({
        "version": "1.0",
        "whatsappBusinessAccountId": "waba-1",
        "whatsapp": meta_value,
    })}}]}


META_MESSAGE = {
    "entry": [{
        "changes": [{
            "value": {
                "messages": [{
                    "from": "+15550001111",
                    "id": "wamid.INBOUND1",
                    "type": "text",
                    "text": {"body": "yes, I'm in"},
                }],
                "contacts": [{"profile": {"name": "Maria"}}],
            },
        }],
    }],
}


def test_parses_text_message():
    msg = parse_whatsapp_sns_event(_sns_body_with(META_MESSAGE))
    assert msg.channel is Channel.WHATSAPP
    assert msg.phone == "+15550001111"
    assert msg.text == "yes, I'm in"
    assert msg.message_id == "wamid.INBOUND1"


def test_returns_none_for_status_events():
    body = _sns_body_with({"entry": [{"changes": [{"value": {"statuses": [
        {"id": "wamid.X", "status": "delivered"}]}}]}]})
    assert parse_whatsapp_sns_event(body) is None
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/unit/test_inbound.py -v
```

Expected: FAIL — `No module named 'nextshift.channels.inbound'`

- [ ] **Step 3: Write minimal implementation**

`backend/src/nextshift/channels/inbound.py`:

```python
"""Parse inbound EUM Social SNS events into InboundMessage.

Event shape: SNS record Message is JSON containing an AWS event header
plus the Meta webhook payload. We search for the first `messages` array
so the parser tolerates header variations.
"""
import json
from typing import Any

from nextshift.domain.models import Channel, InboundMessage


def _find_messages(node: Any) -> list[dict] | None:
    if isinstance(node, dict):
        if isinstance(node.get("messages"), list) and node["messages"]:
            return node["messages"]
        for value in node.values():
            found = _find_messages(value)
            if found:
                return found
    elif isinstance(node, list):
        for item in node:
            found = _find_messages(item)
            if found:
                return found
    return None


def parse_whatsapp_sns_event(event: dict) -> InboundMessage | None:
    try:
        body = json.loads(event["Records"][0]["Sns"]["Message"])
    except (KeyError, IndexError, json.JSONDecodeError):
        return None
    messages = _find_messages(body)
    if not messages:
        return None  # status/delivery event, not an inbound user message
    m = messages[0]
    if m.get("type") != "text":
        return None
    return InboundMessage(
        channel=Channel.WHATSAPP,
        phone=m.get("from", ""),
        text=m.get("text", {}).get("body", ""),
        message_id=m.get("id", ""),
    )
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m pytest tests/unit/test_inbound.py -v
```

Expected: `2 passed`

- [ ] **Step 5: Validate against a real event (manual, once WABA test number is live)**

Send a WhatsApp message to the test number, capture the SNS topic's delivered notification from CloudWatch, and confirm `_find_messages` locates it. If the real shape differs (e.g. Meta payload is base64 or nested differently), update the fixture in this test file to the real shape and adjust the parser. Do not skip — this is the one external contract we could not fully pre-verify.

- [ ] **Step 6: Commit**

```bash
git add backend && git commit -m "feat: defensive inbound WhatsApp event parser"
```

---

### Task 9: Impact-map CSV parser

**Files:**
- Create: `backend/src/nextshift/domain/impact_map.py`
- Test: `backend/tests/unit/test_impact_map.py`

- [ ] **Step 1: Write the failing test**

`backend/tests/unit/test_impact_map.py`:

```python
from nextshift.domain.impact_map import parse_impact_map

CSV = """worker_id,name,phone,current_role
w-001,Maria Silva,+15550001111,warehouse_associate
w-002,John Okafor,+15550002222,inventory_clerk
"""


def test_parse_rows_to_workers():
    workers = parse_impact_map(CSV, company_id="velocity")
    assert len(workers) == 2
    assert workers[0].name == "Maria Silva"
    assert workers[0].company_id == "velocity"


def test_skips_malformed_rows():
    csv = "worker_id,name,phone,current_role\nw-001,Maria,555,bad\nw-002,John,+15550002222,ok\n"
    workers = parse_impact_map(csv, company_id="velocity")
    assert [w.worker_id for w in workers] == ["w-002"]
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/unit/test_impact_map.py -v
```

Expected: FAIL — `No module named 'nextshift.domain.impact_map'`

- [ ] **Step 3: Write minimal implementation**

`backend/src/nextshift/domain/impact_map.py`:

```python
"""Parse the HR Automation Impact Map CSV into Worker records."""
import csv
import io

from nextshift.domain.models import Worker


def parse_impact_map(csv_text: str, company_id: str) -> list[Worker]:
    workers: list[Worker] = []
    for row in csv.DictReader(io.StringIO(csv_text)):
        try:
            workers.append(Worker(
                worker_id=row["worker_id"].strip(),
                phone=row["phone"].strip(),
                name=row["name"].strip(),
                current_role=row["current_role"].strip(),
                company_id=company_id,
            ))
        except ValueError:
            continue  # skip malformed rows (e.g. non E.164 phone)
    return workers
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m pytest tests/unit/test_impact_map.py -v
```

Expected: `2 passed`

- [ ] **Step 5: Commit**

```bash
git add backend && git commit -m "feat: impact map CSV parser"
```

---

### Task 10: Agent tools + prompts + entrypoint

**Files:**
- Create: `backend/src/nextshift/agent/__init__.py`, `backend/src/nextshift/agent/store.py`, `backend/src/nextshift/agent/tools.py`, `backend/src/nextshift/agent/prompts.py`, `backend/src/nextshift/agent/entrypoint.py`, `backend/src/nextshift/agent/memory.py`
- Test: `backend/tests/unit/test_prompts.py`

Design: `store.py` is a thin DynamoDB data-access layer (no unit tests; covered by integration smoke in Task 14). Tools use pure domain logic from Tasks 2-3, so they are testable via a fake store injected through environment-agnostic defaults. Prompts embed the behavioral design rules.

- [ ] **Step 1: Write the failing test (prompt constitution)**

`backend/tests/unit/test_prompts.py`:

```python
from nextshift.agent.prompts import build_system_prompt


def test_prompt_includes_research_rules():
    p = build_system_prompt(worker_name="Maria", tone="reassure", stage="contemplation")
    for rule in ["never promise", "growth", "autonomy", "Maria", "reassure", "contemplation"]:
        assert rule.lower() in p.lower()


def test_prompt_lists_tools():
    p = build_system_prompt(worker_name="A", tone="balanced", stage="action")
    for tool_name in ["match_role", "get_progress", "next_lesson", "enroll_pathway",
                      "escalate_human"]:
        assert tool_name in p
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/unit/test_prompts.py -v
```

Expected: FAIL — `No module named 'nextshift.agent'`

- [ ] **Step 3: Write store.py**

`backend/src/nextshift/agent/__init__.py` — empty.

`backend/src/nextshift/agent/store.py`:

```python
"""DynamoDB data access for the agent tools. Thin by design."""
import json
import os
from datetime import date

import boto3
from boto3.dynamodb.conditions import Key

from nextshift.domain.models import LessonProgress, Pathway, RoleProfile, Worker


class Store:
    def __init__(self, dynamodb=None) -> None:
        self._dynamodb = dynamodb or boto3.resource("dynamodb")
        self._tables = {
            "workers": self._dynamodb.Table(os.environ.get("WORKERS_TABLE", "nextshift-workers")),
            "pathways": self._dynamodb.Table(os.environ.get("PATHWAYS_TABLE", "nextshift-pathways")),
            "progress": self._dynamodb.Table(os.environ.get("PROGRESS_TABLE", "nextshift-progress")),
            "roles": self._dynamodb.Table(os.environ.get("ROLES_TABLE", "nextshift-roles")),
        }

    def get_worker(self, worker_id: str) -> Worker | None:
        item = self._tables["workers"].get_item(Key={"worker_id": worker_id}).get("Item")
        if not item:
            return None
        item["skills"] = {k: int(v) for k, v in (item.get("skills") or {}).items()}
        return Worker(**{k: item[k] for k in
                         ("worker_id", "phone", "name", "current_role", "company_id",
                          "opted_in", "ttm_stage", "skills")})

    def list_roles(self, company_id: str) -> list[RoleProfile]:
        resp = self._tables["roles"].query(
            IndexName="company-index",
            KeyConditionExpression=Key("company_id").eq(company_id))
        return [RoleProfile(
            role_id=i["role_id"], title=i["title"], affected=i.get("affected", False),
            required_skills={k: int(v) for k, v in i.get("required_skills", {}).items()},
        ) for i in resp.get("Items", [])]

    def save_pathway(self, p: Pathway) -> None:
        self._tables["pathways"].put_item(Item={
            "pathway_id": p.pathway_id, "worker_id": p.worker_id,
            "target_role_id": p.target_role_id, "lesson_ids": p.lesson_ids,
        })

    def get_pathway(self, worker_id: str) -> Pathway | None:
        resp = self._tables["pathways"].query(
            KeyConditionExpression=Key("worker_id").eq(worker_id))
        items = resp.get("Items", [])
        if not items:
            return None
        i = items[0]
        return Pathway(pathway_id=i["pathway_id"], worker_id=i["worker_id"],
                       target_role_id=i["target_role_id"], lesson_ids=i["lesson_ids"])

    def list_progress(self, worker_id: str) -> list[LessonProgress]:
        resp = self._tables["progress"].query(
            KeyConditionExpression=Key("worker_id").eq(worker_id))
        return [LessonProgress(i["lesson_id"], i["skill"],
                               int(i.get("correct_streak", 0)), i.get("due_date", ""))
                for i in resp.get("Items", [])]

    def put_progress(self, worker_id: str, p: LessonProgress) -> None:
        self._tables["progress"].put_item(Item={
            "worker_id": worker_id, "lesson_id": p.lesson_id, "skill": p.skill,
            "correct_streak": p.correct_streak, "due_date": p.due_date,
        })

    def load_lessons(self) -> dict:
        """Lessons are a static bundle uploaded to the roles table as JSON."""
        item = self._tables["roles"].get_item(Key={"role_id": "LESSONS",
                                                   "company_id": "GLOBAL"}).get("Item")
        return json.loads(item["payload"]) if item else {}
```

- [ ] **Step 4: Write tools.py**

`backend/src/nextshift/agent/tools.py`:

```python
"""Agent tools (Strands @tool). Pure logic lives in domain modules."""
import os
import uuid
from datetime import date

from strands import tool

from nextshift.agent.store import Store
from nextshift.domain.matching import match_score, skill_gap, transferable_skills
from nextshift.domain.models import LessonProgress, Pathway, TtmStage
from nextshift.domain.scheduler import due_lessons

STORE = Store()


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
        lesson = lessons[first]
        return {"lesson_id": first, **_public(lesson)}
    due = due_lessons(progress, date.today())
    if not due:
        return {"done_for_today": True}
    lesson = lessons.get(due[0].lesson_id, {})
    return {"lesson_id": due[0].lesson_id, **_public(lesson)}


def _public(lesson: dict) -> dict:
    return {"question": lesson.get("question"),
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
    from nextshift.domain.scheduler import advance
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
    return {"enrolled": True, "target_role_id": target_role_id,
            "lesson_count": len(lesson_ids)}


@tool
def escalate_human(worker_id: str, reason: str) -> dict:
    """Escalate to the human HR partner queue. Use for crisis or complaints."""
    STORE.put_event(worker_id, "escalation", reason)
    return {"escalated": True,
            "message": "Your HR partner will reach out within one business day."}
```

Add `put_event` to `Store`:

```python
    def put_event(self, worker_id: str, type_: str, detail: str) -> None:
        import time
        self._tables["workers"].table  # no-op to keep client warm
        events = self._dynamodb.Table(os.environ.get("EVENTS_TABLE", "nextshift-events"))
        events.put_item(Item={
            "worker_id": worker_id, "ts": str(time.time()),
            "type": type_, "detail": detail,
        })
```

- [ ] **Step 5: Write prompts.py (make the test pass)**

`backend/src/nextshift/agent/prompts.py`:

```python
"""System prompt embeds the behavioral research rules (see spec section 5B/5C)."""
SYSTEM_TEMPLATE = """You are NextShift, a career companion for {worker_name}.
Current tone: {tone}. Worker stage of change: {stage}.

RULES (never break):
1. NEVER promise employment, promotions, or interview outcomes. Never give legal or financial advice.
2. GROWTH framing: skills are buildable. Never say the worker "lacks" something; say what they are "ready to build next".
3. AUTONOMY: always offer choices; the worker decides. CONFIDENCE: acknowledge progress concretely.
4. If {tone} is "reassure": slow down, validate worry first, one small step only.
   If "push": offer stretch goals and faster pacing.
5. If the worker expresses self-harm or crisis: call escalate_human immediately.
6. Keep replies under 80 words, mobile-friendly, one question at a time.

TOOLS: match_role, get_progress, next_lesson, submit_answer, enroll_pathway, escalate_human.
"""


def build_system_prompt(worker_name: str, tone: str, stage: str) -> str:
    return SYSTEM_TEMPLATE.format(worker_name=worker_name, tone=tone, stage=stage)
```

- [ ] **Step 6: Run prompt test to verify it passes**

```bash
python -m pytest tests/unit/test_prompts.py -v
```

Expected: `2 passed`

- [ ] **Step 7: Write memory.py + entrypoint.py**

`backend/src/nextshift/agent/memory.py`:

```python
"""AgentCore Memory bootstrap. MEMORY_ID is created once by scripts/create_memory.py."""
import os

from bedrock_agentcore.memory import MemorySessionManager
from bedrock_agentcore.memory.constants import ConversationalMessage, MessageRole

MEMORY_ID = os.environ.get("MEMORY_ID", "")


def get_session(worker_id: str) -> MemorySessionManager | None:
    if not MEMORY_ID:
        return None
    manager = MemorySessionManager(memory_id=MEMORY_ID,
                                   region_name=os.environ.get("AWS_REGION", "us-east-1"))
    try:
        manager.create_memory_session(actor_id=worker_id,
                                      session_id=f"nextshift-{worker_id}-session-0000001")
    except Exception:
        pass  # session already exists from a previous turn — reuse it
    return manager


def record_turn(session: MemorySessionManager | None, user_text: str,
                agent_text: str) -> None:
    if session is None:
        return
    session.add_turns([
        ConversationalMessage(user_text, MessageRole.USER),
        ConversationalMessage(agent_text, MessageRole.ASSISTANT),
    ])


def recall(session: MemorySessionManager | None, query: str, actor_id: str) -> list:
    if session is None:
        return []
    return session.search_long_term_memories(
        query=query, namespace_path=f"/facts/{actor_id}/", top_k=5)
```

`backend/src/nextshift/agent/entrypoint.py`:

```python
"""Bedrock AgentCore Runtime entrypoint.

Payload (from webhook Lambda): {"prompt": str, "worker_id": str,
"tone": str, "stage": str}. Response: {"reply": str}.
"""
import json
import os

from bedrock_agentcore import BedrockAgentCoreApp
from strands import Agent

from nextshift.agent import memory as agent_memory
from nextshift.agent import tools as nextshift_tools
from nextshift.agent.prompts import build_system_prompt
from nextshift.domain.guardrails import SAFE_FALLBACK, check_output

app = BedrockAgentCoreApp()

MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "us.amazon.nova-lite-v1:0")

AGENT_TOOLS = [
    nextshift_tools.match_role,
    nextshift_tools.get_progress,
    nextshift_tools.next_lesson,
    nextshift_tools.submit_answer,
    nextshift_tools.enroll_pathway,
    nextshift_tools.escalate_human,
]


@app.entrypoint
async def handler(request: dict):
    prompt = request.get("prompt")
    worker_id = request.get("worker_id", "unknown")
    if not isinstance(prompt, str) or not prompt:
        raise ValueError("prompt must be a non-empty string")

    session = agent_memory.get_session(worker_id)
    memories = agent_memory.recall(session, prompt, worker_id)
    memory_lines = "\n".join(str(m) for m in memories[:5])

    system = build_system_prompt(
        worker_name=request.get("worker_name", "friend"),
        tone=request.get("tone", "balanced"),
        stage=request.get("stage", "contemplation"),
    )
    if memory_lines:
        system += f"\nREMEMBERED FACTS:\n{memory_lines}\n"

    agent = Agent(model=MODEL_ID, tools=AGENT_TOOLS, system_prompt=system)  # strands 1.56 kwarg is system_prompt
    result = agent(prompt)  # strands Agent is callable and returns the final message
    reply = str(result)

    guard = check_output(reply)
    if guard.escalation:
        reply = ("I hear you, and you are not alone. I have alerted your HR partner "
                 "who will reach out. If you are in immediate danger, please call "
                 "or text 988 (Suicide & Crisis Lifeline, US).")
    elif not guard.allowed:
        reply = SAFE_FALLBACK

    agent_memory.record_turn(session, prompt, reply)
    yield json.dumps({"reply": reply})


app.run()
```

- [ ] **Step 8: Run full unit suite**

```bash
python -m pytest tests/unit -v
```

Expected: all passed (20 tests total so far)

- [ ] **Step 9: Commit**

```bash
git add backend && git commit -m "feat: agent tools, prompts, memory, AgentCore entrypoint"
```

---

### Task 11: Lambda handlers (webhook, invite, dispatcher, hr_api)

**Files:**
- Create: `backend/src/nextshift/handlers/__init__.py`, `backend/src/nextshift/handlers/webhook_whatsapp.py`, `backend/src/nextshift/handlers/invite.py`, `backend/src/nextshift/handlers/dispatcher.py`, `backend/src/nextshift/handlers/hr_api.py`
- Test: `backend/tests/unit/test_dispatcher_logic.py`

- [ ] **Step 1: Write the failing test (milestone + session id logic)**

`backend/tests/unit/test_dispatcher_logic.py`:

```python
from datetime import date

from nextshift.domain.models import LessonProgress, Pathway


def test_milestone_reached_on_full_completion():
    p = Pathway("pw-1", "w-001", "robot_fleet_operator", ["L1", "L2", "L3"])
    done = [LessonProgress("L1", "s", 2), LessonProgress("L2", "s", 2),
            LessonProgress("L3", "s", 2)]
    assert p.completion([d.lesson_id for d in done]) == 1.0


def test_no_milestone_when_partial():
    p = Pathway("pw-1", "w-001", "r", ["L1", "L2", "L3"])
    assert p.completion(["L1", "L2"]) < 1.0


def test_session_id_is_33_chars_and_stable():
    from nextshift.handlers.webhook_whatsapp import session_id_for
    assert session_id_for("w-001") == session_id_for("w-001")
    assert len(session_id_for("w-001")) >= 33
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/unit/test_dispatcher_logic.py -v
```

Expected: FAIL — `No module named 'nextshift.handlers'`

- [ ] **Step 3: Write webhook_whatsapp.py**

`backend/src/nextshift/handlers/__init__.py` — empty.

`backend/src/nextshift/handlers/webhook_whatsapp.py`:

```python
"""Lambda: SNS subscription for inbound WhatsApp events.

Flow: parse -> mark consent -> look up worker -> invoke AgentCore
(with stable per-worker session) -> guardrail -> reply.
"""
import hashlib
import json
import os

import boto3

from nextshift.channels.inbound import parse_whatsapp_sns_event
from nextshift.channels.whatsapp import WhatsAppSender

agentcore = boto3.client("bedrock-agentcore")
dynamodb = boto3.resource("dynamodb")
consent_table = dynamodb.Table(os.environ.get("CONSENT_TABLE", "nextshift-consent"))
workers_table = dynamodb.Table(os.environ.get("WORKERS_TABLE", "nextshift-workers"))

AGENT_RUNTIME_ARN = os.environ.get("AGENT_RUNTIME_ARN", "")


def session_id_for(worker_id: str) -> str:
    """Stable per-worker session across channels (>= 33 chars per API)."""
    digest = hashlib.sha1(worker_id.encode()).hexdigest()
    return f"nextshift-{digest}"[:48].ljust(33, "0")


def _find_worker_by_phone(phone: str) -> dict | None:
    # Workers table has a phone GSI for this lookup
    resp = workers_table.query(
        IndexName="phone-index",
        KeyConditionExpression=boto3.dynamodb.conditions.Key("phone").eq(phone))
    items = resp.get("Items", [])
    return items[0] if items else None


def handler(event, context):
    msg = parse_whatsapp_sns_event(event)
    if msg is None:
        return {"skipped": True}

    # Inbound user message opens the 24h window -> consent
    consent_table.put_item(Item={"phone": msg.phone, "user_consents": True})
    worker = _find_worker_by_phone(msg.phone)
    if worker is None or not AGENT_RUNTIME_ARN:
        WhatsAppSender(phone_id=os.environ.get("WA_PHONE_ID", "")).send_text(
            consent={"user_consents": True}, to=msg.phone,
            body="Thanks for reaching NextShift! Your HR team will enroll you shortly.")
        return {"ok": True}

    resp = agentcore.invoke_agent_runtime(
        agentRuntimeArn=AGENT_RUNTIME_ARN,
        payload=json.dumps({
            "prompt": msg.text,
            "worker_id": worker["worker_id"],
            "worker_name": worker.get("name", "friend"),
            "tone": worker.get("tone", "balanced"),
            "stage": worker.get("ttm_stage", "contemplation"),
        }).encode(),
        runtimeSessionId=session_id_for(worker["worker_id"]),
    )
    body = json.loads(resp["response"].read().decode())
    reply = body.get("reply", "")
    WhatsAppSender(phone_id=os.environ.get("WA_PHONE_ID", "")).send_text(
        consent={"user_consents": True}, to=msg.phone, body=reply)
    return {"ok": True, "reply": reply}
```

- [ ] **Step 4: Write invite.py**

`backend/src/nextshift/handlers/invite.py`:

```python
"""Lambda: HR-triggered SMS invites (SMS is the no-app baseline channel).

Event shape (from hr_api or manual test):
{"company_id": "velocity", "workers": [{"worker_id": "w-001", "phone": "+1...", "name": "Maria"}]}
"""
import os

from nextshift.channels.sms_rcs import SmsRcsSender

SMS_POOL_ID = os.environ.get("SMS_POOL_ID", "")

INVITE_TEMPLATE = (
    "Hi {name}, {company} is investing in new roles as automation grows. "
    "NextShift helps you get there, free, on your phone. Reply on WhatsApp "
    "to {wa_number} with 'START' or reply YES here."
)


def handler(event, context):
    sender = SmsRcsSender()
    results = []
    for w in event.get("workers", []):
        text = INVITE_TEMPLATE.format(
            name=w["name"].split()[0],
            company=event.get("company_name", "your company"),
            wa_number=os.environ.get("WA_DISPLAY_NUMBER", "our WhatsApp number"))
        results.append(sender.send(to=w["phone"], body=text,
                                   origination=SMS_POOL_ID))
    return {"invited": len(results), "message_ids": results}
```

- [ ] **Step 5: Write dispatcher.py**

`backend/src/nextshift/handlers/dispatcher.py`:

```python
"""Lambda: EventBridge daily run.

1. Send each enrolled worker their due lesson (WhatsApp if consented, SMS fallback).
2. On 100% pathway completion, send the SES milestone email with certificate.
"""
import os

import boto3

from nextshift.agent.store import Store
from nextshift.channels.email import EmailSender
from nextshift.channels.sms_rcs import SmsRcsSender
from nextshift.channels.whatsapp import WhatsAppSender
from nextshift.domain.scheduler import due_lessons
from datetime import date

dynamodb = boto3.resource("dynamodb")
consent_table = dynamodb.Table(os.environ.get("CONSENT_TABLE", "nextshift-consent"))
store = Store(dynamodb=dynamodb)

CERT_TEMPLATE = """<h1>Congratulations, {name}!</h1>
<p>You completed the <b>{role}</b> learning pathway on NextShift.</p>
<p>Your verified transcript is attached to your profile. Tap below to apply:</p>
<p><a href="{apply_url}">Apply for the {role} role</a></p>
<p>Skills demonstrated: {skills}</p>
"""


def handler(event, context):
    sent, milestones = 0, 0
    workers = store.list_enrolled_workers()
    for worker in workers:
        consent = consent_table.get_item(Key={"phone": worker.phone}).get("Item")
        progress = store.list_progress(worker.worker_id)
        pathway = store.get_pathway(worker.worker_id)
        if pathway is None:
            continue

        done = [p.lesson_id for p in progress if p.correct_streak >= 1]
        if pathway.completion(done) >= 1.0:
            milestones += 1
            _send_milestone(worker, pathway)
            continue

        lessons = store.load_lessons()
        due = due_lessons(progress, date.today())
        if not due and done:      # no reviews pending but not started items? nudge next new lesson
            pending = [lid for lid in pathway.lesson_ids if lid not in done]
            if pending:
                lesson = lessons.get(pending[0], {})
                _deliver(worker, consent, lesson)
                sent += 1
            continue
        for p in due[:1]:         # Fogg: one tiny action per day
            lesson = lessons.get(p.lesson_id, {})
            _deliver(worker, consent, lesson)
            sent += 1
    return {"lessons_sent": sent, "milestones": milestones}


def _deliver(worker, consent, lesson) -> None:
    body = (f"Today's 2-minute lesson:\n{lesson.get('question', '')}\n"
            + "\n".join(f"{i+1}. {o}" for i, o in enumerate(lesson.get("options", [])))
            + "\n\nReply with the number of your answer.")
    if consent and consent.get("user_consents"):
        WhatsAppSender(phone_id=os.environ.get("WA_PHONE_ID", "")).send_text(
            consent=consent, to=worker.phone, body=body)
    else:
        SmsRcsSender().send(to=worker.phone, body=body,
                            origination=os.environ.get("SMS_POOL_ID", ""))


def _send_milestone(worker, pathway) -> None:
    roles = store.list_roles(worker.company_id)
    role = next((r for r in roles if r.role_id == pathway.target_role_id), None)
    title = role.title if role else pathway.target_role_id
    apply_url = os.environ.get("HR_APPLY_URL", "https://hr.velocity.example/apply")
    EmailSender(from_address=os.environ.get("SES_FROM", "")).send(
        to=f"{worker.worker_id}@workers.velocity-logistics.example",
        subject="Your NextShift certificate is ready",
        html=CERT_TEMPLATE.format(
            name=worker.name.split()[0], role=title,
            apply_url=apply_url,
            skills=", ".join(pathway.lesson_ids)))
    # RCS card (spec journey step 7): rich channel for the interview tap;
    # falls back to SMS pool when no RCS agent ARN is configured.
    SmsRcsSender().send(
        to=worker.phone,
        body=(f"Congratulations {worker.name.split()[0]}! You completed the {title} "
              f"pathway. Book your interview: {apply_url}"),
        origination=os.environ.get("RCS_AGENT_ARN") or os.environ.get("SMS_POOL_ID", ""))
```

Add `list_enrolled_workers` to `Store`:

```python
    def list_enrolled_workers(self) -> list:
        """Workers that have opted in (scanned via GSI; demo scale is small)."""
        table = self._tables["pathways"]
        resp = table.scan(ProjectionExpression="worker_id")
        ids = [i["worker_id"] for i in resp.get("Items", [])]
        workers = []
        for wid in ids:
            w = self.get_worker(wid)
            if w:
                workers.append(w)
        return workers
```

- [ ] **Step 6: Write hr_api.py**

`backend/src/nextshift/handlers/hr_api.py`:

```python
"""Lambda behind API Gateway: GET /workers, POST /impact-map, POST /invite."""
import json
import os

import boto3
from boto3.dynamodb.conditions import Attr

from nextshift.domain.impact_map import parse_impact_map

dynamodb = boto3.resource("dynamodb")
workers_table = dynamodb.Table(os.environ.get("WORKERS_TABLE", "nextshift-workers"))
COMPANY_ID = os.environ.get("COMPANY_ID", "velocity")


def handler(event, context):
    route = f"{event.get('requestContext', {}).get('http', {}).get('method', '')} {event.get('rawPath', '')}"
    body = json.loads(event.get("body") or "{}")

    if event.get("rawPath") == "/workers" and event.get("requestContext", {}).get("http", {}).get("method") == "GET":
        resp = workers_table.scan(FilterExpression=Attr("company_id").eq(COMPANY_ID))
        return {"statusCode": 200, "body": json.dumps(resp.get("Items", []))}

    if event.get("rawPath") == "/impact-map" and event.get("requestContext", {}).get("http", {}).get("method") == "POST":
        workers, skipped = parse_impact_map(body.get("csv", ""), company_id=COMPANY_ID)
        with workers_table.batch_writer() as batch:
            for w in workers:
                batch.put_item(Item={
                    "worker_id": w.worker_id, "phone": w.phone, "name": w.name,
                    "current_role": w.current_role, "company_id": w.company_id,
                    "opted_in": False, "ttm_stage": "precontemplation",
                })
        return {"statusCode": 200, "body": json.dumps({"ingested": len(workers), "skipped": skipped})}

    if event.get("rawPath") == "/invite" and event.get("requestContext", {}).get("http", {}).get("method") == "POST":
        import boto3 as b3
        lambda_client = b3.client("lambda")
        lambda_client.invoke(
            FunctionName=os.environ.get("INVITE_FUNCTION", "nextshift-invite"),
            InvocationType="Event",
            Payload=json.dumps({"company_id": COMPANY_ID, "workers": body.get("workers", [])}).encode())
        return {"statusCode": 202, "body": json.dumps({"invite_queued": True})}

    return {"statusCode": 404, "body": json.dumps({"error": f"unknown route {route}"})}
```

- [ ] **Step 7: Run test to verify it passes**

```bash
python -m pytest tests/unit/test_dispatcher_logic.py -v
```

Expected: `3 passed`

- [ ] **Step 8: Run full suite and commit**

```bash
python -m pytest tests/unit -v
```

Expected: all passed (23 tests)

```bash
git add backend && git commit -m "feat: lambda handlers for webhook, invite, dispatcher, hr api"
```

---

### Task 12: Seed data (Velocity Logistics)

**Files:**
- Create: `backend/seed/impact_map.csv`, `backend/seed/roles.json`, `backend/seed/lessons.json`, `backend/scripts/seed.py`

- [ ] **Step 1: Create impact_map.csv**

`backend/seed/impact_map.csv`:

```csv
worker_id,name,phone,current_role
w-001,Maria Silva,+15550001111,warehouse_associate
w-002,John Okafor,+15550002222,inventory_clerk
w-003,Ana Reyes,+15550003333,warehouse_associate
```

- [ ] **Step 2: Create roles.json**

`backend/seed/roles.json`:

```json
{
  "company_id": "velocity",
  "roles": [
    {"role_id": "warehouse_associate", "title": "Warehouse Associate",
     "affected": true,
     "required_skills": {"physical_handling": 4, "scanning": 3, "wms_software": 2}},
    {"role_id": "inventory_clerk", "title": "Inventory Clerk",
     "affected": true,
     "required_skills": {"wms_software": 3, "scanning": 3, "data_entry": 3}},
    {"role_id": "robot_fleet_operator", "title": "Robot Fleet Operator",
     "affected": false,
     "required_skills": {"robot_monitoring": 3, "exception_handling": 3,
                          "safety_protocols": 4, "wms_software": 3}},
    {"role_id": "customer_care_specialist", "title": "Customer Care Specialist",
     "affected": false,
     "required_skills": {"de_escalation": 3, "order_management": 3,
                          "wms_software": 3, "empathy": 4}}
  ],
  "worker_skills": {
    "w-001": {"physical_handling": 5, "scanning": 4, "wms_software": 3, "safety_protocols": 4, "teamwork": 4},
    "w-002": {"wms_software": 4, "scanning": 3, "data_entry": 4, "attention_detail": 4},
    "w-003": {"physical_handling": 4, "scanning": 3, "empathy": 4, "teamwork": 5}
  }
}
```

- [ ] **Step 3: Create lessons.json (complete, retrieval-first)**

`backend/seed/lessons.json`:

```json
{
  "L-RFO-01": {"role_ids": ["robot_fleet_operator"], "skill": "robot_monitoring",
    "question": "An AMR robot stops in aisle 3 with a flashing amber light. What do you check FIRST?",
    "options": ["Push the robot to the dock", "Look for an obstruction in its path on the tablet map",
                "Turn off the whole fleet", "Call the robot manufacturer"],
    "answer_index": 1,
    "explanation": "Amber means a recoverable fault. The fleet console shows which robot and why — check the tablet map first."},
  "L-RFO-02": {"role_ids": ["robot_fleet_operator"], "skill": "safety_protocols",
    "question": "A robot is stuck blocking a fire exit route. What is the correct first action?",
    "options": ["Ignore it, robots move eventually", "Use the manual override to move it clear, then log the incident",
                "Lift the robot out of the way", "Wait for the fire alarm to test it"],
    "answer_index": 1,
    "explanation": "Manual override clears the path; every blockage of a fire route must be logged."},
  "L-RFO-03": {"role_ids": ["robot_fleet_operator"], "skill": "exception_handling",
    "question": "The system shows 'pick exception: item not found' for order 8841. What next?",
    "options": ["Cancel the order", "Flag the slot for cycle count and reroute the pick",
                "Guess the nearest slot", "Skip it silently"],
    "answer_index": 1,
    "explanation": "Exceptions are flagged for cycle count; rerouting keeps the order promise."},
  "L-RFO-04": {"role_ids": ["robot_fleet_operator"], "skill": "wms_software",
    "question": "In the WMS, what does a red 'charge critical' icon on a robot mean?",
    "options": ["Robot is damaged", "Battery below threshold — send it to charge station",
                "Robot is offline forever", "Software update needed"],
    "answer_index": 1,
    "explanation": "Charge-critical robots must be routed to charge before they die mid-run."},
  "L-RFO-05": {"role_ids": ["robot_fleet_operator"], "skill": "robot_monitoring",
    "question": "Throughput on the dashboard dropped 30% in the last hour. What is the FIRST thing to look at?",
    "options": ["Fire the night shift", "Check the fleet status board for faulted/charging robots",
                "Reboot the server", "Order more robots"],
    "answer_index": 1,
    "explanation": "Faulted or charging robots reduce fleet capacity — the status board shows it instantly."},
  "L-RFO-06": {"role_ids": ["robot_fleet_operator"], "skill": "exception_handling",
    "question": "Two robots deadlock facing each other in a narrow aisle. What do you do?",
    "options": ["Let them figure it out", "Pause one robot on the console so the other passes, then report the hotspot zone",
                "Push one robot", "Shut down the fleet"],
    "answer_index": 1,
    "explanation": "Pause-one-unblocks-both; repeated deadlocks mark a traffic hotspot for re-mapping."},
  "L-CCS-01": {"role_ids": ["customer_care_specialist"], "skill": "de_escalation",
    "question": "A customer says: 'This is the THIRD late delivery this month!' What is the best first reply?",
    "options": ["It's the carrier's fault, not us", "I'm sorry this keeps happening — let me look at your orders right now",
                "Please calm down", "That's our policy"],
    "answer_index": 1,
    "explanation": "Acknowledge the pattern, take ownership, move to action — the A-A-R pattern."},
  "L-CCS-02": {"role_ids": ["customer_care_specialist"], "skill": "order_management",
    "question": "A customer wants to change the delivery address AFTER the order shipped. What can you offer?",
    "options": ["Nothing, it's impossible", "Check carrier intercept options and, if unavailable, the closest pickup point",
                "Cancel and charge again", "Tell them to refuse the package"],
    "answer_index": 1,
    "explanation": "Intercept first; pickup point is the fallback that still delivers."},
  "L-CCS-03": {"role_ids": ["customer_care_specialist"], "skill": "empathy",
    "question": "A caller's medicine delivery is late and they sound anxious. Best response order?",
    "options": ["Explain carrier SLAs", "Acknowledge the urgency, check live status, give a firm follow-up time",
                "Offer a coupon", "Ask them to call back later"],
    "answer_index": 1,
    "explanation": "Empathy first, concrete information second, commitment to follow up third."},
  "L-CCS-04": {"role_ids": ["customer_care_specialist"], "skill": "wms_software",
    "question": "In the WMS, what status means an order is packed but waiting for carrier scan?",
    "options": ["READY_TO_SHIP", "CARRIER_PENDING", "IN_PACK", "CLOSED"],
    "answer_index": 1,
    "explanation": "CARRIER_PENDING = packed, label printed, waiting for the carrier's first scan."}
}
```

- [ ] **Step 4: Create scripts/seed.py**

`backend/scripts/seed.py`:

```python
"""Load seed data into DynamoDB. Run: python scripts/seed.py"""
import json
import os
import sys
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nextshift.domain.impact_map import parse_impact_map  # noqa: E402

SEED_DIR = Path(__file__).parent.parent / "seed"


def main() -> None:
    dynamodb = boto3.resource("dynamodb")
    workers = dynamodb.Table(os.environ.get("WORKERS_TABLE", "nextshift-workers"))
    roles = dynamodb.Table(os.environ.get("ROLES_TABLE", "nextshift-roles"))

    csv_text = (SEED_DIR / "impact_map.csv").read_text(encoding="utf-8")
    data = json.loads((SEED_DIR / "roles.json").read_text(encoding="utf-8"))
    lessons = json.loads((SEED_DIR / "lessons.json").read_text(encoding="utf-8"))

    workers, skipped = parse_impact_map(csv_text, company_id=data["company_id"])
    for w in workers:
        workers.put_item(Item={
            "worker_id": w.worker_id, "phone": w.phone, "name": w.name,
            "current_role": w.current_role, "company_id": w.company_id,
            "opted_in": False, "ttm_stage": "precontemplation",
            "skills": data["worker_skills"].get(w.worker_id, {}),
        })
    for r in data["roles"]:
        roles.put_item(Item={
            "role_id": r["role_id"], "company_id": data["company_id"],
            "title": r["title"], "affected": r["affected"],
            "required_skills": r["required_skills"],
        })
    roles.put_item(Item={
        "role_id": "LESSONS", "company_id": "GLOBAL",
        "payload": json.dumps(lessons),
    })
    print("Seed complete: 3 workers, 5 roles, 10 lessons.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Smoke-test locally (dynamo local optional; else syntax check)**

```bash
python -c "import ast; ast.parse(open('scripts/seed.py').read()); print('syntax ok')"
```

Expected: `syntax ok`

- [ ] **Step 6: Commit**

```bash
git add backend && git commit -m "feat: velocity logistics seed data and loader"
```

---

### Task 13: CDK infrastructure

**Files:**
- Create: `infra/requirements.txt`, `infra/app.py`, `infra/cdk.json`, `infra/nextshift/__init__.py`, `infra/nextshift/stack_core.py`, `infra/nextshift/stack_messaging.py`

- [ ] **Step 1: Create infra requirements**

`infra/requirements.txt`:

```
aws-cdk-lib>=2.160
constructs>=10.0
```

`infra/cdk.json`:

```json
{"app": "python3 app.py"}
```

`infra/nextshift/__init__.py` — empty.

- [ ] **Step 2: Write stack_core.py**

`infra/nextshift/stack_core.py`:

```python
"""Core state: DynamoDB tables + SNS topic for inbound WhatsApp + SES."""
from aws_cdk import Duration, Stack
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk import aws_sns as sns
from constructs import Construct


class CoreStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        def table(name: str, partition: str, sort: str | None = None,
                  gsi: list[dynamodb.GlobalSecondaryIndexProps] | None = None):
            return dynamodb.Table(
                self, name, table_name=f"nextshift-{name}",
                partition_key=dynamodb.Attribute(name=partition,
                                                 type=dynamodb.AttributeType.STRING),
                sort_key=(dynamodb.Attribute(name=sort, type=dynamodb.AttributeType.STRING)
                          if sort else None),
                billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
                global_secondary_indexes=gsi or [],
            )

        phone_index = dynamodb.GlobalSecondaryIndexProps(
            index_name="phone-index",
            partition_key=dynamodb.Attribute(name="phone",
                                             type=dynamodb.AttributeType.STRING))
        company_index = dynamodb.GlobalSecondaryIndexProps(
            index_name="company-index",
            partition_key=dynamodb.Attribute(name="company_id",
                                             type=dynamodb.AttributeType.STRING))

        self.workers = table("workers", "worker_id", gsi=[phone_index])
        self.roles = table("roles", "role_id", sort_key="company_id",
                           gsi=[company_index])
        self.pathways = table("pathways", "worker_id", sort_key="pathway_id")
        self.progress = table("progress", "worker_id", sort_key="lesson_id")
        self.consent = table("consent", "phone")
        self.events = table("events", "worker_id", sort_key="ts",
                            time_to_live_attribute="expiration_date")

        self.inbound_whatsapp = sns.Topic(
            self, "inbound-whatsapp", topic_name="nextshift-inbound-whatsapp")

        # SES: domain/identity must be verified in console; construct records intent.
        # For hackathon: verify a sandbox email, then set SES_FROM env on lambdas.
```

- [ ] **Step 3: Write stack_messaging.py**

`infra/nextshift/stack_messaging.py`:

```python
"""Lambda functions, EventBridge schedules, API Gateway for HR dashboard."""
import os
from pathlib import Path

from aws_cdk import Duration, Stack
from aws_cdk import aws_apigatewayv2 as apigwv2
from aws_cdk import aws_apigatewayv2_integrations as apigwv2i
from aws_cdk import aws_events as events
from aws_cdk import aws_events_targets as targets
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_sns_subscriptions as sns_subs
from constructs import Construct

from nextshift.stack_core import CoreStack

BACKEND = Path(__file__).parents[2] / "backend" / "src"


def fn(scope, name: str, handler: str, env: dict, timeout: int = 60) -> lambda_.Function:
    return lambda_.Function(
        scope, name, function_name=f"nextshift-{name}",
        runtime=lambda_.Runtime.PYTHON_3_12,
        handler=handler,
        code=lambda_.Code.from_asset(str(BACKEND)),
        memory_size=512,
        timeout=Duration.seconds(timeout),
        environment=env,
    )


class MessagingStack(Stack):
    def __init__(self, scope: Construct, construct_id: str,
                 core: CoreStack, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        env_common = {
            "WORKERS_TABLE": core.workers.table_name,
            "ROLES_TABLE": core.roles.table_name,
            "PATHWAYS_TABLE": core.pathways.table_name,
            "PROGRESS_TABLE": core.progress.table_name,
            "CONSENT_TABLE": core.consent.table_name,
            "EVENTS_TABLE": core.events.table_name,
        }

        webhook = fn(self, "webhook", "nextshift.handlers.webhook_whatsapp.handler",
                     {**env_common, "WA_PHONE_ID": os.environ.get("WA_PHONE_ID", ""),
                      "AGENT_RUNTIME_ARN": os.environ.get("AGENT_RUNTIME_ARN", "")},
                     timeout=120)
        core.inbound_whatsapp.add_subscription(sns_subs.LambdaSubscription(webhook))

        invite = fn(self, "invite", "nextshift.handlers.invite.handler",
                    {**env_common, "SMS_POOL_ID": os.environ.get("SMS_POOL_ID", ""),
                     "WA_DISPLAY_NUMBER": os.environ.get("WA_DISPLAY_NUMBER", "")})

        dispatcher = fn(self, "dispatcher", "nextshift.handlers.dispatcher.handler",
                        {**env_common, "WA_PHONE_ID": os.environ.get("WA_PHONE_ID", ""),
                         "SMS_POOL_ID": os.environ.get("SMS_POOL_ID", ""),
                         "RCS_AGENT_ARN": os.environ.get("RCS_AGENT_ARN", ""),
                         "SES_FROM": os.environ.get("SES_FROM", "")},
                        timeout=120)

        events.Rule(
            self, "daily-lessons", schedule=events.Schedule.cron(
                minute="0", hour="14"),  # 09:00 US Eastern (UTC-5 approx)
            targets=[targets.LambdaFunction(dispatcher)])

        hr_api = fn(self, "hr-api", "nextshift.handlers.hr_api.handler",
                    {**env_common, "COMPANY_ID": "velocity",
                     "INVITE_FUNCTION": invite.function_name})

        api = apigwv2.HttpApi(self, "hr-http-api")
        api.add_routes(
            path="/workers",
            methods=[apigwv2.HttpMethod.GET],
            integration=apigwv2i.HttpLambdaIntegration("workers", hr_api))
        api.add_routes(
            path="/impact-map",
            methods=[apigwv2.HttpMethod.POST],
            integration=apigwv2i.HttpLambdaIntegration("impact", hr_api))
        api.add_routes(
            path="/invite",
            methods=[apigwv2.HttpMethod.POST],
            integration=apigwv2i.HttpLambdaIntegration("invite", hr_api))

        for t in (core.workers, core.roles, core.pathways,
                  core.progress, core.consent, core.events):
            t.grant_read_write_data(webhook)
            t.grant_read_write_data(dispatcher)
            t.grant_read_write_data(hr_api)
        core.inbound_whatsapp.grant_publish(webhook)

        # Cross-stack references
        self.api_url = api.url
```

- [ ] **Step 4: Write app.py**

`infra/app.py`:

```python
from aws_cdk import App, Environment

from nextshift.stack_core import CoreStack
from nextshift.stack_messaging import MessagingStack

app = App()
core = CoreStack(app, "nextshift-core")
messaging = MessagingStack(app, "nextshift-messaging", core)
app.synth()
```

- [ ] **Step 5: Synth check**

```bash
cd infra && python -m venv .venv && source .venv/Scripts/activate && pip install -r requirements.txt && cdk synth --quiet
```

Expected: synth completes with no errors. Fix any import/typo errors until clean.

- [ ] **Step 6: Commit**

```bash
cd /d/awscdspartnerHackathon && git add infra && git commit -m "feat: cdk stacks for tables, sns, lambdas, eventbridge, api gateway"
```

---

### Task 14: Deploy pipeline + integration smoke test

**Files:**
- Create: `backend/scripts/create_memory.py`, `docs/runbook.md`

- [ ] **Step 1: Write create_memory.py**

`backend/scripts/create_memory.py`:

```python
"""Create the AgentCore Memory resource once; store id in SSM.
Run: python scripts/create_memory.py"""
import boto3

from bedrock_agentcore.memory import MemoryClient

ssm = boto3.client("ssm")

client = MemoryClient(region_name="us-east-1")
memory = client.create_memory_and_wait(
    name="nextshift-worker-memory",
    description="Cross-channel worker profiles and conversation history",
    strategies=[
        {"semanticMemoryStrategy": {
            "name": "FactExtractor",
            "namespaceTemplates": ["/facts/{actorId}/"]}},
        {"userPreferenceMemoryStrategy": {
            "name": "PreferenceLearner",
            "namespaceTemplates": ["/preferences/{actorId}/"]}},
    ],
)
ssm.put_parameter(Name="/nextshift/memory-id",
                  Value=memory["id"], Type="String", Overwrite=True)
print(f"Memory created: {memory['id']}")
```

- [ ] **Step 2: Deploy CDK stacks**

Prerequisites (console, one-time): link WABA + phone in EUM Social (get `WA_PHONE_ID`), create SMS pool (`SMS_POOL_ID`), verify SES identity (`SES_FROM`), request WhatsApp template `nextshift_invite` (UTILITY category).

```bash
cd infra && source .venv/Scripts/activate && cdk deploy nextshift-core nextshift-messaging
```

Expected: both stacks CREATE_COMPLETE.

- [ ] **Step 3: Create memory + deploy agent**

```bash
cd ../backend && source .venv/Scripts/activate && pip install "bedrock-agentcore[cli]" && python scripts/create_memory.py && MEMORY_ID=$(aws ssm get-parameter --name /nextshift/memory-id --query Parameter.Value --output text) && agentcore deploy entrypoint.py --region us-east-1
```

Record the returned Agent Runtime ARN, then re-deploy messaging stack with it:

```bash
cd ../infra && AGENT_RUNTIME_ARN=<arn> WA_PHONE_ID=<id> SMS_POOL_ID=<pool> SES_FROM=<email> cdk deploy nextshift-messaging
```

- [ ] **Step 4: Seed + end-to-end smoke**

```bash
cd ../backend && python scripts/seed.py
aws s3 ... # (skip; local check only)
aws lambda invoke --function-name nextshift-dispatcher --payload '{}' /tmp/dispatch.json && cat /tmp/dispatch.json
```

Expected: `{"lessons_sent": 0, "milestones": 0}` (nobody enrolled yet — correct).

Manual WhatsApp check: text "hi" to the test number -> agent replies via the full loop (SNS -> webhook -> AgentCore -> WhatsApp). If no reply, inspect CloudWatch logs for `nextshift-webhook` first.

- [ ] **Step 5: Write docs/runbook.md**

`docs/runbook.md`:

```markdown
# NextShift Runbook

## One-time setup
1. EUM Social: link WABA, register phone (WA_PHONE_ID), create template `nextshift_invite`.
2. End User Messaging: create SMS pool (SMS_POOL_ID).
3. SES: verify identity (SES_FROM); sandbox: verify worker email too.
4. `python backend/scripts/create_memory.py` -> MEMORY_ID in SSM.
5. `agentcore deploy backend/src/nextshift/agent/entrypoint.py` -> AGENT_RUNTIME_ARN.

## Deploy
- `cd infra && cdk deploy nextshift-core nextshift-messaging`
- Env vars: WA_PHONE_ID, SMS_POOL_ID, SES_FROM, AGENT_RUNTIME_ARN.

## Seed & operate
- `python backend/scripts/seed.py`
- Daily lessons: EventBridge 14:00 UTC -> nextshift-dispatcher.
- Inbound: WABA -> EUM Social -> SNS nextshift-inbound-whatsapp -> nextshift-webhook.

## Demo worker journey
1. POST /impact-map (CSV)  2. POST /invite (SMS)  3. worker replies on WhatsApp
4. agent profiles + match_role + enroll_pathway  5. daily lessons  6. milestone email.
```

- [ ] **Step 6: Commit**

```bash
git add backend docs && git commit -m "feat: memory creation script, runbook, integration smoke"
```

---

### Task 15: HR dashboard (Next.js)

**Files:**
- Create: `frontend/package.json`, `frontend/tsconfig.json`, `frontend/next.config.js`, `frontend/src/app/page.tsx`, `frontend/src/app/layout.tsx`, `frontend/src/lib/api.ts`

- [ ] **Step 1: Scaffold files**

`frontend/package.json`:

```json
{
  "name": "nextshift-dashboard",
  "private": true,
  "scripts": {"dev": "next dev", "build": "next build", "start": "next start"},
  "dependencies": {"next": "14.2.15", "react": "18.3.1", "react-dom": "18.3.1"},
  "devDependencies": {"typescript": "5.5.4", "@types/react": "18.3.5", "@types/node": "20.14.9"}
}
```

`frontend/tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2017",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": false,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "paths": {"@/*": ["./src/*"]}
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

`frontend/next.config.js`:

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {};
module.exports = nextConfig;
```

- [ ] **Step 2: Write api.ts + page**

`frontend/src/lib/api.ts`:

```typescript
const API = process.env.NEXT_PUBLIC_API_URL ?? "";

export interface WorkerRow {
  worker_id: string;
  name: string;
  phone: string;
  current_role: string;
  opted_in: boolean;
  ttm_stage: string;
}

export async function fetchWorkers(): Promise<WorkerRow[]> {
  const res = await fetch(`${API}/workers`);
  if (!res.ok) throw new Error(`workers ${res.status}`);
  return res.json();
}

export async function uploadImpactMap(csv: string): Promise<number> {
  const res = await fetch(`${API}/impact-map`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ csv }),
  });
  const body = await res.json();
  return body.ingested ?? 0;
}

export async function inviteWorkers(rows: WorkerRow[]): Promise<void> {
  const res = await fetch(`${API}/invite`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      workers: rows.map((w) => ({
        worker_id: w.worker_id, name: w.name, phone: w.phone,
      })),
    }),
  });
  if (!res.ok) throw new Error(`invite ${res.status}`);
}
```

`frontend/src/app/layout.tsx`:

```tsx
export const metadata = { title: "NextShift - HR Dashboard" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body style={{ fontFamily: "system-ui", margin: "2rem" }}>{children}</body>
    </html>
  );
}
```

`frontend/src/app/page.tsx`:

```tsx
"use client";

import { useCallback, useEffect, useState } from "react";
import { fetchWorkers, inviteWorkers, uploadImpactMap, WorkerRow } from "@/lib/api";

const STAGE_COLORS: Record<string, string> = {
  precontemplation: "#e0e0e0",
  contemplation: "#ffe08a",
  preparation: "#a5d8ff",
  action: "#b2f2bb",
};

export default function Home() {
  const [workers, setWorkers] = useState<WorkerRow[]>([]);
  const [status, setStatus] = useState("");

  const refresh = useCallback(async () => {
    try {
      setWorkers(await fetchWorkers());
    } catch {
      setStatus("Could not load workers. Is the API deployed?");
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  async function onUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    const ingested = await uploadImpactMap(await file.text());
    setStatus(`Impact map ingested: ${ingested} workers`);
    refresh();
  }

  async function onInvite() {
    await inviteWorkers(workers);
    setStatus("SMS invites queued");
  }

  return (
    <main>
      <h1>NextShift HR Dashboard</h1>
      <p>{status}</p>
      <input type="file" accept=".csv" onChange={onUpload} />
      <button onClick={onInvite}>Send SMS invites to all</button>
      <table>
        <thead>
          <tr><th>Worker</th><th>Role</th><th>Phone</th><th>Stage</th><th>Opted in</th></tr>
        </thead>
        <tbody>
          {workers.map((w) => (
            <tr key={w.worker_id}>
              <td>{w.name}</td>
              <td>{w.current_role}</td>
              <td>{w.phone}</td>
              <td>
                <span style={{
                  background: STAGE_COLORS[w.ttm_stage] ?? "#eee",
                  padding: "2px 8px", borderRadius: 8,
                }}>{w.ttm_stage}</span>
              </td>
              <td>{w.opted_in ? "yes" : "no"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}
```

- [ ] **Step 3: Verify build**

```bash
cd frontend && npm install && npm run build
```

Expected: build succeeds with no type errors.

- [ ] **Step 4: Commit**

```bash
cd /d/awscdspartnerHackathon && git add frontend && git commit -m "feat: HR dashboard with impact map upload and invite"
```

---

### Task 16: Demo assets + submission package

**Files:**
- Create: `README.md`, `LICENSE`, `docs/architecture.md`, `docs/demo-script.md`

- [ ] **Step 1: Create LICENSE (MIT)**

Standard MIT license text, copyright 2026 NextShift Team.

- [ ] **Step 2: Write README.md**

`README.md` must contain: pitch, architecture diagram reference, research table (28 sources, copy from spec section 5), setup steps (from `docs/runbook.md`), demo script link, license badge in About section. Full text is copied from the spec + runbook; no new content needed beyond assembly.

- [ ] **Step 3: Write docs/architecture.md**

Embed the ASCII diagram from spec section 6, replacing placeholders with real deployed resource names after Task 14 (table names, topic name, function names).

- [ ] **Step 4: Write docs/demo-script.md (3-minute storyboard)**

`docs/demo-script.md`:

```markdown
# NextShift Demo Script (3:00)

0:00-0:20  Problem: WEF numbers on screen. "92M jobs displaced, 170M new ones.
           The gap is the transition itself."
0:20-0:40  HR dashboard: upload impact_map.csv -> 3 workers ingested. Send SMS invite.
0:40-1:10  Phone (left half): SMS arrives. Maria replies on WhatsApp.
1:10-1:50  Agent conversation: profiling (2 questions shown), match_role output
           (Robot Fleet Operator 50% match, transferable skills highlighted),
           Maria chooses -> enroll_pathway. Point at architecture overlay:
           "SMS -> WhatsApp -> AgentCore Runtime, one memory."
1:50-2:30  Next day (EventBridge): daily lesson arrives. Maria answers. Wrong
           answer -> explanation + rescheduled tomorrow (spacing effect).
2:30-2:50  Milestone email opens: certificate + apply button. LinkedIn stat
           overlay: internal movers stay 40% longer.
2:50-3:00  Close: "AI didn't replace Maria. It promoted her." CTA + repo link.
```

- [ ] **Step 5: Devpost submission checklist review**

Verify against spec section 11: repo + MIT license visible in About, architecture diagram, text description with citations, ~3-min video (record per demo-script), deployed URL (API url + dashboard), ACE opportunity ID with campaign code, WhatsApp usage description for Meta prize.

- [ ] **Step 6: Final commit**

```bash
git add README.md LICENSE docs && git commit -m "docs: demo script, architecture, submission package"
```

---

## Task Dependency Order

Task 0 -> 1 -> {2, 3, 4, 5} (independent, any order) -> 6 -> 7 -> 8 -> 9 -> 10 -> 11 -> 12 -> 13 -> 14 -> 15 -> 16.

Tasks 2-5 are pure-logic and parallelizable. Task 14 requires AWS console prerequisites started early (WABA linking can take days — start it immediately, see Task 14 Step 2 note).

## Definition of Done (per spec section 11)

- [ ] All unit tests green (`python -m pytest backend/tests -v`)
- [ ] `cdk synth` clean
- [ ] Deployed: SMS invite -> WhatsApp reply -> agent conversation -> daily lesson -> milestone email, verified once end-to-end
- [ ] README complete with citations; MIT license visible
- [ ] Demo video recorded per storyboard
- [ ] ACE opportunity ID created
