from pathlib import Path

from langchain_core.runnables import RunnableConfig

from snapbot.common.configs import settings
from snapbot.common.utils.file import read_file, sanitize_identifier

IDENTITY_MEMORY_PATH: Path = Path(settings.IDENTITY_MEMORY_PATH)
PREFERENCE_MEMORY_PATH: Path = Path(settings.PREFERENCE_MEMORY_PATH)
MEMORY_TEMPLATE_PROMPT_FILEPATH: Path = Path("src/snapbot/core/prompts/other/memory.md")


def get_identity_memory_path(user_id: str) -> Path:
    return IDENTITY_MEMORY_PATH / f"{sanitize_identifier(user_id)}.md"


def get_preference_memory_path(thread_id: str) -> Path:
    return PREFERENCE_MEMORY_PATH / f"{sanitize_identifier(thread_id)}.md"


def get_memory_ids(config: RunnableConfig) -> tuple[str, str]:
    configurable = config.get("configurable", {})
    thread_id = str(configurable.get("thread_id", "unknown"))
    user_id = str(configurable.get("user_id", "unknown"))
    return thread_id, user_id


def build_memory_context(thread_id: str, user_id: str) -> str:
    identity_memory = read_file(get_identity_memory_path(user_id), auto_create=True)
    preference_memory = read_file(get_preference_memory_path(thread_id), auto_create=True)
    context_template = read_file(MEMORY_TEMPLATE_PROMPT_FILEPATH, auto_create=True)

    if not identity_memory and not preference_memory:
        return ""

    sections: list[str] = []
    if preference_memory:
        sections.append(f"### Agent Preference\n{preference_memory}")
    if identity_memory:
        sections.append(f"### User Identity\n{identity_memory}")

    payload = "\n\n".join(sections)
    return context_template.format(memory=payload) if context_template else payload
