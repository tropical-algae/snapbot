from typing import Any, Literal

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from snapbot.common.utils.decorator import tool_meta
from snapbot.core.agent.models import AgentName
from snapbot.core.toolkits import tavily_client


class WebSearchInput(BaseModel):
    query: str = Field(
        description="Precise search query. Include entities, constraints, and date context when relevant."
    )
    max_results: int = Field(default=5, ge=1, le=10, description="Maximum number of search results to return.")
    topic: Literal["general", "news", "finance"] = Field(
        default="general",
        description="Search vertical. Use news for current events and finance for markets or companies.",
    )
    include_raw_content: bool = Field(
        default=False,
        description="Whether to include raw page content snippets when Tavily supports it.",
    )


@tool_meta(AgentName.SEARCHAGENT)
@tool(args_schema=WebSearchInput)
def web_search(
    query: str,
    max_results: int = 5,
    topic: Literal["general", "news", "finance"] = "general",
    include_raw_content: bool = False,
) -> dict[str, Any]:
    """Search the web by query and return structured results for research tasks."""
    try:
        result = tavily_client.search(
            query=query,
            max_results=max_results,
            include_raw_content=include_raw_content,
            topic=topic,
        )
        return {"ok": True, "result": result}
    except Exception as exc:
        return {"ok": False, "error": str(exc), "result": []}
