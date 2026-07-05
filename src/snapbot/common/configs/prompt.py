from pydantic import BaseModel, Field


class PromptConfig(BaseModel):
    root_path: str = Field(default="src/snapbot/core/prompts")

    system_prompt_path: str = Field(default="system")
    description_path: str = Field(default="desc")
    other_prompt_path: str = Field(default="other")

    memory_filename: str = Field(default="memory.md")
