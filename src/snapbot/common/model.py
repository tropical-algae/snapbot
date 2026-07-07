from enum import StrEnum


class LoggerBackend(StrEnum):
    LOGURU = "loguru"
    LOGGING = "logging"


class ToolArtifactType(StrEnum):
    CACHE = "cache"
    IDENTITY_MEMORY = "identity_memory"
    PREFERENCE_MEMORY = "preference_memory"
