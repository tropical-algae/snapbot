from pydantic import BaseModel


class ToolkitConfig(BaseModel):
    tavily_key: str
