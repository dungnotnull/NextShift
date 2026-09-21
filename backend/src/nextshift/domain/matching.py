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
