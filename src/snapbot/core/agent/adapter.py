from collections.abc import AsyncGenerator, Iterator
from typing import Any

from ag_ui.core import CustomEvent, Event, EventType
from ag_ui_langgraph import LangGraphAgent
from ag_ui_langgraph.types import LangGraphEventTypes, State
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from snapbot.core.agent.models.event import CustomEventType, ToolArtifactEvent
from snapbot.core.tools.models import ToolArtifactOutput


class AGUIAgentAdapter(LangGraphAgent):
    @staticmethod
    def _iter_tool_messages(output: Any) -> Iterator[ToolMessage]:
        if isinstance(output, ToolMessage):
            yield output
            return

        if not isinstance(output, Command) or not isinstance(output.update, dict):
            return

        messages = output.update.get("messages", []) or []
        for message in messages:
            if isinstance(message, ToolMessage):
                yield message

    @staticmethod
    def _build_tool_artifact_event(event: Any, tool_message: ToolMessage) -> CustomEvent | None:
        artifact: ToolArtifactOutput | None = getattr(tool_message, "artifact", None)
        if artifact is None:
            return None

        return CustomEvent(
            type=EventType.CUSTOM,
            name=CustomEventType.TOOL_ARTIFACT.value,
            value=ToolArtifactEvent(
                tool_name=tool_message.name or event.get("name", ""),
                tool_call_id=tool_message.tool_call_id,
                artifact=artifact,
            ),
            raw_event=event,
        )

    async def _handle_single_event(self, event: Any, state: State) -> AsyncGenerator[Event, None]:
        async for agui_event in super()._handle_single_event(event, state):
            yield agui_event

        if event.get("event") != LangGraphEventTypes.OnToolEnd:
            return

        output = event.get("data", {}).get("output")
        for tool_message in self._iter_tool_messages(output):
            artifact_event = self._build_tool_artifact_event(event, tool_message)
            if artifact_event is not None:
                yield self._dispatch_event(artifact_event)
