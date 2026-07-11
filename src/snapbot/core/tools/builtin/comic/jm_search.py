from pydantic import BaseModel, Field

from snapbot.common.utils.decorator import snap_tool
from snapbot.core.agent.models import RootAgentName
from snapbot.core.toolkits.comic import jm_comic_toolkit


class JmSearchInput(BaseModel):
    keyword: str = Field(description="用于搜索 JM 本子的关键词。只搜索第一页结果。")


@snap_tool(RootAgentName.SNAP_AGENT, args_schema=JmSearchInput)
async def search_jm_album(keyword: str) -> list[dict[str, str]]:
    """根据关键词搜索 JM 本子，返回结果中的本子 ID 和标题。"""
    return [
        {
            "id": album.album_id,
            "title": album.title,
        }
        for album in await jm_comic_toolkit.search_albums(keyword)
    ]
