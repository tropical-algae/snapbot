from collections import defaultdict
from typing import Any, cast

import aiosqlite
from anyio import Path
from deepagents import SubAgent, create_deep_agent
from deepagents.backends import FilesystemBackend
from langchain.agents.middleware.types import AgentMiddleware
from langchain.chat_models import BaseChatModel, init_chat_model
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph.state import CompiledStateGraph

from snapbot.common.configs import settings
from snapbot.common.configs.agent import AgentParam
from snapbot.common.logging import logger
from snapbot.common.model import ToolArtifactType
from snapbot.common.utils.file import get_memory_workspace_path, remove_file
from snapbot.core.agent.models import RootAgentName, SubAgentName
from snapbot.core.middleware.memory import FileMemoryMiddleware
from snapbot.core.prompts.registry import prompt_registry
from snapbot.core.tools.registry import tool_registry


class AgentRegistry:
    def __init__(self) -> None:
        self.models: dict[str, BaseChatModel] = {}
        self.agents: dict[str, dict[RootAgentName, CompiledStateGraph]] = defaultdict(dict)
        self.subagents: list[SubAgent] = []

        self._checkpoint_conns: dict[RootAgentName, aiosqlite.Connection] = {}
        self._checkpointers: dict[RootAgentName, AsyncSqliteSaver] = {}

    async def __aenter__(self) -> "AgentRegistry":
        await self.setup()
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.aclose()

    async def setup(self) -> None:
        logger.info("Setup agent registry.")
        self._register_models()
        await self._register_sub_agents()

        sqlite_path = Path(settings.agent.sqlite_path)
        await sqlite_path.mkdir(parents=True, exist_ok=True)

        for agent_name in RootAgentName:
            self._checkpoint_conns[agent_name] = await aiosqlite.connect(
                str(sqlite_path / f"{agent_name.value}_checkpoint.db"),
                check_same_thread=False,
                isolation_level=None,
            )
            self._checkpointers[agent_name] = AsyncSqliteSaver(self._checkpoint_conns[agent_name])

    async def aclose(self) -> None:
        for checkpoint_conn in self._checkpoint_conns.values():
            await checkpoint_conn.close()
        self._checkpoint_conns.clear()
        self._checkpointers.clear()

    def _register_models(
        self,
    ) -> None:
        models: dict[str, BaseChatModel] = {}
        for config in settings.agent.models:
            for model_name in config.names:
                model_key = f"{config.provider}:{model_name}"
                if model_key in models:
                    raise ValueError(f"Duplicate model config: {model_key}")

                models[model_key] = init_chat_model(
                    model=model_name,
                    model_provider=config.provider,
                    api_key=config.api_key,
                    base_url=config.base_url,
                )

        self.models = models

    @staticmethod
    def _get_agent_param(agent_name: RootAgentName | SubAgentName) -> AgentParam | None:
        return settings.agent.agents.get(agent_name.value)

    async def _register_sub_agents(
        self,
    ) -> None:
        subagents: list[SubAgent] = []
        for name in SubAgentName:
            description = await prompt_registry.get_description(name)
            system_prompt = await prompt_registry.get_system_prompt(name)
            tools = tool_registry.get_tools(name)
            agent_param = self._get_agent_param(name)
            model = self.models.get(agent_param.model) if agent_param is not None else None

            if model is not None:
                subagent = SubAgent(
                    name=name.value,
                    description=description,
                    system_prompt=system_prompt,
                    tools=tools,
                    model=model,
                )
            else:
                subagent = SubAgent(
                    name=name.value,
                    description=description,
                    system_prompt=system_prompt,
                    tools=tools,
                )

            subagents.append(subagent)
        self.subagents = subagents

    async def _register_root_agent(
        self,
        thread_id: str,
        agent_name: RootAgentName,
        excluded_subagents: list[SubAgentName] | None = None,
        excluded_tools: list[str] | None = None,
    ) -> CompiledStateGraph:
        checkpointer = self._checkpointers.get(agent_name)
        if checkpointer is None:
            raise RuntimeError(
                f"Can not get checkpoint for {agent_name}, call AgentRegistry.setup() before get_agent()"
            )

        agent_param = self._get_agent_param(agent_name)
        if agent_param is None:
            raise ValueError(f"Agent {agent_name.value} was not configured")

        model = self.models.get(agent_param.model)
        if not model:
            raise ValueError(f"Agent model {agent_param.model} was not registered")

        tools = tool_registry.get_tools(agent_name, excluded_tools=excluded_tools)
        backend_path = Path(settings.agent.backend_path) / thread_id
        await (backend_path / "skills").mkdir(parents=True, exist_ok=True)
        system_prompt = await prompt_registry.get_system_prompt(agent_name)
        subagents = (
            self.subagents
            if excluded_subagents is None
            else [
                subagent
                for subagent in self.subagents
                if (name := subagent.get("name")) is not None and name not in excluded_subagents
            ]
        )

        return create_deep_agent(
            model=model,
            tools=tools or None,
            subagents=subagents,
            system_prompt=system_prompt,
            middleware=[cast(AgentMiddleware[Any, Any, Any], FileMemoryMiddleware())],
            # permissions=[
            #     FilesystemPermission(operations=["read"], paths=["/**"], mode="allow"),
            #     FilesystemPermission(operations=["write"], paths=["/skills/**"], mode="allow"),
            #     FilesystemPermission(operations=["write"], paths=["/**"], mode="interrupt"),
            # ],
            checkpointer=checkpointer,
            backend=FilesystemBackend(root_dir=str(backend_path), virtual_mode=True),
            # skills=["/skills/"],
            name=agent_name.value,
        )

    async def remove_agent(self, thread_id: str, agent_names: list[RootAgentName] | None = None) -> None:
        useless_paths: list[Path] = [
            Path(settings.agent.backend_path) / thread_id,
            await get_memory_workspace_path(
                RunnableConfig(configurable={"thread_id": thread_id}), ToolArtifactType.PREFERENCE_MEMORY
            ),
        ]
        for useless_path in useless_paths:
            await remove_file(useless_path)

        agent_names = list(RootAgentName) if agent_names is None else agent_names
        agents = self.agents.get(thread_id, {})
        for agent_name in agent_names:
            agents.pop(agent_name, None)
            if checkpointer := self._checkpointers.get(agent_name):
                await checkpointer.adelete_thread(thread_id)

    async def get_agent(
        self,
        thread_id: str,
        agent_name: RootAgentName = RootAgentName.SNAP_AGENT,
        excluded_subagents: list[SubAgentName] | None = None,
        excluded_tools: list[str] | None = None,
    ) -> CompiledStateGraph:
        thread_agents = self.agents[thread_id]
        if agent_name not in thread_agents:
            thread_agents[agent_name] = await self._register_root_agent(
                thread_id, agent_name, excluded_subagents, excluded_tools
            )
        return thread_agents[agent_name]


# async def run():
#     # 用法1
#     agent_registry = AgentRegistry()
#     await agent_registry.setup()
#     try:
#         a = await agent_registry.get_agent("asd")
#         # a.invoke()
#         print(agent_registry.subagents)
#     finally:
#         await agent_registry.aclose()

#     # 用法2
#     async with AgentRegistry() as agent_registry2:
#         b = await agent_registry2.get_agent("asd")
#         # b.invoke()
#         print(agent_registry2.subagents)


# if __name__ == "__main__":
#     import asyncio

#     asyncio.run(run())
