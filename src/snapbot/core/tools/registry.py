from collections import defaultdict

from langchain_core.tools import BaseTool

from snapbot.common.configs import settings
from snapbot.common.configs.tool import ToolConfig
from snapbot.common.utils.decorator import TOOL_META_ATTR
from snapbot.common.utils.packages import iter_builtin_tools
from snapbot.core.agent.models import AgentName
from snapbot.core.tools.models import ToolMeta

BUILTIN_TOOLS_PACKAGE = "snapbot.core.tools.builtin"


class ToolRegistry:
    def __init__(self):
        tools, disabled_tools, tool_metas = self._collect_all_builtin_tools()

        self.tools: dict[AgentName, list[BaseTool]] = tools
        self.disabled_tools: dict[AgentName, list[BaseTool]] = disabled_tools
        self.tool_metas: dict[str, ToolMeta] = tool_metas

    @staticmethod
    def _extract_tool_meta(tool: object) -> ToolMeta | None:
        meta = getattr(tool, TOOL_META_ATTR, None)
        if isinstance(meta, ToolMeta):
            return meta
        return None

    @staticmethod
    def _merge_tool_config(meta: ToolMeta, config: ToolConfig | None) -> ToolMeta:
        if config is None:
            return meta

        cfg_meta = config.meta
        return ToolMeta(
            belong=cfg_meta.belong if len(cfg_meta.belong) > 0 else meta.belong,
            action_message=cfg_meta.action_message or meta.action_message,
            enabled=cfg_meta.enabled if cfg_meta.enabled is not None else meta.enabled,
        )

    def _collect_all_builtin_tools(
        self,
    ) -> tuple[dict[AgentName, list[BaseTool]], dict[AgentName, list[BaseTool]], dict[str, ToolMeta]]:
        tools: dict[AgentName, list[BaseTool]] = defaultdict(list)
        disabled_tools: dict[AgentName, list[BaseTool]] = defaultdict(list)
        tool_metas: dict[str, ToolMeta] = {}

        for tool in iter_builtin_tools(BUILTIN_TOOLS_PACKAGE):
            tool_name = tool.name
            meta: ToolMeta | None = self._extract_tool_meta(tool)
            config: ToolConfig | None = settings.agent_tools.get(tool_name)

            if meta is None:
                continue

            meta = self._merge_tool_config(meta, config)
            enabled = meta.enabled if meta.enabled is not None else False
            tool_metas[tool_name] = meta

            if not enabled:
                for belong in meta.belong:
                    disabled_tools[belong].append(tool)
                continue

            for belong in meta.belong:
                tools[belong].append(tool)

        return tools, disabled_tools, tool_metas

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

    def get_action_message(self, tool_name: str) -> str | None:
        meta = self.tool_metas.get(tool_name)
        if meta is None or not meta.action_message:
            return None
        return meta.action_message


tool_registry = ToolRegistry()
