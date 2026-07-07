from typing import Any

from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field

from snapbot.common.model import ToolArtifactType
from snapbot.common.utils.decorator import snap_tool
from snapbot.common.utils.file import get_memory_workspace_path, read_file, write_file
from snapbot.core.agent.models import SubAgentName


class UpdateIdentityMemoryInput(BaseModel):
    content: str = Field(description="Full Markdown content for the user's identity memory.")


@snap_tool(SubAgentName.MEMORYAGENT, args_schema=UpdateIdentityMemoryInput)
async def update_identity_memory(content: str, config: RunnableConfig) -> dict[str, Any]:
    """Update the current user's identity memory."""
    filepath = await get_memory_workspace_path(config, ToolArtifactType.IDENTITY_MEMORY)
    old_content = await read_file(filepath)
    await write_file(filepath, content)
    return {
        "ok": True,
        "path": str(filepath),
        "previous_empty": not bool(old_content),
    }
