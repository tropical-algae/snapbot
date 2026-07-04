from typing import Any

from langchain_core.runnables import RunnableConfig

from snapbot.common.utils.decorator import snap_tool
from snapbot.common.utils.file import read_file
from snapbot.core.agent.models import SubAgentName
from snapbot.core.middleware.service import get_identity_memory_path, get_memory_ids


@snap_tool(SubAgentName.MEMORYAGENT)
def read_identity_memory(config: RunnableConfig) -> dict[str, Any]:
    """Read the current user's identity memory file."""
    _, user_id = get_memory_ids(config)
    path = get_identity_memory_path(user_id)
    return {
        "ok": True,
        "path": str(path),
        "content": read_file(path),
    }
