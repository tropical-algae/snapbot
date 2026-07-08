import re
import shutil
from datetime import datetime
from typing import Literal
from uuid import uuid4

from anyio import Path
from filelock import FileLock
from langchain_core.runnables import RunnableConfig

from snapbot.common.configs import settings
from snapbot.common.model import ToolArtifactType

_IDENTIFIER_RE = re.compile(r"[^A-Za-z0-9_.-]+")


async def read_file(filepath: str | Path, auto_create: bool = False) -> str:
    filepath = Path(filepath)
    file_existed = await filepath.exists()
    if not file_existed and auto_create:
        await filepath.parent.mkdir(parents=True, exist_ok=True)
        await filepath.touch(exist_ok=True)
        return ""

    try:
        return await filepath.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return await filepath.read_text(encoding="gbk", errors="ignore")


async def write_file(filepath: Path, content: str) -> None:
    await filepath.parent.mkdir(parents=True, exist_ok=True)

    lock = FileLock(str(filepath) + ".lock")

    with lock:
        await filepath.write_text(content, encoding="utf-8")


async def remove_file(path: Path) -> None:
    if not (await path.exists()):
        return

    if await path.is_dir():
        shutil.rmtree(path)
    else:
        await path.unlink()


def sanitize_identifier(identifier: str) -> str:
    cleaned = _IDENTIFIER_RE.sub("_", identifier.strip())
    return cleaned.strip("._-") or "unknown"


def generate_timestamp_filename(ext: str | None = None) -> str:
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    short_uuid = uuid4().hex[:4].upper()

    filename = f"{timestamp}_{short_uuid}"
    if ext:
        ext = ext.lstrip(".")
        filename = f"{filename}.{ext}"
    return filename


async def get_memory_workspace_path(
    config: RunnableConfig,
    artifact_type: Literal[
        ToolArtifactType.IDENTITY_MEMORY,
        ToolArtifactType.PREFERENCE_MEMORY,
    ],
) -> Path:
    configurable = config.get("configurable", {})
    filepath: Path | None = None
    if artifact_type == ToolArtifactType.IDENTITY_MEMORY:
        user_id = str(configurable.get("user_id", "unknown_user"))
        filepath = Path(settings.agent.identity_memory_path) / f"{sanitize_identifier(user_id)}.md"

    if artifact_type == ToolArtifactType.PREFERENCE_MEMORY:
        thread_id = str(configurable.get("thread_id", "unknown_thread"))
        filepath = Path(settings.agent.preference_memory_path) / f"{sanitize_identifier(thread_id)}.md"

    if filepath is None:
        raise RuntimeError(f"Wrong ToolArtifactType for memory: {artifact_type}")
    await filepath.parent.mkdir(parents=True, exist_ok=True)
    return filepath


async def get_thread_workspace_path(
    config: RunnableConfig,
    artifact_type: Literal[ToolArtifactType.CACHE],
    subdir: str = "",
    filename: str | None = None,
    ext: str | None = None,
) -> Path:
    configurable = config.get("configurable", {})
    thread_id = str(configurable.get("thread_id", "unknown_thread"))

    if artifact_type == ToolArtifactType.CACHE:
        filepath = Path(settings.agent.cache_path) / thread_id / subdir
        await filepath.mkdir(parents=True, exist_ok=True)

        if filename:
            if ext:
                ext = ext.lstrip(".")
                filename = f"{sanitize_identifier(filename)}.{ext}"
            filepath = filepath / filename

        return filepath

    raise RuntimeError(f"Wrong ToolArtifactType: {artifact_type}")
