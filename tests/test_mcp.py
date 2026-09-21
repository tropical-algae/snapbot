from typing import Any

import pytest
from ag_ui.core import CustomEvent
from langchain_core.messages import ToolMessage
from langchain_core.tools import StructuredTool

from snapbot.common.configs.mcp import MCPConfig
from snapbot.common.configs.tool import ToolConfig
from snapbot.core.agent.adapter import AGUIAgentAdapter
from snapbot.core.agent.models import RootAgentName, SubAgentName
from snapbot.core.agent.models.event import CustomEventType, ToolArtifactEvent
from snapbot.core.tools.mcp import MCPClientManager, parse_mcp_tool_artifact
from snapbot.core.tools.models import MCPToolRegistration, ToolArtifactKind
from snapbot.core.tools.registry import ToolRegistry


def build_test_tool(name: str) -> StructuredTool:
    return StructuredTool.from_function(
        func=lambda query: query,
        name=name,
        description="测试工具",
    )


def test_mcp_config_parses_stdio_and_http_servers() -> None:
    config = MCPConfig.model_validate(
        {
            "servers": {
                "local": {
                    "transport": "stdio",
                    "command": "uvx",
                    "args": ["mcp-server"],
                    "belong": ["snap_agent"],
                },
                "remote": {
                    "transport": "http",
                    "url": "https://example.com/mcp",
                },
            }
        }
    )

    assert config.servers["local"].to_connection()["command"] == "uvx"
    assert config.servers["local"].belong == frozenset({RootAgentName.SNAP_AGENT})
    assert "belong" not in config.servers["local"].to_connection()
    assert config.servers["remote"].to_connection()["url"] == "https://example.com/mcp"


@pytest.mark.asyncio
async def test_mcp_client_manager_isolates_server_load_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    loaded_tool = build_test_tool("healthy_search")

    class FakeClient:
        def __init__(self, **_: Any) -> None:
            pass

        async def get_tools(self, *, server_name: str) -> list[StructuredTool]:
            if server_name == "broken":
                raise ConnectionError("unavailable")
            return [loaded_tool]

    monkeypatch.setattr("snapbot.core.tools.mcp.MultiServerMCPClient", FakeClient)
    config = MCPConfig.model_validate(
        {
            "fail_fast": False,
            "servers": {
                "broken": {"transport": "http", "url": "https://broken.example/mcp"},
                "healthy": {"transport": "http", "url": "https://example.com/mcp"},
            },
        }
    )

    registrations = await MCPClientManager(config).load_tools()

    assert [registration.tool for registration in registrations] == [loaded_tool]


@pytest.mark.asyncio
async def test_tool_registry_requires_explicit_mcp_tool_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from snapbot.core.tools import registry as registry_module

    configured_tool = build_test_tool("server_configured")
    hidden_tool = build_test_tool("server_hidden")

    class FakeManager:
        def __init__(self, _: MCPConfig) -> None:
            pass

        async def load_tools(self) -> list[MCPToolRegistration]:
            return [
                MCPToolRegistration(tool=configured_tool, belong=frozenset()),
                MCPToolRegistration(tool=hidden_tool, belong=frozenset()),
            ]

    monkeypatch.setattr(registry_module, "MCPClientManager", FakeManager)
    monkeypatch.setitem(
        registry_module.settings.agent_tools,
        configured_tool.name,
        ToolConfig.model_validate(
            {
                "meta": {
                    "enabled": True,
                    "belong": [RootAgentName.SNAP_AGENT.value],
                }
            }
        ),
    )

    registry = ToolRegistry()
    await registry.setup()
    root_tool_names = {tool.name for tool in registry.get_tools(RootAgentName.SNAP_AGENT)}

    assert configured_tool.name in root_tool_names
    assert hidden_tool.name not in root_tool_names


@pytest.mark.asyncio
async def test_server_and_tool_agent_assignments_are_additive(monkeypatch: pytest.MonkeyPatch) -> None:
    from snapbot.core.tools import registry as registry_module

    server_tool = build_test_tool("server_shared")

    class FakeManager:
        def __init__(self, _: MCPConfig) -> None:
            pass

        async def load_tools(self) -> list[MCPToolRegistration]:
            return [
                MCPToolRegistration(
                    tool=server_tool,
                    belong=frozenset({RootAgentName.SNAP_AGENT}),
                )
            ]

    monkeypatch.setattr(registry_module, "MCPClientManager", FakeManager)
    monkeypatch.setitem(
        registry_module.settings.agent_tools,
        server_tool.name,
        ToolConfig.model_validate(
            {
                "meta": {
                    "belong": [SubAgentName.MEMORY_MANAGER.value],
                }
            }
        ),
    )

    registry = ToolRegistry()
    await registry.setup()

    assert server_tool in registry.get_tools(RootAgentName.SNAP_AGENT)
    assert server_tool in registry.get_tools(SubAgentName.MEMORY_MANAGER)


def test_parse_mcp_tool_artifact() -> None:
    artifact = parse_mcp_tool_artifact(
        {
            "structured_content": {
                "artifacts": [
                    {
                        "kind": "image",
                        "path": "https://example.com/image.png",
                        "mime_type": "image/png",
                    }
                ],
                "message": "图片已生成",
            }
        }
    )

    assert artifact is not None
    assert artifact.message == "图片已生成"
    assert artifact.artifacts[0].kind == ToolArtifactKind.IMAGE
    assert parse_mcp_tool_artifact({"structured_content": {"result": 1}}) is None


def test_agui_adapter_emits_mcp_tool_artifact_event() -> None:
    tool_message = ToolMessage(
        content="图片已生成",
        tool_call_id="call-1",
        name="image_server_generate",
        artifact={
            "structured_content": {
                "artifacts": [
                    {
                        "kind": "image",
                        "path": "https://example.com/image.png",
                    }
                ]
            }
        },
    )

    event = AGUIAgentAdapter._build_tool_artifact_event(
        {"name": "image_server_generate"},
        tool_message,
    )

    assert isinstance(event, CustomEvent)
    assert event.name == CustomEventType.TOOL_ARTIFACT
    assert isinstance(event.value, ToolArtifactEvent)
    assert event.value.artifact.artifacts[0].kind == ToolArtifactKind.IMAGE
