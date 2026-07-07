from typing import Any

from anyio import Path

from snapbot.common.configs import settings
from snapbot.common.logging import logger
from snapbot.common.utils.file import read_file
from snapbot.core.agent.models import AgentName


class PromptRegistry:
    def __init__(self):
        prompt_path = Path(settings.prompt.root_path)

        self.system_prompt_path: Path = prompt_path / settings.prompt.system_prompt_path
        self.desc_prompt_path: Path = prompt_path / settings.prompt.description_path
        self.other_prompt_path: Path = prompt_path / settings.prompt.other_prompt_path

        self.cache: dict[str, str] = {}

        logger.info("Prompt has been registered")

    async def get_system_prompt(self, agent_name: AgentName, use_cache: bool = True, **kwargs: Any) -> str:
        filepath = str(self.system_prompt_path / f"{agent_name.value}.md")
        prompt = self.cache.get(filepath) if use_cache else None

        if not prompt:
            prompt = await read_file(filepath, auto_create=True)
            if use_cache:
                self.cache[filepath] = prompt

        return prompt.format(**kwargs)

    async def get_description(
        self,
        agent_name: AgentName,
        use_cache: bool = True,
    ) -> str:
        filepath = str(self.desc_prompt_path / f"{agent_name.value}.md")
        prompt = self.cache.get(filepath) if use_cache else None

        if not prompt:
            prompt = await read_file(filepath, auto_create=True)
            if use_cache:
                self.cache[filepath] = prompt

        return prompt

    async def get_other_prompt(
        self,
        file_name: str,
        use_cache: bool = True,
    ) -> str:
        filepath = str(self.other_prompt_path / file_name)
        prompt = self.cache.get(filepath) if use_cache else None

        if not prompt:
            prompt = await read_file(filepath, auto_create=True)
            if use_cache:
                self.cache[filepath] = prompt

        return prompt


prompt_registry = PromptRegistry()
