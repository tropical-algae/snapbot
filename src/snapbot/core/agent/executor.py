import json
from collections.abc import AsyncGenerator
from typing import Any
from uuid import uuid4

from ag_ui.core import (
    CustomEvent,
    Event,
    EventType,
    InputContent,
    Interrupt,
    ResumeEntry,
    RunAgentInput,
    RunFinishedEvent,
    RunFinishedInterruptOutcome,
    UserMessage,
)
from ag_ui_langgraph.types import LangGraphEventTypes
from ag_ui_langgraph.utils import make_json_safe
from langgraph.graph.state import CompiledStateGraph

from snapbot.common.configs import settings
from snapbot.common.logging import logger
from snapbot.common.model import ToolArtifactType
from snapbot.common.utils.file import generate_timestamp_filename, get_thread_workspace_path, write_file
from snapbot.core.agent.adapter import AGUIAgentAdapter
from snapbot.core.agent.models import (
    AgentRuntimeConfig,
    RootAgentName,
)
from snapbot.core.agent.models.event import InterruptPayload

EVENT_HISTORY_SUBDIR = "agent_events"


class AgentAGUIExecutor:
    def __init__(self, name: str = RootAgentName.SNAP_AGENT.value) -> None:
        self.name = name

    def build_agent(self, agent: CompiledStateGraph, config: AgentRuntimeConfig) -> AGUIAgentAdapter:
        return AGUIAgentAdapter(
            name=self.name,
            graph=agent,
            config=config.to_langgraph_config(),
        )

    @staticmethod
    def _build_decision_resume_payload(resume: list[ResumeEntry]) -> dict[str, Any]:
        decisions: list[dict[str, Any]] = []
        for entry in resume:
            if entry.status == "cancelled":
                decisions.append({"type": "reject"})
                continue

            payload = entry.payload
            if isinstance(payload, dict):
                decision = payload.get("decision") or payload.get("type")
                if decision:
                    item = {"type": decision}
                    edited_args = payload.get("edited_args") or payload.get("editedArgs")
                    if edited_args:
                        item["edited_args"] = edited_args
                    decisions.append(item)

        return {"decisions": decisions}

    @staticmethod
    def _build_standard_interrupts(event: CustomEvent) -> list[Interrupt]:
        return InterruptPayload.from_custom_event(event).to_agui_interrupts()

    @staticmethod
    async def _save_event_history(config: AgentRuntimeConfig, events: list[dict[str, Any]]) -> None:
        if settings.log.debug:
            filepath = await get_thread_workspace_path(
                config=config.to_langgraph_config(),
                artifact_type=ToolArtifactType.HISTORY,
                subdir=EVENT_HISTORY_SUBDIR,
                filename=generate_timestamp_filename("json"),
            )
            content = "[\n"
            content += ",\n".join(json.dumps(event, ensure_ascii=False) for event in events)
            content += "\n]\n"
            await write_file(filepath, content)

    @classmethod
    def build_input(
        cls,
        config: AgentRuntimeConfig,
        message: str | list[InputContent] | None = None,
        resume: list[ResumeEntry] | None = None,
        **kwargs: Any,
    ) -> RunAgentInput:
        forwarded_props: dict[str, Any] = {}
        messages = []
        state = kwargs.get("state", {})
        tools = kwargs.get("tools", [])
        context = kwargs.get("context", [])

        if resume:
            forwarded_props["command"] = {
                "resume": cls._build_decision_resume_payload(resume),
            }
        elif message is not None:
            messages.append(
                UserMessage(
                    id=str(uuid4()),
                    role="user",
                    content=message,
                )
            )

        return RunAgentInput(
            thread_id=config.thread_id,
            run_id=str(uuid4()),
            state=state,
            messages=messages,
            tools=tools,
            context=context,
            forwarded_props=forwarded_props,
            resume=resume,
        )

    async def astream_agent_events(
        self,
        agent: CompiledStateGraph,
        config: AgentRuntimeConfig,
        message: str | list[InputContent] | None = None,
        resume: list[ResumeEntry] | None = None,
        **kwargs: Any,
    ) -> AsyncGenerator[Event, None]:
        agui_agent = self.build_agent(agent, config)
        agui_input = self.build_input(config, message, resume, **kwargs)
        pending_interrupts: list[Interrupt] = []
        recorded_events: list[dict[str, Any]] = []

        try:
            async for event in agui_agent.run(agui_input):
                if isinstance(event, CustomEvent) and event.name == LangGraphEventTypes.OnInterrupt.value:
                    pending_interrupts.extend(self._build_standard_interrupts(event))
                    continue

                if isinstance(event, RunFinishedEvent) and pending_interrupts:
                    event = RunFinishedEvent(
                        type=EventType.RUN_FINISHED,
                        thread_id=event.thread_id,
                        run_id=event.run_id,
                        result=event.result,
                        outcome=RunFinishedInterruptOutcome(interrupts=pending_interrupts),
                        raw_event=event.raw_event,
                    )

                recorded_events.append(make_json_safe(event.model_dump(by_alias=True, exclude_none=True)))
                yield event

        finally:
            try:
                await self._save_event_history(config, recorded_events)
            except Exception as exc:
                logger.warning(f"Failed to save agent event history: {exc}")
