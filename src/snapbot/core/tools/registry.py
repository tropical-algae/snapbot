from collections import defaultdict
from collections.abc import Sequence

from langchain_core.tools import BaseTool

from snapbot.common.configs import settings
from snapbot.common.configs.tool import ToolConfig
from snapbot.common.utils.decorator import TOOL_META_ATTR
from snapbot.common.utils.packages import iter_builtin_tools
from snapbot.core.agent.models import AgentName
from snapbot.core.tools.mcp import MCPClientManager
from snapbot.core.tools.models import ToolMeta

BUILTIN_TOOLS_PACKAGE = "snapbot.core.tools.builtin"


class ToolRegistry:
    def __init__(self):
        self._builtin_tools = list(iter_builtin_tools(BUILTIN_TOOLS_PACKAGE))
        self.mcp_client_manager: MCPClientManager | None = None
        self._mcp_initialized = False

        self.tools: dict[AgentName, list[BaseTool]] = defaultdict(list)
        self.disabled_tools: dict[AgentName, list[BaseTool]] = defaultdict(list)
        self.tool_metas: dict[str, ToolMeta] = {}
        builtin_registrations = [(tool, self._extract_tool_meta(tool)) for tool in self._builtin_tools]
        self._register_tools(builtin_registrations)

    @staticmethod
    def _extract_tool_meta(tool: object) -> ToolMeta | None:
        meta = getattr(tool, TOOL_META_ATTR, None)
        if isinstance(meta, ToolMeta):
            return meta
        return None

    @staticmethod
    def _merge_tool_config(
        meta: ToolMeta,
        config: ToolConfig | None,
        *,
        additive_belong: bool = False,
    ) -> ToolMeta:
        if config is None:
            return meta

        cfg_meta = config.meta
        belong = meta.belong
        if cfg_meta.belong:
            belong = meta.belong | cfg_meta.belong if additive_belong else cfg_meta.belong

        return ToolMeta(
            belong=belong,
            enabled=cfg_meta.enabled if cfg_meta.enabled is not None else meta.enabled,
        )

    def _register_tools(
        self,
        tool_registrations: Sequence[tuple[BaseTool, ToolMeta | None]],
        *,
        additive_belong: bool = False,
    ) -> None:
        registrations: list[tuple[BaseTool, ToolMeta, bool]] = []
        registered_names = set(self.tool_metas)

        for tool, meta in tool_registrations:
            tool_name = tool.name
            config: ToolConfig | None = settings.agent_tools.get(tool_name)

            if meta is None:
                continue

            if tool_name in registered_names:
                raise ValueError(f"Duplicate tool name: {tool_name}")

            meta = meta or ToolMeta(enabled=False)
            meta = self._merge_tool_config(meta, config, additive_belong=additive_belong)
            enabled = meta.enabled if meta.enabled is not None else False
            if enabled and not meta.belong:
                raise ValueError(f"Enabled tool `{tool_name}` does not belong to any agent")

            registered_names.add(tool_name)
            registrations.append((tool, meta, enabled))

        for tool, meta, enabled in registrations:
            tool_name = tool.name
            self.tool_metas[tool_name] = meta

            if not enabled:
                for belong in meta.belong:
                    self.disabled_tools[belong].append(tool)
                continue

            for belong in meta.belong:
                self.tools[belong].append(tool)

    async def setup(self) -> None:
        if self._mcp_initialized:
            return

        manager = MCPClientManager(settings.mcp)
        mcp_tools = await manager.load_tools()
        mcp_registrations = [
            (
                registration.tool,
                ToolMeta(
                    belong=registration.belong,
                    enabled=bool(registration.belong),
                ),
            )
            for registration in mcp_tools
        ]
        self._register_tools(mcp_registrations, additive_belong=True)
        self.mcp_client_manager = manager
        self._mcp_initialized = True

    def get_tools(
        self,
        agent_name: AgentName,
        *,
        include_disabled: bool = False,
        excluded_tools: list[str] | None = None,
    ) -> list[BaseTool]:
        payload: list[BaseTool] = list(self.tools.get(agent_name, []))
        if include_disabled:
            payload.extend(self.disabled_tools.get(agent_name, []))

        if excluded_tools:
            excluded_tool_names = set(excluded_tools)
            payload = [tool for tool in payload if tool.name not in excluded_tool_names]

        return payload


tool_registry = ToolRegistry()
