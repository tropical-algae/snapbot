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
        if settings.agent.default_model not in settings.agent.available_models:
            settings.agent.available_models.append(settings.agent.default_model)

        available_models = set(settings.agent.available_models + [m.model for m in settings.agent.subagents.values()])
        self.models = {
            model: init_chat_model(
                model=model,
                model_provider=settings.agent.model_provider,
                api_key=settings.agent.api_key,
                base_url=settings.agent.base_url,
            )
            for model in available_models
        }

    async def _register_sub_agents(
        self,
    ) -> None:
        subagents: list[SubAgent] = []
        for name in SubAgentName:
            param = {
                "name": name,
                "description": await prompt_registry.get_description(name),
                "system_prompt": await prompt_registry.get_system_prompt(name),
                "tools": tool_registry.get_tools(name),
            }

            model_name = settings.agent.subagents.get(name.value).model
            if model_name is not None and (model := self.models.get(model_name)) is not None:
                param.update({"model": model})
            subagents.append(SubAgent(**param))
        self.subagents = subagents

    async def _register_root_agent(
        self,
        thread_id: str,
        agent_name: RootAgentName,
        excluded_subagents: list[SubAgentName] | None = None,
    ) -> CompiledStateGraph:
        checkpointer = self._checkpointers.get(agent_name)
        if checkpointer is None:
            raise RuntimeError(
                f"Can not get checkpoint for {agent_name}, call AgentRegistry.setup() before get_agent()"
            )

        model = self.models.get(settings.agent.default_model)
        if not model:
            raise ValueError(f"Default model {settings.agent.default_model} was not registered")

        tools = tool_registry.get_tools(agent_name)
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
    ) -> CompiledStateGraph:
        thread_agents = self.agents[thread_id]
        if agent_name not in thread_agents:
            thread_agents[agent_name] = await self._register_root_agent(thread_id, agent_name, excluded_subagents)
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
