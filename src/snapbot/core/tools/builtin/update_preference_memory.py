from typing import Any

from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field

from snapbot.common.model import ToolArtifactType
from snapbot.common.utils.decorator import snap_tool
from snapbot.common.utils.file import get_memory_workspace_path, read_file, write_file
from snapbot.core.agent.models import SubAgentName


class UpdatePreferenceMemoryInput(BaseModel):
    content: str = Field(description="Full Markdown content for the agent preference memory.")


@snap_tool(SubAgentName.MEMORYAGENT, args_schema=UpdatePreferenceMemoryInput)
async def update_preference_memory(content: str, config: RunnableConfig) -> dict[str, Any]:
    """Update the current agent preference memory."""
    filepath = await get_memory_workspace_path(config, ToolArtifactType.PREFERENCE_MEMORY)
    old_content = await read_file(filepath)
    await write_file(filepath, content)
    return {
        "ok": True,
        "path": str(filepath),
        "previous_empty": not bool(old_content),
    }
