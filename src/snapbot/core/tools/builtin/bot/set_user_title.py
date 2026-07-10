from typing import cast

from langchain_core.runnables import RunnableConfig
from ncatbot.api import BotAPIClient
from ncatbot.event.qq import GroupMessageEvent, PrivateMessageEvent

from snapbot.common.utils.decorator import snap_tool
from snapbot.core.agent.models.agent import SubAgentName


@snap_tool(SubAgentName.GROUP_OPERATOR)
async def get_group_user_title(user_id: int, title_name: str, config: RunnableConfig) -> str:
    """为指定用户设置头衔

    Args:
        user_id (int): 成员的ID
        title_name (str): 要设置的头衔名
    """

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
