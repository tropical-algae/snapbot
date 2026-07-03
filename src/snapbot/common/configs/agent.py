from pydantic import BaseModel


class AgentConfig(BaseModel):
    base_url: str = ""
    api_key: str = ""
    model_provide: str = "openai"
    default_model: str = "gpt-5.4-nano"
    available_models: list = [default_model]

    sqlite_path: str = "data/database"
    workspace_path: str = "data/agent"
    identity_memory_path: str = "data/memory/identity"
    preference_memory_path: str = "data/memory/preference"
