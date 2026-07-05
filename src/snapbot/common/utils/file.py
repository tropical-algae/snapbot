import re
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from filelock import FileLock

_IDENTIFIER_RE = re.compile(r"[^A-Za-z0-9_.-]+")


def read_file(filepath: str | Path, auto_create: bool = False) -> str:
    filepath = Path(filepath)
    if not filepath.exists() and auto_create:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.touch(exist_ok=True)
        return ""

    try:
        return filepath.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return filepath.read_text(encoding="gbk", errors="ignore")


def write_file(filepath: Path, content: str) -> None:
    filepath.parent.mkdir(parents=True, exist_ok=True)

    lock = FileLock(str(filepath) + ".lock")

    with lock:
        filepath.write_text(content, encoding="utf-8")


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
