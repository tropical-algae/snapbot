from enum import StrEnum

from langchain_core.runnables.config import RunnableConfig
from pydantic import BaseModel, ConfigDict


class AgentName(StrEnum):
    pass


class RootAgentName(AgentName):
    SNAP_AGENT = "snap_agent"


class SubAgentName(AgentName):
    INFO_SEARCHAGENT = "info_searcher"
    MEMORY_MANAGER = "memory_manager"
    GROUP_OPERATOR = "group_operator"
    COMIC_DOWNLOADER = "comic_downloader"


class AgentRuntimeConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    thread_id: str
    user_id: str

    def to_langgraph_config(self) -> RunnableConfig:
        return RunnableConfig(configurable=self.model_dump())
