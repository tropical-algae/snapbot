import aiosqlite
from anyio import Path
from deepagents import FilesystemPermission, SubAgent, create_deep_agent
from deepagents.backends import FilesystemBackend
from langchain.chat_models import BaseChatModel, init_chat_model
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph.state import CompiledStateGraph

from snapbot.common.configs import settings
from snapbot.core.agent.models import AgentName
from snapbot.core.agent.registry.subagent import subagent_registry
from snapbot.core.prompts.registry import prompt_registry


class AgentRegistry:
    def __init__(self) -> None:
        self.models: dict[str, BaseChatModel] = {}
        self.agents: dict[str, CompiledStateGraph] = {}
        self.subagents: list[SubAgent] = []

        self._checkpoint_conn: aiosqlite.Connection | None = None
        self._checkpointer: AsyncSqliteSaver | None = None

    async def __aenter__(self) -> "AgentRegistry":
        await self.setup()
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.aclose()

    async def setup(self) -> None:
        self._register_models()
        self._register_subagents()

        sqlite_path = Path(settings.SQLITE_PATH)
        await sqlite_path.mkdir(parents=True, exist_ok=True)

        self._checkpoint_conn = await aiosqlite.connect(
            str(sqlite_path / "checkpoint.db"),
            check_same_thread=False,
            isolation_level=None,
        )
        self._checkpointer = AsyncSqliteSaver(self._checkpoint_conn)

    async def aclose(self) -> None:
        if self._checkpoint_conn is not None:
            await self._checkpoint_conn.close()
            self._checkpoint_conn = None
            self._checkpointer = None

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

    def _register_subagents(
        self,
    ) -> None:
        self.subagents = subagent_registry.get_subagents()

    async def _register_agent(self, id: str) -> CompiledStateGraph:
        if self._checkpointer is None:
            raise RuntimeError("AgentRegistry.setup() must be called before get_agent()")

        model = self.models.get(settings.AGENT_DEFAULT_MODEL)
        if not model:
            raise ValueError(f"Default model {settings.AGENT_DEFAULT_MODEL} was not registered")

        return create_deep_agent(
            model=model,
            subagents=self.subagents,
            system_prompt=prompt_registry.get_system_prompt(AgentName.SNAPAGENT),
            permissions=[
                FilesystemPermission(operations=["read"], paths=["/**"], mode="allow"),
                FilesystemPermission(operations=["write"], paths=["/**"], mode="interrupt"),
            ],
            checkpointer=self._checkpointer,
            backend=FilesystemBackend(
                root_dir=f"./agent_data/{id}",
                virtual_mode=True,
            ),
            memory=["/memory/"],
            skills=["/skills/"],
        )

    async def get_agent(self, id: str) -> CompiledStateGraph:
        agent: CompiledStateGraph | None = self.agents.get(id)
        if agent is None:
            new_agent = await self._register_agent(id=id)
            self.agents[id] = new_agent
            return new_agent
        return agent


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
