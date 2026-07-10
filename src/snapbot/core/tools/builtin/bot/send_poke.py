from typing import cast

from langchain_core.runnables import RunnableConfig
from ncatbot.api import BotAPIClient
from ncatbot.event.qq import GroupMessageEvent, PrivateMessageEvent

from snapbot.common.utils.decorator import snap_tool
from snapbot.core.agent.models.agent import SubAgentName


@snap_tool(SubAgentName.GROUP_OPERATOR)
async def send_poke(config: RunnableConfig, target_user_id: str | None = None) -> str:
    """戳一戳用户。当 xiaoyu 需要进行以下内容的回复时：提醒、催促、打招呼、逗趣互动或引起某人注意，必须使用该工具

    Args:
        target_user_id (str | None, optional): 你要戳的对象，空值表示戳当前与你聊天的对象. Defaults to None.

    """
    configurable: dict = config.get("configurable", {})
    api = cast(BotAPIClient | None, configurable.get("api"))
    event = cast(GroupMessageEvent | PrivateMessageEvent | None, configurable.get("event"))

    target_user_id = target_user_id or event.user_id
    if api and event:
        await api.qq.send_poke(event.group_id, target_user_id)
        return "已完成戳一戳"
    return "未完成戳一戳"
