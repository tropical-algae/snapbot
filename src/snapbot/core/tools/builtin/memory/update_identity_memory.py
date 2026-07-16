from typing import Any

from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field

from snapbot.common.model import ToolArtifactType
from snapbot.common.utils.decorator import snap_tool
from snapbot.common.utils.file import get_memory_workspace_path, read_file, write_file
from snapbot.core.agent.models import SubAgentName


class UpdateIdentityMemoryInput(BaseModel):
    content: str = Field(description="用户身份记忆的完整 Markdown 内容")


@snap_tool(SubAgentName.MEMORY_MANAGER, args_schema=UpdateIdentityMemoryInput)
async def update_identity_memory(content: str, config: RunnableConfig) -> dict[str, Any]:
    """更新当前用户的身份记忆。"""
    filepath = await get_memory_workspace_path(config, ToolArtifactType.IDENTITY_MEMORY)
    old_content = await read_file(filepath)
    await write_file(filepath, content)
    return {
        "ok": True,
        "path": str(filepath),
        "previous_empty": not bool(old_content),
    }
