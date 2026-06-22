from pydantic_settings import BaseSettings


class ToolkitSetting(BaseSettings):
    TAVILY_KEY: str
    SQLITE_PATH: str = "cache"
