from enum import StrEnum

from langchain_core.runnables.config import RunnableConfig
from pydantic import BaseModel, ConfigDict


class AgentName(StrEnum):
    pass


class RootAgentName(AgentName):
    SNAPAGENT = "snap_agent"


class SubAgentName(AgentName):
    SEARCHAGENT = "info_searcher"
    MEMORYAGENT = "memory_manager"


class AgentRuntimeConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    thread_id: str
    user_id: str

    def to_langgraph_config(self) -> RunnableConfig:
        return RunnableConfig(configurable=self.model_dump())
