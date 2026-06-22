from pathlib import Path


def read_file(filepath: str | Path) -> str:
    filepath = Path(filepath)

    try:
        return filepath.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return filepath.read_text(encoding="gbk", errors="ignore")
