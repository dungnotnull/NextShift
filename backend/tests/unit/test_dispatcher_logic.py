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
