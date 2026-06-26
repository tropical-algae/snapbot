from typing import Any

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from snapbot.common.utils.decorator import tool_meta
from snapbot.common.utils.file import read_file, write_file
from snapbot.core.agent.models import SubAgentName
from snapbot.core.middleware.service import get_memory_ids, get_preference_memory_path


class UpdatePreferenceMemoryInput(BaseModel):
    content: str = Field(description="Full updated Markdown content for the current thread's agent preference memory.")


@tool_meta(SubAgentName.MEMORYAGENT)
@tool(args_schema=UpdatePreferenceMemoryInput)
def update_preference_memory(content: str, config: RunnableConfig) -> dict[str, Any]:
    """Update the current thread's agent preference memory after reading and merging existing content."""
    thread_id, _ = get_memory_ids(config)
    path = get_preference_memory_path(thread_id)
    old_content = read_file(path)
    write_file(path, content)
    return {
        "ok": True,
        "path": str(path),
        "previous_empty": not bool(old_content),
    }
