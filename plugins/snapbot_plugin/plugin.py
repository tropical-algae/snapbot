from ncatbot.core import registrar
from ncatbot.event.qq import GroupMessageEvent
from ncatbot.plugin import NcatBotPlugin

from snapbot.core.agent.executor import AgentAGUIExecutor
from snapbot.core.agent.registry import AgentRegistry

from .model import SnapBotPluginConfig
from .service.agent import SnapBotAgentService
from .service.file_cleanup import SentFileCleanupService
from .service.group import handle_group_agent_message, handle_reset_memory, handle_test_action


class SnapBotPlugin(NcatBotPlugin):
    async def on_load(self) -> None:
        self.init_defaults(SnapBotPluginConfig.defaults())
        self.snapbot_config = SnapBotPluginConfig.model_validate(self.config)

        self.agent_registry = AgentRegistry()
        self.agent_adapter = AgentAGUIExecutor()
        self.sent_file_cleanup_service = SentFileCleanupService(
            self.api,
            self,
            delete_delay=self.snapbot_config.sent_file_delete_delay,
            enabled=self.snapbot_config.auto_delete_sent_files,
        )
        self.agent_service = SnapBotAgentService(
            self.api,
            self.agent_registry,
            self.agent_adapter,
            artifact_sent_handler=self.sent_file_cleanup_service.handle_sent_artifact,
        )
        await self.agent_registry.setup()

        self.logger.info(f"{self.name} 已加载")

    async def on_close(self) -> None:
        await self.agent_registry.aclose()
        self.logger.info(f"{self.name} 已卸载")

    @registrar.qq.on_group_message()
    async def on_group_at(self, event: GroupMessageEvent) -> None:
        await handle_group_agent_message(
            self.api,
            event,
            self.agent_service,
            self.snapbot_config.get_group(event.group_id),
        )

    @registrar.on_group_command("/重置记忆")
    async def on_reset_memory(self, event: GroupMessageEvent) -> None:
        await handle_reset_memory(
            self.api,
            event,
            self.agent_registry,
            self.agent_service,
            self.snapbot_config.get_group(event.group_id),
        )

    @registrar.on_group_command("/test")
    async def on_send_emoji(self, event: GroupMessageEvent) -> None:
        await handle_test_action(
            self.api,
            event,
            self.snapbot_config.get_group(event.group_id),
        )
