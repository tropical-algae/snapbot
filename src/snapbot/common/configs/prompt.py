from pydantic import BaseModel


class PromptConfig(BaseModel):
    root_path: str = "src/snapbot/core/prompts"

    system_prompt_path: str = "system"
    description_path: str = "desc"
    other_prompt_path: str = "other"

    memory_filename: str = "memory.md"
