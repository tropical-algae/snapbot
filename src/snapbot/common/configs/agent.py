from typing import Self

from pydantic import BaseModel, Field, model_validator

from snapbot.core.agent.models.agent import RootAgentName, SubAgentName


class AgentParam(BaseModel):
    model: str = Field(description="格式为<model_provider>:<model>，provider与model需要是ModelConfig中存在的定义")


class ModelConfig(BaseModel):
    base_url: str = Field(default="")
    api_key: str = Field(default="")
    provider: str = Field(default="openai")
    names: list[str] = Field(default_factory=list, description="模型名的列表")


class AgentConfig(BaseModel):
    models: list[ModelConfig]
    agent: dict[str, AgentParam]

    cache_path: str = Field(default="data/cache")
    history_path: str = Field(default="data/history")
    sqlite_path: str = Field(default="data/database")
    backend_path: str = Field(default="data/agent")
    identity_memory_path: str = Field(default="data/memory/identity")
    preference_memory_path: str = Field(default="data/memory/preference")

    @model_validator(mode="after")
    def validate_agent_definitions(self) -> Self:
        valid_agent_names = {agent.value for agent in (*RootAgentName, *SubAgentName)}
        invalid_agent_names = sorted(set(self.agent) - valid_agent_names)
        if invalid_agent_names:
            raise ValueError(f"agent 包含未定义的名称: {', '.join(invalid_agent_names)}")

        valid_model_names = {f"{model.provider}:{model_name}" for model in self.models for model_name in model.names}
        invalid_model_names = sorted({param.model for param in self.agent.values()} - valid_model_names)
        if invalid_model_names:
            raise ValueError(f"agent 引用了未配置的模型: {', '.join(invalid_model_names)}")

        return self
