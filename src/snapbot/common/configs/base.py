from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

from snapbot import __version__
from snapbot.common.configs.agent import AgentSetting
from snapbot.common.configs.logger import LoggerSetting
from snapbot.common.configs.prompt import PromptSetting
from snapbot.common.configs.toolkit import ToolkitSetting

CONFIG_FILE = "config.yaml"
ENV_FILE = ".env"


class Setting(
    ToolkitSetting,
    PromptSetting,
    LoggerSetting,
    AgentSetting,
):
    VERSION: str = __version__
    PROJECT_NAME: str = "snapbot"

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        case_sensitive=True,
        extra="ignore",
    )

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
