from __future__ import annotations

import logging
import sys
from pathlib import Path
from types import FrameType
from typing import cast

import loguru

from snapbot.common.configs import settings
from snapbot.common.configs.logger import LoggerConfig
from snapbot.common.model import LoggerBackend

ORIGIN_LOGGER_NAMES = ["uvicorn.asgi", "uvicorn.access", "uvicorn"]
ORIGIN_LOGGER_NAMES += ["sqlalchemy.engine", "sqlalchemy.engine.Engine"] if settings.log.debug else []

LOGURU_CONSOLE_FORMAT = (
    "<green>{time:YYYYMMDD HH:mm:ss}</green> | "
    "{process.name} | "
    "{thread.name} | "
    "<cyan>{module}</cyan>.<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{level}</level>: "
    "<level>{message}</level>"
)
LOGURU_FILE_FORMAT = (
    "{time:YYYYMMDD HH:mm:ss} - {process.name} | {thread.name} | {module}.{function}:{line} - {level} - {message}"
)
STD_LOGGING_FORMAT = (
    "%(asctime)s - %(processName)s | %(threadName)s | %(name)s.%(funcName)s:%(lineno)d - %(levelname)s - %(message)s"
)
STD_LOGGING_DATE_FORMAT = "%Y%m%d %H:%M:%S"


def get_log_level(config: LoggerConfig) -> str:
    return "DEBUG" if config.debug else config.level


def get_log_filepath(config: LoggerConfig) -> Path:
    return Path(config.root_path) / f"{settings.project_name}.log"


def intercept_std_logging(level: str | None = None) -> None:
    class InterceptHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:  # pragma: no cover
            try:
                log_level = loguru.logger.level(record.levelname).name
            except ValueError:
                log_level = str(record.levelno)

            frame, depth = logging.currentframe(), 2
            while frame and frame.f_code.co_filename == logging.__file__:
                frame = cast(FrameType, frame.f_back)
                depth += 1

            loguru.logger.opt(depth=depth, exception=record.exc_info).log(
                log_level,
                record.getMessage(),
            )

    resolved_level = level or get_log_level(settings.log)
    logging.basicConfig(handlers=[InterceptHandler()], level=resolved_level)
    logging.getLogger().handlers = [InterceptHandler()]
    for logger_name in ORIGIN_LOGGER_NAMES:
        std_logger = logging.getLogger(logger_name)
        std_logger.handlers = [InterceptHandler()]
        std_logger.setLevel(resolved_level)


def create_std_logger(config: LoggerConfig) -> logging.Logger:
    logger_name = config.name or settings.project_name
    std_logger = logging.getLogger(logger_name)

    if config.configure:
        level = get_log_level(config)
        std_logger.handlers = []
        std_logger.setLevel(level)
        std_logger.propagate = False

        formatter = logging.Formatter(STD_LOGGING_FORMAT, datefmt=STD_LOGGING_DATE_FORMAT)

        if config.console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(level)
            console_handler.setFormatter(formatter)
            std_logger.addHandler(console_handler)

        if config.file_output:
            log_filepath = get_log_filepath(config)
            log_filepath.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_filepath, encoding=config.file_encoding)
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            std_logger.addHandler(file_handler)

    return std_logger


def create_loguru_logger(config: LoggerConfig) -> loguru.Logger:
    if config.configure:
        loguru.logger.remove()
        level = get_log_level(config)

        if config.console_output:
            loguru.logger.add(
                sys.stdout,
                level=level,
                colorize=True,
                format=LOGURU_CONSOLE_FORMAT,
            )

        if config.file_output:
            log_filepath = get_log_filepath(config)
            log_filepath.parent.mkdir(parents=True, exist_ok=True)
            loguru.logger.add(
                log_filepath,
                level=level,
                format=LOGURU_FILE_FORMAT,
                encoding=config.file_encoding,
                retention="12 week",
                rotation="1 week",
                compression="zip",
                backtrace=True,
                diagnose=True,
                enqueue=True,
            )

        if config.intercept_std_logging:
            intercept_std_logging(level)
    return loguru.logger


def create_logger(config: LoggerConfig | None = None) -> logging.Logger | loguru.Logger:
    config = settings.log if config is None else config
    if config.backend == LoggerBackend.LOGGING:
        return create_std_logger(config)
    return create_loguru_logger(config)


logger: logging.Logger | loguru.Logger = create_logger()
