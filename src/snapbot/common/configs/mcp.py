from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field

from snapbot.core.agent.models import RootAgentName, SubAgentName


class MCPServerConfig(BaseModel):
    enabled: bool = True
    belong: frozenset[RootAgentName | SubAgentName] = Field(default_factory=frozenset)
    session_kwargs: dict[str, Any] | None = None

    def to_connection(self) -> dict[str, Any]:
        return self.model_dump(exclude={"enabled", "belong"}, exclude_none=True)


class MCPStdioServerConfig(MCPServerConfig):
    transport: Literal["stdio"] = "stdio"
    command: str
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] | None = None
    cwd: str | None = None
    encoding: str = "utf-8"
    encoding_error_handler: Literal["strict", "ignore", "replace"] = "strict"


class MCPHttpServerConfig(MCPServerConfig):
    transport: Literal["http", "streamable_http", "streamable-http"] = "http"
    url: str
    headers: dict[str, str] | None = None
    timeout: float = Field(default=30, gt=0)
    sse_read_timeout: float = Field(default=300, gt=0)
    terminate_on_close: bool = True


MCPConnectionConfig = Annotated[
    MCPStdioServerConfig | MCPHttpServerConfig,
    Field(discriminator="transport"),
]


class MCPConfig(BaseModel):
    enabled: bool = True
    tool_name_prefix: bool = True
    handle_tool_errors: bool = True
    fail_fast: bool = False
    servers: dict[str, MCPConnectionConfig] = Field(default_factory=dict)
