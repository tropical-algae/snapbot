from ncatbot.api import BotAPIClient
from ncatbot.event.qq import GroupMessageEvent

from snapbot.core.agent.models import AgentRuntimeConfig
from snapbot.core.agent.registry import AgentRegistry

from ..model import GroupConfig  # noqa: TID252
from .agent import SnapBotAgentService
from .client import send_message
from .message import build_agent_input_message


async def handle_group_agent_message(
    api: BotAPIClient,
    event: GroupMessageEvent,
    agent_service: SnapBotAgentService,
    group_config: GroupConfig,
) -> None:
    if not group_config.can_speak or not group_config.agent_enabled:
        return

    bot_info = await api.qq.query.get_login_info()
    if not event.message.is_at(bot_info.user_id, all_except=True):
        return

    config = AgentRuntimeConfig(
        thread_id=agent_service.build_session_id(event),
        user_id=str(event.user_id),
        api=api,
        event=event,
    )
    message = build_agent_input_message(event.message, bot_info.user_id)
    await agent_service.reply_agent_events(
        event,
        config,
        message,
        excluded_subagents=group_config.excluded_subagents,
        excluded_tools=group_config.excluded_tools,
    )


async def handle_reset_memory(
    api: BotAPIClient,
    event: GroupMessageEvent,
    agent_registry: AgentRegistry,
    agent_service: SnapBotAgentService,
    group_config: GroupConfig,
) -> None:
    if not group_config.can_speak:
        return

    thread_id = agent_service.build_session_id(event)
    agent_service.clear_pending_interrupt(thread_id)
    await agent_registry.remove_agent(thread_id)
    await send_message(api, event, "记忆已重置")


async def handle_test_action(api: BotAPIClient, event: GroupMessageEvent, group_config: GroupConfig) -> None:
    if not group_config.can_speak:
        return

    # await api.qq.messaging.set_msg_emoji_like(
    #     message_id=event.message_id,
    #     emoji_id="0",
    #     set=True,
    # )
    # await api.qq.send_poke(event.group_id, event.user_id)
    await api.qq.messaging.get_group_msg_history(
        group_id=event.group_id,
        message_seq=None,
        count=20,
    )
    # file_list = await api.qq.query.get_group_root_files(event.group_id)
    # for f in file_list.files or []:
    #     print(f"  📄 {f.file_name}  (ID: {f.file_id}, 大小: {f.file_size} bytes)")
    # print(f"\n\n\n\n\n\n\n\n{files}\n\n\n\n\n")
