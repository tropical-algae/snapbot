from typing import Any

from pydantic import BaseModel, Field

from snapbot.common.utils.decorator import snap_tool
from snapbot.core.agent.models.agent import RootAgentName
from snapbot.core.toolkits import tavily_client


class WebExtractInput(BaseModel):
    url: str = Field(description="需要提取内容的网页 URL")


@snap_tool(RootAgentName.SNAP_AGENT, args_schema=WebExtractInput)
def web_extract(
    url: str,
) -> dict[str, Any]:
    """提取指定网页的内容，并返回适合研究任务使用的结构化结果。"""
    try:
        result = tavily_client.extract(
            urls=url,
            format="markdown",
        )
        return {"ok": True, "result": result}
    except Exception as exc:
        return {"ok": False, "error": str(exc), "result": []}
