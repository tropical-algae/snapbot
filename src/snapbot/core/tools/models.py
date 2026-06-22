from dataclasses import dataclass

from snapbot.core.agent.models import AgentName


@dataclass(frozen=True)
class ToolMeta:
    belong: frozenset[AgentName]
    enabled: bool = True
