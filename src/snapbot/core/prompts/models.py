from dataclasses import dataclass

# from pydantic import BaseModel

# class AgentInfo(BaseModel):
#     system_prompt: str = ""
#     description: str = ""


@dataclass(frozen=True)
class PromptMeta:
    system_prompt: str = ""
    description: str = ""
