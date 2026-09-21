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
