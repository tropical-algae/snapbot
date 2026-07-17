from collections.abc import Awaitable, Callable
from typing import Any

from ag_ui.core import (
    CustomEvent,
    InputContent,
    Interrupt,
    RawEvent,
    ResumeEntry,
    RunErrorEvent,
    RunFinishedEvent,
    TextInputContent,
    TextMessageContentEvent,
    ToolCallStartEvent,
)
from ncatbot.api.client import BotAPIClient
from ncatbot.event.qq import GroupMessageEvent, PrivateMessageEvent

from snapbot.common.model import ToolArtifactType
from snapbot.common.utils.file import generate_timestamp_filename, get_thread_workspace_path
from snapbot.core.agent.executor import AgentAGUIExecutor
from snapbot.core.agent.models import AgentRuntimeConfig, RootAgentName, SubAgentName
from snapbot.core.agent.models.event import CustomEventType, ToolArtifactEvent
from snapbot.core.agent.registry import AgentRegistry
from snapbot.core.tools.models import ToolArtifact, ToolArtifactKind

from ..model import (  # noqa: TID252
    GeneratedImage,
    ImageContentBlock,
    LangChainRawEvent,
    PendingInterruptState,
    SentMessageResult,
)
from .client import send_message

# MESSAGE_END_CHARS = frozenset(("\u3002", "\uff01", "\uff1f", "!", "?", "\n"))
MESSAGE_END_CHARS = frozenset("qwoeiuqwoeiuqowieu")

ROOT_AGENT_NAMES = frozenset(agent_name.value for agent_name in RootAgentName)
SUPPRESS_FINAL_TEXT_TOOLS = ["text_to_speech"]
ArtifactSentHandler = Callable[
    [GroupMessageEvent | PrivateMessageEvent, ToolArtifact, SentMessageResult | None],
    Awaitable[str | None],
]


