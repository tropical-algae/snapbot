from collections.abc import Callable
from typing import TypeVar

from snapbot.core.agent.models import AgentName
from snapbot.core.tools.models import ToolMeta

T = TypeVar("T")

TOOL_META_ATTR = "__tool_meta__"


def tool_meta(*belong: AgentName, enabled: bool = True) -> Callable[[T], T]:
    def decorator(obj: T) -> T:
        setattr(obj, TOOL_META_ATTR, ToolMeta(belong=frozenset(belong), enabled=enabled))
        return obj

    return decorator
