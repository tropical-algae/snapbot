import base64
import hashlib
import re
from dataclasses import dataclass, field
from typing import Any

from ag_ui.core import Interrupt, ResumeEntry
from pydantic import BaseModel, ConfigDict, Field

DATA_IMAGE_URL_RE = re.compile(r"^data:(?P<mime_type>image/[\w.+-]+);base64,(?P<data>.+)$", re.DOTALL)
IMAGE_EXTENSIONS = {
    "image/gif": "gif",
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}


class GeneratedImage(BaseModel):
    base64_data: str
    mime_type: str = "image/png"

    @property
    def ext(self) -> str:
        return IMAGE_EXTENSIONS.get(self.mime_type, self.mime_type.rsplit("/", maxsplit=1)[-1] or "png")

    @property
    def digest(self) -> str:
        return hashlib.sha256(self.base64_data.encode()).hexdigest()

    def decode(self) -> bytes:
        return base64.b64decode(self.base64_data)


class ImageContentBlock(BaseModel):
    model_config = ConfigDict(extra="allow")

    type: str
    base64: str | None = None
    mime_type: str | None = None
    url: str | None = None
    result: str | None = None
    data: str | None = None
    source_type: str | None = None
    image_url: Any | None = None

    @classmethod
    def from_unknown(cls, value: Any) -> "ImageContentBlock | None":
        if not isinstance(value, dict):
            return None

        if value.get("type") not in {"image", "image_url", "image_generation_call", "output_image"}:
            return None
        return cls.model_validate(value)

    def to_generated_image(self) -> GeneratedImage | None:
        base64_data = self.base64 or self.result
        mime_type = self.mime_type or "image/png"

        if self.source_type == "base64" and self.data:
            base64_data = self.data

        image_url = self._resolve_image_url()
        if image_url:
            match = DATA_IMAGE_URL_RE.match(image_url)
            if match:
                base64_data = match.group("data")
                mime_type = match.group("mime_type")

        if not base64_data:
            return None

        return GeneratedImage(base64_data=base64_data, mime_type=mime_type)

    def _resolve_image_url(self) -> str | None:
        if self.url:
            return self.url
        if isinstance(self.image_url, str):
            return self.image_url
        if isinstance(self.image_url, dict):
            value = self.image_url.get("url")
            return value if isinstance(value, str) else None
        return None


class LangChainRawEventData(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="ignore")

    chunk: Any | None = None
    output: Any | None = None


class LangChainRawEvent(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="ignore")

    event: str = ""
    data: LangChainRawEventData = Field(default_factory=LangChainRawEventData)

    @classmethod
    def from_raw_event(cls, value: Any) -> "LangChainRawEvent | None":
        if not isinstance(value, dict):
            return None
        return cls.model_validate(value)


@dataclass
class PendingInterruptState:
    interrupts: list[Interrupt]
    decisions: list[ResumeEntry] = field(default_factory=list)

    @property
    def is_opened(self) -> bool:
        return len(self.decisions) < len(self.interrupts)

    def get_next_interrupt(self) -> Interrupt | None:
        if not self.is_opened:
            return None
        return self.interrupts[len(self.decisions)]
