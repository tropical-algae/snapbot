from typing import Any

from langchain_core.runnables import RunnableConfig

from snapbot.common.model import ToolArtifactType
from snapbot.common.utils.decorator import snap_tool
from snapbot.common.utils.file import get_memory_workspace_path, read_file
from snapbot.core.agent.models import SubAgentName


@snap_tool(SubAgentName.MEMORYAGENT)
async def read_preference_memory(config: RunnableConfig) -> dict[str, Any]:
    """Read the current agent preference memory file."""
    filepath = await get_memory_workspace_path(config, ToolArtifactType.PREFERENCE_MEMORY)
    return {
        "ok": True,
        "path": str(filepath),
        "content": await read_file(filepath),
    }
