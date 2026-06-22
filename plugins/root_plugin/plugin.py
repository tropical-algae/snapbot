"""模板插件 — 发送 hello 回复 hi (QQ)。"""

from ncatbot.core import registrar
from ncatbot.event.qq import GroupMessageEvent, PrivateMessageEvent
from ncatbot.plugin import NcatBotPlugin


class RootPlugin(NcatBotPlugin):
    async def on_load(self) -> None:
        self.logger.info(f"{self.name} 已加载")

    async def on_close(self) -> None:
        self.logger.info(f"{self.name} 已卸载")

    @registrar.qq.on_group_command("hello", ignore_case=True)
    async def on_group_hello(self, event: GroupMessageEvent) -> None:
        await event.reply(text="hi")

    @registrar.on_private_command("hello", ignore_case=True)
    async def on_private_hello(self, event: PrivateMessageEvent) -> None:
        await event.reply(text="hi")
