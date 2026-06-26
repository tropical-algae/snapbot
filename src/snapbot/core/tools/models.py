from dataclasses import dataclass

from snapbot.core.agent.models import SubAgentName


@dataclass(frozen=True)
class ToolMeta:
    belong: frozenset[SubAgentName]
    enabled: bool = True
