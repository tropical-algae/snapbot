from collections.abc import AsyncGenerator, Iterator
from typing import Any

from langchain.messages import ToolMessage
from langgraph.graph.state import Command, CompiledStateGraph

from snapbot.core.agent.models import (
    AgentRuntimeConfig,
    AgentStreamEvent,
    ApprovalPromptStreamEvent,
    ApprovalRequest,
    ApprovalStatus,
    FinalTextStreamEvent,
    IntermediateTextStreamEvent,
    RootAgentName,
    TaskEndStreamEvent,
    TaskErrorStreamEvent,
    TaskStartStreamEvent,
    TextStreamEvent,
    ToolEndStreamEvent,
    ToolErrorStreamEvent,
    ToolStartStreamEvent,
)
from snapbot.core.agent.service import build_user_message_payload, get_agent_approval_requests, get_agent_interrupt
from snapbot.core.tools.models import ToolArtifactOutput
from snapbot.core.tools.registry import tool_registry


class AgentExecutor:
    def __init__(self):
        self.approval_status: dict[str, ApprovalStatus] = {}

    def get_approval_status(self, thread_id: str) -> ApprovalStatus:
        approval_status = self.approval_status.get(thread_id)
        if approval_status is None:
            approval_status = ApprovalStatus(approvals=[], decisions=[])
            self.approval_status[thread_id] = approval_status
        return approval_status

    @staticmethod
    def _build_metadata(event: dict[str, Any]) -> dict[str, Any]:
        metadata = event.get("metadata") or {}
        return {
            "name": event.get("name", ""),
            "run_id": event.get("run_id", ""),
            "parent_ids": event.get("parent_ids", []),
            "tags": event.get("tags", []),
            "langgraph_node": metadata.get("langgraph_node", ""),
            "metadata": metadata,
        }

    @staticmethod
    def _get_metadata_value(metadata: dict[str, Any], key: str) -> str:
        value = metadata.get("metadata", {}).get(key, "")
        return value if isinstance(value, str) else ""

    @classmethod
    def _get_agent_name(cls, metadata: dict[str, Any]) -> str:
        return cls._get_metadata_value(metadata, "lc_agent_name")

    @classmethod
    def _build_text_event(cls, delta: str, metadata: dict[str, Any]) -> TextStreamEvent:
        agent_name = cls._get_agent_name(metadata)
        node = str(metadata.get("langgraph_node", ""))
        payload = {
            "delta": delta,
            "agent_name": agent_name,
            "node": node,
            "metadata": metadata,
        }
        if agent_name in RootAgentName:
            return FinalTextStreamEvent(**payload)
        return IntermediateTextStreamEvent(**payload)

    @staticmethod
    def _normalize_tool_args(tool_input: Any) -> dict[str, Any]:
        if isinstance(tool_input, dict):
            return tool_input
        if tool_input is None:
            return {}
        return {"input": tool_input}

    @staticmethod
    def _iter_content_chars(content: Any) -> Iterator[str]:
        if isinstance(content, str):
            yield from content
            return

        if not isinstance(content, list):
            return

        for item in content:
            if isinstance(item, str):
                yield from item
            elif isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    yield from text

    @staticmethod
    def _has_tool_call(chunk: Any) -> bool:
        return bool(
            getattr(chunk, "tool_calls", None)
            or getattr(chunk, "tool_call_chunks", None)
            or getattr(chunk, "invalid_tool_calls", None)
        )

    @staticmethod
    def _iter_approval_prompt_events(approval: ApprovalRequest, prompt: str) -> Iterator[AgentStreamEvent]:
        for char in prompt:
            yield ApprovalPromptStreamEvent(delta=char, approval=approval)

    async def _astream_agent_events(
        self, agent: CompiledStateGraph, config: AgentRuntimeConfig, payload: dict | Command
    ) -> AsyncGenerator[AgentStreamEvent, None]:
        async for event in agent.astream_events(payload, config=config.to_langgraph_config(), version="v2"):
            kind = event["event"]
            data = event.get("data") or {}
            metadata = self._build_metadata(event)

            if kind == "on_tool_start":
                tool_name = event["name"]
                tool_args = self._normalize_tool_args(data.get("input"))
                if tool_name == "task":
                    yield TaskStartStreamEvent(
                        description=str(tool_args.get("description", "")),
                        subagent_type=str(tool_args.get("subagent_type", "")),
                        metadata=metadata,
                    )
                else:
                    yield ToolStartStreamEvent(
                        name=tool_name,
                        args=tool_args,
                        action_message=tool_registry.get_action_message(tool_name),
                        metadata=metadata,
                    )

            elif kind == "on_tool_end":
                tool_name = event["name"]
                tool_args = self._normalize_tool_args(data.get("input"))
                tool_output: ToolMessage = data.get("output")

                if tool_name == "task":
                    yield TaskEndStreamEvent(
                        description=str(tool_args.get("description", "")),
                        subagent_type=str(tool_args.get("subagent_type", "")),
                        output=tool_output,
                        metadata=metadata,
                    )
                else:
                    artifact: ToolArtifactOutput | None = tool_output.artifact
                    yield ToolEndStreamEvent(
                        name=tool_name,
                        args=tool_args,
                        output=tool_output,
                        metadata=metadata,
                        artifacts=[] if artifact is None else artifact.artifacts,
                    )

            elif kind == "on_tool_error":
                tool_name = event["name"]
                tool_args = self._normalize_tool_args(data.get("input"))
                error = str(data.get("error", ""))
                if tool_name == "task":
                    yield TaskErrorStreamEvent(
                        description=str(tool_args.get("description", "")),
                        subagent_type=str(tool_args.get("subagent_type", "")),
                        error=error,
                        metadata=metadata,
                    )
                else:
                    yield ToolErrorStreamEvent(name=tool_name, args=tool_args, error=error, metadata=metadata)

            elif kind == "on_chat_model_stream":
                chunk = data.get("chunk")
                if chunk is None or self._has_tool_call(chunk):
                    continue

                for char in self._iter_content_chars(getattr(chunk, "content", "")):
                    yield self._build_text_event(char, metadata)

    async def astream_agent_events(
        self,
        agent: CompiledStateGraph,
        config: AgentRuntimeConfig,
        message: str,
    ) -> AsyncGenerator[AgentStreamEvent, None]:
        thread_id = config.thread_id
        approval_status = self.get_approval_status(thread_id)

        payload: Command | dict = build_user_message_payload(message)

        if approval_status.is_opened:
            decision = approval_status.resolve_next_decision(message)

            if decision and not approval_status.is_opened:
                payload = approval_status.get_approval_command()

            else:
                next_approval = approval_status.get_next_approval()
                if next_approval is None:
                    return

                prompt = approval_status.get_next_approval_desc() or "Something is wrong here."
                if not decision:
                    prompt = f"审批决策无效, 请重新选择.\n\n{prompt}"

                for approval_event in self._iter_approval_prompt_events(next_approval, prompt):
                    yield approval_event
                return

        async for text in self._astream_agent_events(agent, config, payload):
            yield text

        approval_requests = get_agent_approval_requests(await get_agent_interrupt(agent, config))

        if approval_requests:
            approval_status.set_approvals(approval_requests)
            next_approval = approval_status.get_next_approval()
            if next_approval is None:
                return

            prompt = approval_status.get_next_approval_desc() or "Something is wrong here."
            for approval_event in self._iter_approval_prompt_events(next_approval, prompt):
                yield approval_event
