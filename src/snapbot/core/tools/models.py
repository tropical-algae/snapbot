from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from snapbot.core.agent.models import AgentName


@dataclass(frozen=True)
class ToolMeta:
    belong: frozenset[AgentName] = field(default_factory=frozenset)
    action_message: str | None = None
    enabled: bool | None = None


class ToolArtifactKind(StrEnum):
    FILE = "file"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    STICKER = "sticker"


class ToolArtifact(BaseModel):
    kind: ToolArtifactKind
    path: str
    name: str | None = None
    caption: str | None = None
    mime_type: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ToolArtifactOutput(BaseModel):
    artifacts: list[ToolArtifact]
    message: str = ""
    data: dict[str, Any] = Field(default_factory=dict)
