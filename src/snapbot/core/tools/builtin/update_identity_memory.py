from typing import Any

from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field

from snapbot.common.utils.decorator import snap_tool
from snapbot.common.utils.file import read_file, write_file
from snapbot.core.agent.models import SubAgentName
from snapbot.core.middleware.service import get_identity_memory_path, get_memory_ids


class UpdateIdentityMemoryInput(BaseModel):
    content: str = Field(description="Full Markdown content for the user's identity memory.")


@snap_tool(SubAgentName.MEMORYAGENT, args_schema=UpdateIdentityMemoryInput)
def update_identity_memory(content: str, config: RunnableConfig) -> dict[str, Any]:
    """Update the current user's identity memory."""
    _, user_id = get_memory_ids(config)
    path = get_identity_memory_path(user_id)
    old_content = read_file(path)
    write_file(path, content)
    return {
        "ok": True,
        "path": str(path),
        "previous_empty": not bool(old_content),
    }
