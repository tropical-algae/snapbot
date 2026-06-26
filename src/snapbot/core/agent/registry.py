import shutil
from collections import defaultdict
from typing import Any, cast

import aiosqlite
from anyio import Path
from deepagents import FilesystemPermission, SubAgent, create_deep_agent
from deepagents.backends import FilesystemBackend
from langchain.agents.middleware.types import AgentMiddleware
from langchain.chat_models import BaseChatModel, init_chat_model
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph.state import CompiledStateGraph

from snapbot.common.configs import settings
from snapbot.common.logging import logger
from snapbot.core.agent.models import ApprovalStatus, RootAgentName, SubAgentName
from snapbot.core.middleware.memory import FileMemoryMiddleware
from snapbot.core.middleware.service import get_preference_memory_path
from snapbot.core.prompts.registry import prompt_registry
from snapbot.core.tools.registry import tool_registry


class AgentRegistry:
    def __init__(self) -> None:
        self.models: dict[str, BaseChatModel] = {}
        self.agents: dict[str, dict[RootAgentName, CompiledStateGraph]] = defaultdict(dict)
        self.subagents: list[SubAgent] = []
        self.approval_status: dict[str, ApprovalStatus] = {}

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
        self._register_sub_agents()

        sqlite_path = Path(settings.SQLITE_PATH)
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
        if settings.AGENT_DEFAULT_MODEL not in settings.AGENT_AVAILABLE_MODELS:
            settings.AGENT_AVAILABLE_MODELS.append(settings.AGENT_DEFAULT_MODEL)

        available_models = set(settings.AGENT_AVAILABLE_MODELS)
        self.models = {
            model: init_chat_model(
                model=model,
                model_provider=settings.AGENT_MODEL_PROVIDE,
                api_key=settings.AGENT_MODEL_KEY,
                base_url=settings.AGENT_MODEL_URL,
            )
            for model in available_models
        }

    def _register_sub_agents(
        self,
    ) -> None:
        subagents: list[SubAgent] = [
            SubAgent(
                name=name,
                description=prompt_registry.get_description(name),
                system_prompt=prompt_registry.get_system_prompt(name),
                tools=tool_registry.get_tools(name),
            )
            for name in SubAgentName
        ]
        self.subagents = subagents

    async def _register_root_agent(self, thread_id: str, agent_name: RootAgentName) -> CompiledStateGraph:
        checkpointer = self._checkpointers.get(agent_name)
        if checkpointer is None:
            raise RuntimeError(
                f"Can not get checkpoint for {agent_name}, call AgentRegistry.setup() before get_agent()"
            )

        model = self.models.get(settings.AGENT_DEFAULT_MODEL)
        if not model:
            raise ValueError(f"Default model {settings.AGENT_DEFAULT_MODEL} was not registered")

        root_dir = Path(settings.AGENT_WORKSPACE_PATH) / thread_id
        await (root_dir / "skills").mkdir(parents=True, exist_ok=True)

        return create_deep_agent(
            model=model,
            subagents=self.subagents,
            system_prompt=prompt_registry.get_system_prompt(agent_name),
            middleware=[cast(AgentMiddleware[Any, Any, Any], FileMemoryMiddleware())],
            permissions=[
                FilesystemPermission(operations=["read"], paths=["/**"], mode="allow"),
                FilesystemPermission(operations=["write"], paths=["/skills/**"], mode="allow"),
                FilesystemPermission(operations=["write"], paths=["/**"], mode="interrupt"),
            ],
            checkpointer=checkpointer,
            backend=FilesystemBackend(root_dir=str(root_dir), virtual_mode=True),
            skills=["/skills/"],
        )

    async def remove_agent(self, thread_id: str, agent_names: list[RootAgentName] | None = None) -> None:
        agent_names = list(RootAgentName) if agent_names is None else agent_names
        root_dir = Path(settings.AGENT_WORKSPACE_PATH) / thread_id
        agents = self.agents.get(thread_id, {})

        for agent_name in agent_names:
            agents.pop(agent_name, None)

            if await root_dir.exists() and await root_dir.is_dir():
                shutil.rmtree(root_dir)

            if checkpointer := self._checkpointers.get(agent_name):
                await checkpointer.adelete_thread(thread_id)

            preference_path = get_preference_memory_path(thread_id)
            if preference_path.exists():
                preference_path.unlink()

    async def get_agent(
        self, thread_id: str, agent_name: RootAgentName = RootAgentName.SNAPAGENT
    ) -> CompiledStateGraph:
        thread_agents = self.agents[thread_id]
        if agent_name not in thread_agents:
            thread_agents[agent_name] = await self._register_root_agent(thread_id, agent_name)
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
