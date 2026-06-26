from pydantic_settings import BaseSettings


class PromptSetting(BaseSettings):
    PROMPT_PATH: str = "src/snapbot/core/prompts"

    SYSTEM_PROMPT_DIR: str = "system"
    DESCRIPTION_DIR: str = "desc"
    OTHER_PROMPT_DIR: str = "other"

    MEMORY_FILENAME: str = "memory.md"
