from typing import Literal

from pydantic import BaseModel, Field

from snapbot.common.utils.decorator import snap_tool
from snapbot.core.agent.models.agent import SubAgentName
from snapbot.core.toolkits.comic import jm_comic_toolkit

JmRankingTime = Literal["t", "w", "m", "a"]
JmRankingCategory = Literal[
    "0",
    "doujin",
    "single",
    "short",
    "another",
    "hanman",
    "meiman",
    "doujin_cosplay",
    "3D",
    "english_site",
]
JmRankingOrderBy = Literal["mr", "mv", "mp", "tf"]


class JmRankingInput(BaseModel):
    time: JmRankingTime = Field(default="w", description="排行榜时间范围：t=今日，w=本周，m=本月，a=全部时间")
    category: JmRankingCategory = Field(
        default="0",
        description=(
            "本子分类：0=全部，doujin=同人，single=单本，short=短篇，another=其他，hanman=韩漫，"
            "meiman=美漫，doujin_cosplay=cosplay，3D=3D，english_site=英文站"
        ),
    )
    order_by: JmRankingOrderBy = Field(
        default="mv", description="排行榜排序方式：mr=最新，mv=最多观看，mp=最多图片，tf=最多喜欢，默认采用 mv"
    )
    count: int = Field(default=3, description="查找的数量，默认找前 3 个")


@snap_tool(SubAgentName.COMIC_DOWNLOADER, args_schema=JmRankingInput)
async def get_jm_album_ranking(
    time: JmRankingTime = "w",
    category: JmRankingCategory = "0",
    order_by: JmRankingOrderBy = "mv",
    count: int = 3,
) -> list[dict[str, str]]:
    """查看 JM 本子排行榜，使用 JM API 原始排行榜参数，返回本子 ID 和标题。"""
    return [
        {
            "id": album.album_id,
            "title": album.title,
        }
        for album in await jm_comic_toolkit.ranking(
            time=time,
            category=category,
            order_by=order_by,
            max_count=count,
        )
    ]
