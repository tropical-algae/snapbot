from typing import Literal

from pydantic import BaseModel, Field

from snapbot.common.utils.decorator import snap_tool
from snapbot.core.agent.models import RootAgentName
from snapbot.core.toolkits.comic import JM_CATEGORY_VALUES, JM_ORDER_BY_VALUES, JM_TIME_VALUES, jm_comic_toolkit

JmRankingTime = Literal["all", "today", "week", "month"]
JmRankingCategory = Literal[
    "all",
    "doujin",
    "single",
    "short",
    "another",
    "hanman",
    "meiman",
    "doujin_cosplay",
    "3d",
    "english_site",
]
JmRankingOrderBy = Literal["latest", "view", "picture", "like", "comment", "score"]


class JmRankingInput(BaseModel):
    time: JmRankingTime = Field(
        default="week",
        description="排行榜时间范围。可选值: all 全部、today 今日、week 本周、month 本月。",
    )
    category: JmRankingCategory = Field(
        default="all",
        description=(
            "本子分类。可选值: all 全部、doujin 同人、single 单行本、short 短篇、another 其他、"
            "hanman 韩漫、meiman 美漫、doujin_cosplay Cosplay、3d 3D、english_site 英文站。"
        ),
    )
    order_by: JmRankingOrderBy = Field(
        default="view",
        description="排行榜排序方式。可选值: latest 最新、view 浏览、picture 图片数、like 喜欢、comment 评论、score 评分。",
    )
    max_count: int = Field(default=3, description="返回的最大数量，若未指定则默认为3")


@snap_tool(RootAgentName.SNAP_AGENT, args_schema=JmRankingInput)
async def get_jm_album_ranking(
    time: JmRankingTime = "week",
    category: JmRankingCategory = "all",
    order_by: JmRankingOrderBy = "view",
    max_count: int = 3,
) -> list[dict[str, str]]:
    """查看 JM 本子排行榜，返回本子 ID 和标题。"""
    return [
        {
            "id": album.album_id,
            "title": album.title,
        }
        for album in await jm_comic_toolkit.ranking(
            time=JM_TIME_VALUES[time],
            category=JM_CATEGORY_VALUES[category],
            order_by=JM_ORDER_BY_VALUES[order_by],
            max_count=max_count,
        )
    ]
