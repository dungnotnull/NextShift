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
