from pydantic_settings import BaseSettings


class AgentSetting(BaseSettings):
    AGENT_MODEL_URL: str = ""
    AGENT_MODEL_KEY: str = ""
    AGENT_MODEL_PROVIDE: str = "openai"
    AGENT_DEFAULT_MODEL: str = "gpt-5.4-nano"
    AGENT_AVAILABLE_MODELS: list = [AGENT_DEFAULT_MODEL]
