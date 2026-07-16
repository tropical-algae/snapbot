from typing import Any

from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field

from snapbot.common.model import ToolArtifactType
from snapbot.common.utils.decorator import snap_tool
from snapbot.common.utils.file import get_memory_workspace_path, read_file, write_file
from snapbot.core.agent.models import SubAgentName


class UpdatePreferenceMemoryInput(BaseModel):
    content: str = Field(description="当前会话对 Agent 偏好记忆的完整 Markdown 内容")


@snap_tool(SubAgentName.MEMORY_MANAGER, args_schema=UpdatePreferenceMemoryInput)
async def update_preference_memory(content: str, config: RunnableConfig) -> dict[str, Any]:
    """更新当前会话对 Agent 的偏好记忆。"""
    filepath = await get_memory_workspace_path(config, ToolArtifactType.PREFERENCE_MEMORY)
    old_content = await read_file(filepath)
    await write_file(filepath, content)
    return {
        "ok": True,
        "path": str(filepath),
        "previous_empty": not bool(old_content),
    }
