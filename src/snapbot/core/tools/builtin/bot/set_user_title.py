from typing import cast

from langchain_core.runnables import RunnableConfig
from ncatbot.api import BotAPIClient
from ncatbot.event.qq import GroupMessageEvent, PrivateMessageEvent
from pydantic import BaseModel, Field

from snapbot.common.utils.decorator import snap_tool
from snapbot.core.agent.models.agent import SubAgentName


class SetGroupUserTitleInput(BaseModel):
    user_id: int = Field(description="要设置头衔的群成员 ID")
    title_name: str = Field(description="要设置的群头衔名称")


@snap_tool(SubAgentName.GROUP_OPERATOR, args_schema=SetGroupUserTitleInput)
async def get_group_user_title(user_id: int, title_name: str, config: RunnableConfig) -> str:
    """为当前群聊中的指定成员设置群头衔。"""

    configurable: dict = config.get("configurable", {})
    api = cast(BotAPIClient | None, configurable.get("api"))
    event = cast(GroupMessageEvent | PrivateMessageEvent | None, configurable.get("event"))

    if api and event:
        await api.qq.manage.set_group_special_title(
            group_id=event.group_id,
            user_id=user_id,
            special_title=title_name,
        )
        return "已成功设置"
    return "未成功设置"
