from collections.abc import Callable
from typing import Any

from langchain_core.tools import ArgsSchema, BaseTool, tool

from snapbot.core.agent.models import SubAgentName
from snapbot.core.tools.models import ToolMeta

TOOL_META_ATTR = "__tool_meta__"


def snap_tool(
    *belong: SubAgentName,
    args_schema: ArgsSchema | None = None,
    action_message: str | None = None,
    enabled: bool = True,
) -> Callable[[Callable[..., Any]], BaseTool]:
    def decorator(func: Callable[..., Any]) -> BaseTool:
        if not belong:
            raise ValueError(f"The tool `{func.__name__}` does not have an assigned agent configured")

        base_tool = tool(args_schema=args_schema)(func)
        setattr(
            base_tool,
            TOOL_META_ATTR,
            ToolMeta(belong=frozenset(belong), action_message=action_message, enabled=enabled),
        )
        return base_tool

    return decorator
