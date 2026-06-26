import re
from pathlib import Path

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
