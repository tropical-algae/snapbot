from pydantic_settings import BaseSettings


class LoggerSetting(BaseSettings):
    DEBUG: bool = False
    LOG_PATH: str = "./log"
    LOG_LEVEL: str = "INFO"  # force to "DEBUG" if DEBUG == True
    LOG_FILE_ENCODING: str = "utf-8"
    LOG_CONSOLE_OUTPUT: bool = True
