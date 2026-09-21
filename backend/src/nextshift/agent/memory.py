"""AgentCore Memory bootstrap. MEMORY_ID is created once by scripts/create_memory.py."""
import os

from bedrock_agentcore.memory import MemorySessionManager
from bedrock_agentcore.memory.constants import ConversationalMessage, MessageRole

def get_session(worker_id: str) -> MemorySessionManager | None:
    memory_id = os.environ.get("MEMORY_ID", "")
    if not memory_id:
        return None
    manager = MemorySessionManager(memory_id=memory_id,
                                   region_name=os.environ.get("AWS_REGION", "us-east-1"))
    try:
        raw = f"nextshift-{worker_id}-session"
        session_id = raw[:33].ljust(33, "0")
        manager.create_memory_session(actor_id=worker_id,
                                      session_id=session_id)
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
