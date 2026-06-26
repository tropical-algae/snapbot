from typing import Any

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from snapbot.common.utils.decorator import tool_meta
from snapbot.core.agent.models import SubAgentName
from snapbot.core.toolkits import tavily_client


class WebExtractInput(BaseModel):
    url: str = Field(description="The URL requested by the user for retrieval")


@tool_meta(SubAgentName.SEARCHAGENT)
@tool(args_schema=WebExtractInput)
def web_extract(
    url: str,
) -> dict[str, Any]:
    """Search the web by given URL and return structured results for research tasks."""
    try:
        result = tavily_client.extract(
            urls=url,
            format="markdown",
        )
        return {"ok": True, "result": result}
    except Exception as exc:
        return {"ok": False, "error": str(exc), "result": []}
