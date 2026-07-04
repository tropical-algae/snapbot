from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from snapbot.core.agent.models.approval import ApprovalRequest


class AgentStreamEventType(StrEnum):
    FINAL_TEXT = "final_text"
    INTERMEDIATE_TEXT = "intermediate_text"
    TASK_START = "task_start"
    TASK_END = "task_end"
    TASK_ERROR = "task_error"
    TOOL_START = "tool_start"
    TOOL_END = "tool_end"
    TOOL_ERROR = "tool_error"
    APPROVAL_PROMPT = "approval_prompt"


@dataclass(frozen=True)
class AgentStreamEvent:
    type: AgentStreamEventType
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_text(self) -> bool:
        return False

    @property
    def is_user_visible_text(self) -> bool:
        return False


@dataclass(frozen=True)
class TextStreamEvent(AgentStreamEvent):
    delta: str = ""
    agent_name: str = ""
    node: str = ""

    @property
    def is_text(self) -> bool:
        return True


@dataclass(frozen=True)
class FinalTextStreamEvent(TextStreamEvent):
    type: AgentStreamEventType = AgentStreamEventType.FINAL_TEXT

    @property
    def is_user_visible_text(self) -> bool:
        return True


@dataclass(frozen=True)
class IntermediateTextStreamEvent(TextStreamEvent):
    type: AgentStreamEventType = AgentStreamEventType.INTERMEDIATE_TEXT


@dataclass(frozen=True)
class TaskStartStreamEvent(AgentStreamEvent):
    type: AgentStreamEventType = AgentStreamEventType.TASK_START
    description: str = ""
    subagent_type: str = ""


@dataclass(frozen=True)
class TaskEndStreamEvent(AgentStreamEvent):
    type: AgentStreamEventType = AgentStreamEventType.TASK_END
    description: str = ""
    subagent_type: str = ""
    output: Any | None = None


@dataclass(frozen=True)
class TaskErrorStreamEvent(AgentStreamEvent):
    type: AgentStreamEventType = AgentStreamEventType.TASK_ERROR
    description: str = ""
    subagent_type: str = ""
    error: str = ""


@dataclass(frozen=True)
class ToolStartStreamEvent(AgentStreamEvent):
    type: AgentStreamEventType = AgentStreamEventType.TOOL_START
    name: str = ""
    args: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ToolEndStreamEvent(AgentStreamEvent):
    type: AgentStreamEventType = AgentStreamEventType.TOOL_END
    name: str = ""
    args: dict[str, Any] = field(default_factory=dict)
    output: Any | None = None


@dataclass(frozen=True)
class ToolErrorStreamEvent(AgentStreamEvent):
    type: AgentStreamEventType = AgentStreamEventType.TOOL_ERROR
    name: str = ""
    args: dict[str, Any] = field(default_factory=dict)
    error: str = ""


@dataclass(frozen=True)
class ApprovalPromptStreamEvent(TextStreamEvent):
    type: AgentStreamEventType = AgentStreamEventType.APPROVAL_PROMPT
    approval: ApprovalRequest | None = None

    @property
    def is_user_visible_text(self) -> bool:
        return True
