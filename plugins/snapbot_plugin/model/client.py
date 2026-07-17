from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SentGroupFile:
    group_id: int | str
    file_id: str
    name: str | None = None


@dataclass(frozen=True)
class SentMessageResult:
    raw: Any = None
    group_file: SentGroupFile | None = None
