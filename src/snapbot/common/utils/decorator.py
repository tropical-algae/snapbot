from collections.abc import Callable
from typing import Any, get_args, get_origin, get_type_hints

from langchain_core.tools import ArgsSchema, BaseTool, tool

from snapbot.core.tools.models import AgentName, ToolMeta

TOOL_META_ATTR = "__tool_meta__"


def snap_tool(
    *belong: AgentName,
    args_schema: ArgsSchema | None = None,
    enabled: bool = True,
    produces_artifacts: bool = False,
) -> Callable[[Callable[..., Any]], BaseTool]:
    def decorator(func: Callable[..., Any]) -> BaseTool:
        if not belong:
            raise ValueError(f"The tool `{func.__name__}` does not have an assigned agent configured")

        if produces_artifacts:
            return_annotation = get_type_hints(func).get("return")
            origin = get_origin(return_annotation)
            args = get_args(return_annotation)
            if origin is not tuple or len(args) != 2:
                raise TypeError(f"The artifact tool `{func.__name__}` must return tuple[model_content, Any]")

        response_format = "content_and_artifact" if produces_artifacts else "content"
        base_tool = tool(args_schema=args_schema, response_format=response_format)(func)
        setattr(
            base_tool,
            TOOL_META_ATTR,
            ToolMeta(
                belong=frozenset(belong),
                enabled=enabled,
            ),
        )
        return base_tool

    return decorator
