from collections import defaultdict

from langchain_core.tools import BaseTool

from snapbot.common.utils.decorator import TOOL_META_ATTR
from snapbot.common.utils.packages import iter_builtin_tools
from snapbot.core.agent.models import AgentName
from snapbot.core.tools.models import ToolMeta

BUILTIN_TOOLS_PACKAGE = "snapbot.core.tools.builtin"


class ToolRegistry:
    def __init__(self):
        tools, disabled_tools = self.get_all_builtin_tools()

        self.tools: dict[AgentName, list[BaseTool]] = tools
        self.disabled_tools: dict[AgentName, list[BaseTool]] = disabled_tools

    @staticmethod
    def get_tool_meta(tool: object) -> ToolMeta | None:
        meta = getattr(tool, TOOL_META_ATTR, None)
        if isinstance(meta, ToolMeta):
            return meta
        return None

    def get_all_builtin_tools(
        self,
    ) -> tuple[dict[AgentName, list[BaseTool]], dict[AgentName, list[BaseTool]]]:
        tools: dict[AgentName, list[BaseTool]] = defaultdict(list)
        disabled_tools: dict[AgentName, list[BaseTool]] = defaultdict(list)

        for tool in iter_builtin_tools(BUILTIN_TOOLS_PACKAGE):
            meta = self.get_tool_meta(tool)
            if meta is None:
                continue

            if not meta.enabled:
                for belong in meta.belong:
                    disabled_tools[belong].append(tool)
                continue

            for belong in meta.belong:
                tools[belong].append(tool)

        return tools, disabled_tools

    def get_tools(
        self,
        agent_name: AgentName,
        *,
        include_disabled: bool = False,
    ) -> list[BaseTool]:
        payload: list[BaseTool] = self.tools.get(agent_name, [])
        if include_disabled:
            payload.extend(self.disabled_tools.get(agent_name, []))

        return payload


tool_registry = ToolRegistry()
