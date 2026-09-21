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
