from ncatbot.core import registrar
from ncatbot.event.qq import GroupMessageEvent, PrivateMessageEvent
from ncatbot.plugin import NcatBotPlugin

from snapbot.core.agent.executor import AgentExecutor
from snapbot.core.agent.models import AgentRuntimeConfig
from snapbot.core.agent.registry import AgentRegistry


class SnapBotPlugin(NcatBotPlugin):
    async def on_load(self) -> None:
        self.agent_registry = AgentRegistry()
        self.agent_executor = AgentExecutor()
        await self.agent_registry.setup()

        self.set_config("prefix", "/")
        self.logger.info(f"{self.name} 已加载")

    async def on_close(self) -> None:
        await self.agent_registry.aclose()
        self.logger.info(f"{self.name} 已卸载")

    @staticmethod
    def build_session_id(event: GroupMessageEvent | PrivateMessageEvent) -> str:
        return f"group-{event.group_id}" if event.is_group_msg() else f"user-{event.user_id}"

    @registrar.qq.on_group_message()
    async def on_group_at(self, event: GroupMessageEvent) -> None:
        bot_info = await self.api.qq.query.get_login_info()
        at = [a for a in event.message.filter_at() if a.user_id == bot_info.user_id]
        if self.agent_registry and len(at) > 0:
            thread_id = self.build_session_id(event)
            config = AgentRuntimeConfig(thread_id=thread_id, user_id=str(event.user_id))
            message: str = "\n".join(msg.text for msg in event.message.filter_text())
            agent = await self.agent_registry.get_agent(thread_id=thread_id)
            async for text in self.agent_executor.astream_agent_events(agent, config, message):
                await self.api.qq.post_group_msg(event.group_id, text=text)

    @registrar.on_group_command("小鱼")
    async def on_group_chat(self, event: GroupMessageEvent) -> None:
        if self.agent_registry:
            thread_id = self.build_session_id(event)
            config = AgentRuntimeConfig(thread_id=thread_id, user_id=str(event.user_id))
            message: str = "\n".join(msg.text for msg in event.message.filter_text())
            message = message.lstrip("小鱼").lstrip()
            agent = await self.agent_registry.get_agent(thread_id=thread_id)
            async for text in self.agent_executor.astream_agent_events(agent, config, message):
                await self.api.qq.post_group_msg(event.group_id, text=text)

    @registrar.on_group_command("重置记忆")
    async def on_reset_memory(self, event: GroupMessageEvent) -> None:
        thread_id = self.build_session_id(event)
        await self.agent_registry.remove_agent(thread_id)
        await event.reply(text="记忆已重置")

    @registrar.on_private_command("小鱼")
    async def on_private_chat(self, event: PrivateMessageEvent, message: str) -> None:
        await event.reply(text=message)

    # @registrar.on_group_command("小鱼")
    # async def on_set_prefix(self, event: GroupMessageEvent, message: str):
    #     await event.reply(text=message)
