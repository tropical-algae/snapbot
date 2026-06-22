from deepagents import SubAgent

from snapbot.core.agent.models import AgentName
from snapbot.core.prompts.registry import prompt_registry
from snapbot.core.tools.registry import tool_registry


class SubAgentRegistry:
    def __init__(self):
        pass

    def get_subagents(self) -> list[SubAgent]:
        subagents: list[SubAgent] = []
        for name in AgentName:
            if name == AgentName.SNAPAGENT:
                continue

            subagents.append(
                SubAgent(
                    name=name,
                    description=prompt_registry.get_description(name),
                    system_prompt=prompt_registry.get_system_prompt(name),
                    tools=tool_registry.get_tools(name),
                )
            )

        return subagents


subagent_registry = SubAgentRegistry()
