from __future__ import annotations

from typing import Any, cast

from langchain_core.runnables import RunnableConfig
from ncatbot.api import BotAPIClient
from ncatbot.event.qq import GroupMessageEvent, PrivateMessageEvent
from ncatbot.types.napcat import MessageData
from pydantic import BaseModel, Field

from snapbot.common.utils.decorator import snap_tool
from snapbot.core.agent.models.agent import SubAgentName


class CollectGroupHistoryInput(BaseModel):
    number: int = Field(description="要读取的群聊历史消息条数，通常建议读取 1 至 10 条")


@snap_tool(SubAgentName.GROUP_OPERATOR, args_schema=CollectGroupHistoryInput)
async def collect_group_history(number: int, config: RunnableConfig) -> list[dict[str, Any]] | str:
    """读取当前群聊的历史消息记录。"""
    configurable: dict = config.get("configurable", {})
    api = cast(BotAPIClient | None, configurable.get("api"))
    event = cast(GroupMessageEvent | PrivateMessageEvent | None, configurable.get("event"))
    if api and event:
        history = await api.qq.messaging.get_group_msg_history(
            group_id=event.group_id,
            message_seq=None,
            count=number,
        )
        messages: list[MessageData] = history.messages
        payload = []

        for message in messages:
            sender = message.sender.nickname
            for content in message.message:
                if content.get("type", None) == "text":
                    text = cast(dict, content.get("data", {})).get("text", "")
                    if text:
                        payload.append({"type": "text", "text": f"Sender [{sender}]: {text}"})
                if content.get("type", None) == "image":
                    image_url = cast(dict, content.get("data", {})).get("url", "")
                    if image_url:
                        payload.append({"type": "image", "url": image_url})
        if payload:
            return payload
    return "未能读取群聊历史消息。"
