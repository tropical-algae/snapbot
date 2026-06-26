from pathlib import Path
from typing import Any

from snapbot.common.configs import settings
from snapbot.common.logging import logger
from snapbot.common.utils.file import read_file
from snapbot.core.agent.models import RootAgentName, SubAgentName


class PromptRegistry:
    def __init__(self):
        prompt_path = Path(settings.PROMPT_PATH)

        self.system_prompt_path: Path = prompt_path / settings.SYSTEM_PROMPT_DIR
        self.desc_prompt_path: Path = prompt_path / settings.DESCRIPTION_DIR

        self.cache: dict[str, str] = {}

        logger.info("Prompt has been registered")

    def get_system_prompt(
        self, agent_name: RootAgentName | SubAgentName, use_cache: bool = True, **kwargs: Any
    ) -> str:
        filepath = self.system_prompt_path / f"{agent_name.value}.md"
        prompt = self.cache.get(filepath) if use_cache else None

        if not prompt:
            prompt = read_file(filepath, auto_create=True)
            if use_cache:
                self.cache[filepath] = prompt

        return prompt.format(**kwargs)

    def get_description(
        self,
        agent_name: RootAgentName | SubAgentName,
        use_cache: bool = True,
    ) -> str:
        filepath = self.desc_prompt_path / f"{agent_name.value}.md"
        prompt = self.cache.get(filepath) if use_cache else None

        if not prompt:
            prompt = read_file(filepath, auto_create=True)
            if use_cache:
                self.cache[filepath] = prompt

        return prompt


prompt_registry = PromptRegistry()
