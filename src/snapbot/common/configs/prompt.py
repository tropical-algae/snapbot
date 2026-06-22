from pydantic_settings import BaseSettings


class PromptSetting(BaseSettings):
    # system prompt
    SNAPAGENT_PROMPT_FILEPATH: str = "src/snapbot/core/prompts/system/snap-agent.md"
    SEARCHAGENT_PROMPT_FILEPATH: str = "src/snapbot/core/prompts/system/search-agent.md"

    # description
    SEARCHAGENT_DESC_FILEPATH: str = "src/snapbot/core/prompts/desc/search-agent.md"
