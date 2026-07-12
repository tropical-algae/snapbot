from pydantic import BaseModel, Field

DEFAULT_MODEL = "gpt-5.4-nano"


class SubAgentConfig(BaseModel):
    model: str = Field(default=DEFAULT_MODEL)


class AgentConfig(BaseModel):
    base_url: str = Field(default="")
    api_key: str = Field(default="")
    model_provider: str = Field(default="openai")
    default_model: str = Field(default=DEFAULT_MODEL)
    available_models: list[str] = Field(default_factory=lambda: [DEFAULT_MODEL])
    subagents: dict[str, SubAgentConfig] = Field(default_factory=dict)

    cache_path: str = Field(default="data/cache")
    history_path: str = Field(default="data/history")
    sqlite_path: str = Field(default="data/database")
    backend_path: str = Field(default="data/agent")
    identity_memory_path: str = Field(default="data/memory/identity")
    preference_memory_path: str = Field(default="data/memory/preference")
