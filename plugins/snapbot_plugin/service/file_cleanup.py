from collections.abc import Callable
from typing import Protocol
from uuid import uuid4

from ncatbot.api import BotAPIClient
from ncatbot.event.qq import GroupMessageEvent, PrivateMessageEvent

from snapbot.common.logging import logger
from snapbot.core.tools.models import ToolArtifact, ToolArtifactKind

from ..model import SentGroupFile, SentMessageResult  # noqa: TID252


class ScheduledTaskHost(Protocol):
    def add_scheduled_task(
        self,
        name: str,
        interval: str | float,
        conditions: list[Callable[[], bool]] | None = None,
        max_runs: int | None = None,
        callback: Callable[[], object] | None = None,
    ) -> bool: ...


class SentFileCleanupService:
    def __init__(
        self,
        api: BotAPIClient,
        task_host: ScheduledTaskHost,
        delete_delay: str | float,
        enabled: bool = True,
    ) -> None:
        self.api = api
        self.task_host = task_host
        self.delete_delay = delete_delay
        self.enabled = enabled

    async def handle_sent_artifact(
        self,
        event: GroupMessageEvent | PrivateMessageEvent,
        artifact: ToolArtifact,
        result: SentMessageResult | None,
    ) -> str | None:
        if not self.enabled or not event.is_group_msg() or artifact.kind != ToolArtifactKind.FILE or result is None:
            return None

        if result.group_file is None:
            return f"文件已发送，但没有在群文件列表中追踪到 {artifact.name or artifact.path}，请手动删除。"

        return self.schedule_group_file_cleanup(result.group_file)

    def schedule_group_file_cleanup(self, file: SentGroupFile) -> str | None:
        task_name = f"snapbot_delete_group_file_{file.group_id}_{uuid4().hex}"

        async def delete_file() -> None:
            try:
                await self.api.qq.file.delete_group_file(file.group_id, file.file_id)
                logger.info(f"已删除群文件: group_id={file.group_id}, file_id={file.file_id}, name={file.name}")
            except Exception:
                logger.exception(f"删除群文件失败: group_id={file.group_id}, file_id={file.file_id}, name={file.name}")

        scheduled = self.task_host.add_scheduled_task(
            task_name,
            self.delete_delay,
            max_runs=1,
            callback=delete_file,
        )
        if not scheduled:
            logger.warning(
                "群文件删除定时任务注册失败: group_id={file.group_id}, file_id={file.file_id}, name={file.name}"
            )
            return None
        return f"注意！{self.delete_delay} 后文件将删除！"
