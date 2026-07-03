from pydantic import BaseModel, Field

from snapbot.core.tools.models import ToolMeta


class ToolConfig(BaseModel):
    meta: ToolMeta = Field(default_factory=ToolMeta)
    enable_whitelist: bool = Field(default=False)
    thread_whitelist: list[str] = Field(default_factory=list)
    thread_blacklist: list[str] = Field(default_factory=list)
