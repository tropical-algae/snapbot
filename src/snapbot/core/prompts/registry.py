from typing import Any

from snapbot.common.configs import settings
from snapbot.common.logging import logger
from snapbot.common.utils.file import read_file
from snapbot.core.agent.models import AgentName
from snapbot.core.prompts.models import PromptMeta

content = read_file(settings.SNAPAGENT_PROMPT_FILEPATH)


class PromptRegistry:
    def __init__(self):
        self.mapping: dict[AgentName, PromptMeta] = {
            AgentName.SNAPAGENT: PromptMeta(
                system_prompt=read_file(settings.SNAPAGENT_PROMPT_FILEPATH),
            ),
            AgentName.SEARCHAGENT: PromptMeta(
                system_prompt=read_file(settings.SEARCHAGENT_PROMPT_FILEPATH),
                description=read_file(settings.SEARCHAGENT_DESC_FILEPATH),
            ),
        }
        logger.info("Prompt has been registered")

    def _get_prompt_meta(self, agent_name: AgentName) -> PromptMeta:
        prompt: PromptMeta | None = self.mapping.get(agent_name)
        if not prompt:
            raise ValueError(f"The PromptMeta for {agent_name} is empty")
        return prompt

    def get_system_prompt(self, agent_name: AgentName, **kwargs: Any) -> str:
        payload: PromptMeta = self._get_prompt_meta(agent_name)
        return payload.system_prompt.format(**kwargs)

    def get_description(self, agent_name: AgentName) -> str:
        payload: PromptMeta = self._get_prompt_meta(agent_name)
        return payload.description


prompt_registry = PromptRegistry()
