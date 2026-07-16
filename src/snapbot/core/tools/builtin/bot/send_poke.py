from typing import cast

from langchain_core.runnables import RunnableConfig
from ncatbot.api import BotAPIClient
from ncatbot.event.qq import GroupMessageEvent, PrivateMessageEvent
from pydantic import BaseModel, Field

from snapbot.common.utils.decorator import snap_tool
from snapbot.core.agent.models.agent import SubAgentName


class SendPokeInput(BaseModel):
    target_user_id: str | None = Field(
        default=None,
        description="要戳一戳的用户 ID；不传时表示当前正在聊天的用户",
    )


@snap_tool(SubAgentName.GROUP_OPERATOR, args_schema=SendPokeInput)
async def send_poke(config: RunnableConfig, target_user_id: str | None = None) -> str:
    """戳一戳用户，用于提醒、催促、打招呼、逗趣互动或引起对方注意。"""
    configurable: dict = config.get("configurable", {})
    api = cast(BotAPIClient | None, configurable.get("api"))
    event = cast(GroupMessageEvent | PrivateMessageEvent | None, configurable.get("event"))

    target_user_id = target_user_id or event.user_id
    if api and event:
        await api.qq.send_poke(event.group_id, target_user_id)
        return "已完成戳一戳"
    return "未完成戳一戳"
