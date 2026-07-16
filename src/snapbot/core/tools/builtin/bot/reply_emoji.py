from typing import Literal, cast

from langchain_core.runnables import RunnableConfig
from ncatbot.api import BotAPIClient
from ncatbot.event.qq import GroupMessageEvent, PrivateMessageEvent
from pydantic import BaseModel, Field

from snapbot.common.utils.decorator import snap_tool
from snapbot.core.agent.models.agent import SubAgentName


class ReplyEmojiInput(BaseModel):
    emoji_id: Literal[0, 1, 2, 3, 4, 5, 6, 7, 8, 9] = Field(
        default=0,
        description=(
            "要发送的表情 ID：0=微笑，1=撇嘴，2=好色，3=发呆，4=得意，5=流泪，6=害羞，7=闭嘴，8=困倦，9=大哭"
        ),
    )


@snap_tool(SubAgentName.GROUP_OPERATOR, args_schema=ReplyEmojiInput)
async def reply_emoji(config: RunnableConfig, emoji_id: Literal[0, 1, 2, 3, 4, 5, 6, 7, 8, 9] = 0) -> str:
    """向当前消息发送一个表情回应。"""
    configurable: dict = config.get("configurable", {})
    api = cast(BotAPIClient | None, configurable.get("api"))
    event = cast(GroupMessageEvent | PrivateMessageEvent | None, configurable.get("event"))

    if api and event:
        await api.qq.messaging.set_msg_emoji_like(
            message_id=event.message_id,
            emoji_id=str(emoji_id),  # 表情 ID
        )
        return "已发送表情"
    return "表情未发送"
