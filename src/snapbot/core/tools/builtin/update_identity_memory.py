from typing import Any

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from snapbot.common.utils.decorator import tool_meta
from snapbot.common.utils.file import read_file, write_file
from snapbot.core.agent.models import SubAgentName
from snapbot.core.middleware.service import get_identity_memory_path, get_memory_ids


class UpdateIdentityMemoryInput(BaseModel):
    content: str = Field(description="Full updated Markdown content for the user's identity memory.")


@tool_meta(SubAgentName.MEMORYAGENT)
@tool(args_schema=UpdateIdentityMemoryInput)
def update_identity_memory(content: str, config: RunnableConfig) -> dict[str, Any]:
    """Update the current user's identity memory after reading and merging existing content."""
    _, user_id = get_memory_ids(config)
    path = get_identity_memory_path(user_id)
    old_content = read_file(path)
    write_file(path, content)
    return {
        "ok": True,
        "path": str(path),
        "previous_empty": not bool(old_content),
    }
