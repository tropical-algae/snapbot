from pydantic import BaseModel, Field

from snapbot.common.model import LoggerBackend


class LoggerConfig(BaseModel):
    backend: LoggerBackend = Field(default=LoggerBackend.LOGURU)
    configure: bool = Field(default=True)
    intercept_std_logging: bool = Field(default=False)
    name: str | None = Field(default=None)

    debug: bool = Field(default=False)
    root_path: str = Field(default="./logs")
    level: str = Field(default="INFO")  # force to "DEBUG" if DEBUG == True
    file_encoding: str = Field(default="utf-8")
    console_output: bool = Field(default=True)
    file_output: bool = Field(default=True)
