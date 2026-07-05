from enum import StrEnum


class LoggerBackend(StrEnum):
    LOGURU = "loguru"
    LOGGING = "logging"
