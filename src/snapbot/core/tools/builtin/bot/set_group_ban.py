from typing import cast

from langchain_core.runnables import RunnableConfig
from ncatbot.api import BotAPIClient
from ncatbot.event.qq import GroupMessageEvent, PrivateMessageEvent

from snapbot.common.utils.decorator import snap_tool
from snapbot.core.agent.models.agent import SubAgentName


@snap_tool(SubAgentName.GROUP_OPERATOR)
async def manage_group_ban(user_id: int, duration: int, config: RunnableConfig) -> str:
    """禁言用户 / 解除用户的禁言

    Args:
        user_id (int): 成员的ID
        duration (int): 要禁言的时间，单位为秒。设置为0时表示解除禁言
    """

    configurable: dict = config.get("configurable", {})
    api = cast(BotAPIClient | None, configurable.get("api"))
    event = cast(GroupMessageEvent | PrivateMessageEvent | None, configurable.get("event"))

    if api and event:
        await api.qq.manage.set_group_ban(group_id=event.group_id, user_id=user_id, duration=duration)
        return "已解除禁言" if duration == 0 else "已禁言"
    return "未成功执行"