class SnapBotAgentService:
    def __init__(
        self,
        api: BotAPIClient,
        agent_registry: AgentRegistry,
        agent_adapter: AgentAGUIExecutor | None = None,
        artifact_sent_handler: ArtifactSentHandler | None = None,
    ) -> None:
        self.api = api
        self.agent_registry = agent_registry
        self.agent_adapter = agent_adapter or AgentAGUIExecutor()
        self.artifact_sent_handler = artifact_sent_handler
        self.pending_interrupts: dict[str, PendingInterruptState] = {}

    @staticmethod
    def build_session_id(event: GroupMessageEvent | PrivateMessageEvent) -> str:
        return f"group-{event.group_id}" if event.is_group_msg() else f"user-{event.user_id}"

    def has_pending_interrupt(self, thread_id: str) -> bool:
        return thread_id in self.pending_interrupts

    def clear_pending_interrupt(self, thread_id: str) -> None:
        self.pending_interrupts.pop(thread_id, None)

    @staticmethod
    def _get_raw_event_metadata(event: TextMessageContentEvent) -> dict[str, Any]:
        raw_event = event.raw_event
        if not isinstance(raw_event, dict):
            return {}

        metadata = raw_event.get("metadata")
        return metadata if isinstance(metadata, dict) else {}

    @classmethod
    def _is_root_text_content(cls, event: TextMessageContentEvent) -> bool:
        agent_name = cls._get_raw_event_metadata(event).get("lc_agent_name")
        if isinstance(agent_name, str) and agent_name:
            return agent_name in ROOT_AGENT_NAMES

        return True

    @staticmethod
    def _get_interrupt_allowed_decisions(interrupt: Interrupt) -> list[str]:
        metadata = interrupt.metadata or {}
        allowed_decisions = metadata.get("allowed_decisions", [])
        return allowed_decisions if isinstance(allowed_decisions, list) else []

    @classmethod
    def _build_interrupt_prompt(cls, interrupt: Interrupt, invalid: bool = False) -> str:
        allowed_decisions = cls._get_interrupt_allowed_decisions(interrupt)
        lines = [interrupt.message or "需要你的确认后才能继续。"]

        if allowed_decisions:
            lines.append("")
            lines.extend(f"{index}: {decision}" for index, decision in enumerate(allowed_decisions))
            lines.append("")
            lines.append("回复决策或编号以继续")

        prompt = "\n".join(lines)
        if invalid:
            prompt = f"决策无效, 请重新选择。\n\n{prompt}"
        return prompt

    @classmethod
    def _resolve_interrupt_decision(cls, interrupt: Interrupt, message: str) -> str | None:
        allowed_decisions = cls._get_interrupt_allowed_decisions(interrupt)
        message = message.strip()

        if not allowed_decisions:
            return message or None

        try:
            return allowed_decisions[int(message)]
        except (ValueError, IndexError):
            if message in allowed_decisions:
                return message
            return None

    async def _resolve_pending_interrupts(
        self,
        event: GroupMessageEvent | PrivateMessageEvent,
        config: AgentRuntimeConfig,
        message: str | list[InputContent],
    ) -> list[ResumeEntry] | None:
        pending = self.pending_interrupts.get(config.thread_id)
        if pending is None:
            return None

        interrupt = pending.get_next_interrupt()
        if interrupt is None:
            self.pending_interrupts.pop(config.thread_id, None)
            return []

        decision = self._resolve_interrupt_decision(interrupt, self._message_to_text(message))
        if decision is None:
            await send_message(self.api, event, self._build_interrupt_prompt(interrupt, invalid=True))
            return None

        pending.decisions.append(
            ResumeEntry(
                interrupt_id=interrupt.id,
                status="resolved",
                payload={"decision": decision},
            )
        )

        next_interrupt = pending.get_next_interrupt()
        if next_interrupt is not None:
            await send_message(self.api, event, self._build_interrupt_prompt(next_interrupt))
            return None

        self.pending_interrupts.pop(config.thread_id, None)
        return pending.decisions

    @staticmethod
    def _message_to_text(message: str | list[InputContent]) -> str:
        if isinstance(message, str):
            return message

        return "".join(content.text for content in message if isinstance(content, TextInputContent))

    async def _handle_custom_event(
        self,
        event: GroupMessageEvent | PrivateMessageEvent,
        custom_event: CustomEvent,
    ) -> None:
        if custom_event.name == CustomEventType.TOOL_ARTIFACT.value and isinstance(
            custom_event.value, ToolArtifactEvent
        ):
            for payload in custom_event.value.artifact.artifacts:
                result = await send_message(self.api, event, payload)
                if self.artifact_sent_handler is not None:
                    notice = await self.artifact_sent_handler(event, payload, result)
                    if notice:
                        await send_message(self.api, event, notice)

    @staticmethod
    def _iter_message_content_blocks(message: Any) -> list[Any]:
        if message is None:
            return []

        content_blocks = getattr(message, "content_blocks", None)
        if isinstance(content_blocks, list):
            return content_blocks

        content = getattr(message, "content", None)
        if isinstance(content, list):
            return content

        if isinstance(message, dict):
            content = message.get("content")
            return content if isinstance(content, list) else []

        return []

    @classmethod
    def _iter_generated_images(cls, raw_event: RawEvent) -> list[GeneratedImage]:
        event = LangChainRawEvent.from_raw_event(raw_event.event)
        if event is None:
            return []

        images: list[GeneratedImage] = []
        for message in (event.data.chunk, event.data.output):
            for block in cls._iter_message_content_blocks(message):
                image_block = ImageContentBlock.from_unknown(block)
                if image_block is None:
                    continue

                image = image_block.to_generated_image()
                if image is not None:
                    images.append(image)

        return images

    async def _save_generated_image(self, config: AgentRuntimeConfig, image: GeneratedImage) -> str:
        filepath = await get_thread_workspace_path(
            config=config.to_langgraph_config(),
            artifact_type=ToolArtifactType.CACHE,
            subdir="generated_images",
            filename=generate_timestamp_filename(),
            ext=image.ext,
        )
        await filepath.write_bytes(image.decode())
        return str(filepath)

    async def _save_raw_event_images(
        self,
        config: AgentRuntimeConfig,
        raw_event: RawEvent,
        sent_image_hashes: set[str],
    ) -> list[str]:
        image_paths: list[str] = []
        for image in self._iter_generated_images(raw_event):
            if image.digest in sent_image_hashes:
                continue

            sent_image_hashes.add(image.digest)
            image_path = await self._save_generated_image(config, image)
            image_paths.append(image_path)

        return image_paths

    async def _handle_run_finished(
        self,
        event: GroupMessageEvent | PrivateMessageEvent,
        config: AgentRuntimeConfig,
        stream_event: RunFinishedEvent,
    ) -> None:
        outcome = stream_event.outcome
        if outcome is None or outcome.type != "interrupt":
            return

        self.pending_interrupts[config.thread_id] = PendingInterruptState(interrupts=outcome.interrupts)
        next_interrupt = self.pending_interrupts[config.thread_id].get_next_interrupt()
        if next_interrupt is not None:
            await send_message(self.api, event, self._build_interrupt_prompt(next_interrupt))

    async def reply_agent_events(
        self,
        event: GroupMessageEvent | PrivateMessageEvent,
        config: AgentRuntimeConfig,
        message: str | list[InputContent],
        excluded_subagents: list[SubAgentName] | None = None,
        excluded_tools: list[str] | None = None,
    ) -> None:
        text_chunks: list[str] = []
        sent_image_hashes: set[str] = set()
        suppress_text = False
        resume = await self._resolve_pending_interrupts(event, config, message)
        if resume is None and config.thread_id in self.pending_interrupts:
            return

        agent = await self.agent_registry.get_agent(
            thread_id=config.thread_id,
            excluded_subagents=excluded_subagents,
            excluded_tools=excluded_tools,
        )

        async def flush_text() -> None:
            if text_chunks:
                await send_message(self.api, event, "".join(text_chunks))
                text_chunks.clear()

        async def append_text(delta: str) -> None:
            for char in delta:
                text_chunks.append(char)
                if char in MESSAGE_END_CHARS:
                    await flush_text()

        async for stream_event in self.agent_adapter.astream_agent_events(
            agent,
            config,
            message=None if resume is not None else message,
            resume=resume,
        ):
            if isinstance(stream_event, TextMessageContentEvent):
                if not suppress_text and self._is_root_text_content(stream_event):
                    await append_text(stream_event.delta)

            elif isinstance(stream_event, ToolCallStartEvent):
                if stream_event.tool_call_name in SUPPRESS_FINAL_TEXT_TOOLS:
                    suppress_text = True
                    text_chunks.clear()

            elif isinstance(stream_event, CustomEvent):
                await flush_text()
                await self._handle_custom_event(event, stream_event)

            elif isinstance(stream_event, RawEvent):
                image_paths = await self._save_raw_event_images(config, stream_event, sent_image_hashes)
                if image_paths:
                    await flush_text()
                    for image_path in image_paths:
                        await send_message(self.api, event, ToolArtifact(kind=ToolArtifactKind.IMAGE, path=image_path))

            elif isinstance(stream_event, RunErrorEvent):
                await flush_text()
                await send_message(self.api, event, f"运行失败: {stream_event.message}")

            elif isinstance(stream_event, RunFinishedEvent):
                await flush_text()
                await self._handle_run_finished(event, config, stream_event)

        await flush_text()
