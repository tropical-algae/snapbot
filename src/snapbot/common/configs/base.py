from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

from snapbot import __version__
from snapbot.common.configs.agent import AgentConfig
from snapbot.common.configs.logger import LoggerConfig
from snapbot.common.configs.prompt import PromptConfig
from snapbot.common.configs.tool import ToolConfig
from snapbot.common.configs.toolkit import ToolkitConfig

CONFIG_FILE = "config.yaml"
ENV_FILE = ".env"


class Setting(BaseSettings):
    version: str = __version__
    project_name: str = "snapbot"

    log: LoggerConfig = Field(default_factory=LoggerConfig)
    toolkits: ToolkitConfig
    prompt: PromptConfig = Field(default_factory=PromptConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)
    agent_tools: dict[str, ToolConfig] = Field(default_factory=dict)

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        case_sensitive=True,
        extra="ignore",
        env_nested_delimiter="__",
    )

    # @model_validator(mode="after")
    # def validate_tool_names(self) -> "Setting":

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        _ = init_settings
        yaml_settings = YamlConfigSettingsSource(
            settings_cls=settings_cls, yaml_file=CONFIG_FILE, yaml_file_encoding="utf-8"
        )
        return yaml_settings, env_settings, dotenv_settings, file_secret_settings


settings = Setting()
