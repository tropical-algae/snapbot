from typing import Any

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from snapbot.common.utils.decorator import tool_meta
from snapbot.common.utils.file import read_file
from snapbot.core.agent.models import SubAgentName
from snapbot.core.middleware.service import get_memory_ids, get_preference_memory_path


@tool_meta(SubAgentName.MEMORYAGENT)
@tool
def read_preference_memory(config: RunnableConfig) -> dict[str, Any]:
    """Read the current thread's agent preference memory file."""
    thread_id, _ = get_memory_ids(config)
    path = get_preference_memory_path(thread_id)
    return {
        "ok": True,
        "path": str(path),
        "content": read_file(path),
    }
