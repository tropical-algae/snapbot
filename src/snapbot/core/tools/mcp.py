from typing import Any, cast

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.sessions import Connection

from snapbot.common.configs.mcp import MCPConfig
from snapbot.common.logging import logger
from snapbot.core.tools.models import MCPToolRegistration, ToolArtifactOutput


def parse_mcp_tool_artifact(artifact: Any) -> ToolArtifactOutput | None:
    if isinstance(artifact, ToolArtifactOutput):
        return artifact
    if not isinstance(artifact, dict):
        return None

    payload = artifact.get("structured_content", artifact)
    if not isinstance(payload, dict):
        return None

    try:
        return ToolArtifactOutput.model_validate(payload)
    except ValueError:
        return None


class MCPClientManager:
    def __init__(self, config: MCPConfig) -> None:
        self.config = config
        self.client: MultiServerMCPClient | None = None

    async def load_tools(self) -> list[MCPToolRegistration]:
        if not self.config.enabled:
            return []

        connections = {
            name: cast(Connection, server.to_connection())
            for name, server in self.config.servers.items()
            if server.enabled
        }
        if not connections:
            return []

        self.client = MultiServerMCPClient(
            connections=connections,
            tool_name_prefix=self.config.tool_name_prefix,
            handle_tool_errors=self.config.handle_tool_errors,
        )

        registrations: list[MCPToolRegistration] = []
        for server_name in connections:
            try:
                server_tools = await self.client.get_tools(server_name=server_name)
            except Exception as exc:
                message = f"Failed to load MCP tools from server `{server_name}`: {exc}"
                if self.config.fail_fast:
                    raise RuntimeError(message) from exc
                logger.warning(message)
                continue

            logger.info(f"Loaded {len(server_tools)} MCP tools from server `{server_name}`")
            belong = self.config.servers[server_name].belong
            registrations.extend(MCPToolRegistration(tool=tool, belong=belong) for tool in server_tools)

        return registrations
