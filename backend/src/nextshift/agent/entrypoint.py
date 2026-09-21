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

    agent = Agent(model=MODEL_ID, tools=AGENT_TOOLS, system_prompt=system)
    result = agent(prompt)  # strands Agent is callable, returns the final message
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
