from dataclasses import dataclass, field

from snapbot.core.agent.models import SubAgentName


@dataclass(frozen=True)
class ToolMeta:
    belong: frozenset[SubAgentName] = field(default_factory=frozenset)
    enabled: bool = True
