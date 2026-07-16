from typing import Any, Literal

from pydantic import BaseModel, Field

from snapbot.common.utils.decorator import snap_tool
from snapbot.core.agent.models.agent import RootAgentName
from snapbot.core.toolkits import tavily_client


class WebSearchInput(BaseModel):
    query: str = Field(description="精确的搜索词；必要时应包含实体、限制条件和日期信息")
    max_results: int = Field(default=5, ge=1, le=10, description="最多返回的搜索结果数量")
    topic: Literal["general", "news", "finance"] = Field(
        default="general",
        description="搜索领域：general=通用，news=时事新闻，finance=市场或公司财经信息",
    )
    include_raw_content: bool = Field(
        default=False,
        description="当 Tavily 支持时，是否包含网页原始内容片段",
    )


@snap_tool(RootAgentName.SNAP_AGENT, args_schema=WebSearchInput)
def web_search(
    query: str,
    max_results: int = 5,
    topic: Literal["general", "news", "finance"] = "general",
    include_raw_content: bool = False,
) -> dict[str, Any]:
    """根据搜索词检索网页，并返回适合研究任务使用的结构化结果。"""
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
