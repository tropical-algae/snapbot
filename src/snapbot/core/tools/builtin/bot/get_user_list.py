from typing import cast

from langchain_core.runnables import RunnableConfig
from ncatbot.api import BotAPIClient
from ncatbot.event.qq import GroupMessageEvent, PrivateMessageEvent
from ncatbot.types.napcat.group import GroupMemberInfo

from snapbot.common.utils.decorator import snap_tool
from snapbot.core.agent.models.agent import SubAgentName


@snap_tool(SubAgentName.GROUP_OPERATOR)
async def get_group_user_list(config: RunnableConfig) -> str:
    """获取当前群组中全部用户的nickname与ID"""

    configurable: dict = config.get("configurable", {})
    api = cast(BotAPIClient | None, configurable.get("api"))
    event = cast(GroupMessageEvent | PrivateMessageEvent | None, configurable.get("event"))

    if api and event:
        member_list: list[GroupMemberInfo] = await api.qq.query.get_group_member_list(
            group_id=event.group_id,
        )
        payload = [f"[nickname: {member.nickname}][ID: {member.user_id}]" for member in member_list]
        return "\n".join(payload)
    return "未查到成员信息"
