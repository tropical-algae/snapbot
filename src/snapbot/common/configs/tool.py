from pydantic import BaseModel, Field

from snapbot.core.tools.models import ToolMeta


class ToolConfig(BaseModel):
    meta: ToolMeta = Field(default_factory=ToolMeta)
