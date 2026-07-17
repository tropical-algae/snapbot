from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from snapbot.core.agent.models import SubAgentName


class GroupConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    can_speak: bool = True
    agent_enabled: bool = True
    excluded_subagents: list[SubAgentName] = Field(default_factory=list)
    excluded_tools: list[str] = Field(default_factory=list)

    @field_validator("excluded_subagents", mode="before")
    @classmethod
    def validate_excluded_subagents(cls, value: Any) -> list[SubAgentName]:
        if not isinstance(value, list):
            return []

        subagents: list[SubAgentName] = []
        for item in value:
            try:
                subagents.append(SubAgentName(str(item)))
            except ValueError:
                continue
        return subagents

    @field_validator("excluded_tools", mode="before")
    @classmethod
    def validate_excluded_tools(cls, value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        return [str(item) for item in value if str(item)]


class SnapBotPluginConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    prefix: str = "/"
    auto_delete_sent_files: bool = True
    sent_file_delete_delay: str = "10m"
    groups: dict[str, GroupConfig] = Field(default_factory=dict)

    @field_validator("groups", mode="before")
    @classmethod
    def validate_groups(cls, value: Any) -> dict[str, Any]:
        if not isinstance(value, dict):
            return {}
        return {str(group_id): group_config for group_id, group_config in value.items()}

    @classmethod
    def defaults(cls) -> dict[str, Any]:
        return cls().model_dump(mode="json")

    def get_group(self, group_id: int | str) -> GroupConfig:
        return self.groups.get(str(group_id), GroupConfig())
