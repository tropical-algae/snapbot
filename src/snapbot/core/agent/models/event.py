from enum import StrEnum
from typing import Any

from ag_ui.core import CustomEvent, Interrupt
from ag_ui_langgraph.utils import make_json_safe
from pydantic import BaseModel, ConfigDict, Field

from snapbot.core.tools.models import ToolArtifactOutput


class CustomEventType(StrEnum):
    TOOL_ARTIFACT = "tool_artifact"


class ToolArtifactEvent(BaseModel):
    tool_name: str
    tool_call_id: str
    artifact: ToolArtifactOutput


class InterruptRawEvent(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str | None = None


class InterruptActionRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str = "unknown_tool"
    description: str | None = None
    id: str | None = None
    tool_call_id: str | None = None

    @property
    def message(self) -> str:
        return self.description or f"Tool call {self.name} requires confirmation."

    @property
    def resolved_tool_call_id(self) -> str | None:
        return self.id or self.tool_call_id


class InterruptReviewConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    action_name: str
    allowed_decisions: list[str] = Field(default_factory=list)


class InterruptPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str | None = None
    action_requests: list[InterruptActionRequest] = Field(default_factory=list)
    review_configs: list[InterruptReviewConfig] = Field(default_factory=list)
    fallback_message: str = ""

    @classmethod
    def from_custom_event(cls, event: CustomEvent) -> "InterruptPayload":
        raw_event = InterruptRawEvent.model_validate(event.raw_event or {})
        if isinstance(event.value, dict):
            payload = cls.model_validate(event.value)
        else:
            payload = cls(fallback_message=str(event.value))

        if not payload.id:
            payload.id = raw_event.id or ""

        return payload

    def get_allowed_decisions(self, action_name: str) -> list[str]:
        for review_config in self.review_configs:
            if review_config.action_name == action_name:
                return review_config.allowed_decisions
        return []

    def build_response_schema(self, allowed_decisions: list[str]) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "decision": {
                    "type": "string",
                    "enum": allowed_decisions,
                },
                "editedArgs": {
                    "type": "object",
                    "description": "Full replacement of the tool arguments.",
                },
            },
            "required": ["decision"],
        }

    def to_agui_interrupts(self) -> list[Interrupt]:
        if not self.action_requests:
            return [
                Interrupt(
                    id=self.id or "",
                    reason="input_required",
                    message=self.fallback_message,
                    metadata={"value": make_json_safe(self.model_dump())},
                )
            ]

        interrupts: list[Interrupt] = []
        for index, action_request in enumerate(self.action_requests):
            allowed_decisions = self.get_allowed_decisions(action_request.name)
            interrupt_id = self.id or ""
            if len(self.action_requests) > 1:
                interrupt_id = f"{interrupt_id}:{index}"

            interrupts.append(
                Interrupt(
                    id=interrupt_id,
                    reason="tool_call",
                    message=action_request.message,
                    tool_call_id=action_request.resolved_tool_call_id,
                    response_schema=self.build_response_schema(allowed_decisions),
                    metadata={
                        "langgraph_interrupt_id": self.id or "",
                        "action_index": index,
                        "action_name": action_request.name,
                        "allowed_decisions": allowed_decisions,
                        "action_request": make_json_safe(action_request),
                    },
                )
            )

        return interrupts
