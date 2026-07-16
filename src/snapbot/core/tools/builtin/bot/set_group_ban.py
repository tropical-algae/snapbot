from typing import cast

from langchain_core.runnables import RunnableConfig
from ncatbot.api import BotAPIClient
from ncatbot.event.qq import GroupMessageEvent, PrivateMessageEvent
from pydantic import BaseModel, Field

from snapbot.common.utils.decorator import snap_tool
from snapbot.core.agent.models.agent import SubAgentName


class ManageGroupBanInput(BaseModel):
    user_id: int = Field(description="要操作的群成员 ID")
    duration: int = Field(ge=0, description="禁言时长，单位为秒；设为 0 表示解除禁言")


@snap_tool(SubAgentName.GROUP_OPERATOR, args_schema=ManageGroupBanInput)
async def manage_group_ban(user_id: int, duration: int, config: RunnableConfig) -> str:
    """禁言当前群聊中的指定成员，或解除其禁言。"""

    configurable: dict = config.get("configurable", {})
    api = cast(BotAPIClient | None, configurable.get("api"))
    event = cast(GroupMessageEvent | PrivateMessageEvent | None, configurable.get("event"))

    if api and event:
        await api.qq.manage.set_group_ban(group_id=event.group_id, user_id=user_id, duration=duration)
        return "已解除禁言" if duration == 0 else "已禁言"
    return "未成功执行"
