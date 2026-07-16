from typing import cast

from langchain_core.runnables import RunnableConfig
from ncatbot.api import BotAPIClient
from ncatbot.event.qq import GroupMessageEvent, PrivateMessageEvent
from ncatbot.types.napcat.group import GroupMemberInfo
from pydantic import BaseModel, Field

from snapbot.common.utils.decorator import snap_tool
from snapbot.core.agent.models.agent import SubAgentName


class GetGroupUserInfoInput(BaseModel):
    user_id: int = Field(description="要查询的群成员 ID")


@snap_tool(SubAgentName.GROUP_OPERATOR, args_schema=GetGroupUserInfoInput)
async def get_group_user_info(user_id: int, config: RunnableConfig) -> str:
    """通过用户 ID 获取当前群聊中指定成员的信息。"""

    configurable: dict = config.get("configurable", {})
    api = cast(BotAPIClient | None, configurable.get("api"))
    event = cast(GroupMessageEvent | PrivateMessageEvent | None, configurable.get("event"))

    if api and event:
        member_info: GroupMemberInfo = await api.qq.query.get_group_member_info(
            group_id=event.group_id, user_id=user_id
        )
        return str(member_info.model_dump_json())
    return "未查到成员信息"
