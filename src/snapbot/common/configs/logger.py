from pydantic import BaseModel, Field


class LoggerConfig(BaseModel):
    debug: bool = Field(default=False)
    root_path: str = Field(default="./logs")
    level: str = Field(default="INFO")  # force to "DEBUG" if DEBUG == True
    file_encoding: str = Field(default="utf-8")
    console_output: bool = Field(default=True)
