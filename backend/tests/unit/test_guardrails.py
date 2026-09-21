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
