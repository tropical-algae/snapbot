import shutil
from collections.abc import AsyncGenerator

import aiosqlite
from anyio import Path
from deepagents import FilesystemPermission, SubAgent, create_deep_agent
from deepagents.backends import FilesystemBackend
from langchain.chat_models import BaseChatModel, init_chat_model
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph.state import Command, CompiledStateGraph

from snapbot.common.configs import settings
from snapbot.common.logging import logger
from snapbot.core.agent.models import AgentName, AgentRuntimeConfig, ApprovalStatus
from snapbot.core.agent.registry.subagent import subagent_registry
from snapbot.core.agent.service import build_user_message_payload, get_agent_approval_requests, get_agent_interrupt
from snapbot.core.prompts.registry import prompt_registry


class AgentRegistry:
    def __init__(self) -> None:
        self.models: dict[str, BaseChatModel] = {}
        self.agents: dict[str, CompiledStateGraph] = {}
        self.subagents: list[SubAgent] = []
        self.approval_status: dict[str, ApprovalStatus] = {}

        self._checkpoint_conn: aiosqlite.Connection | None = None
        self._checkpointer: AsyncSqliteSaver | None = None

    async def __aenter__(self) -> "AgentRegistry":
        await self.setup()
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.aclose()

    async def setup(self) -> None:
        logger.info("Setup agent registry.")
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

    async def _register_agent(self, thread_id: str) -> CompiledStateGraph:
        if self._checkpointer is None:
            raise RuntimeError("AgentRegistry.setup() must be called before get_agent()")

        model = self.models.get(settings.AGENT_DEFAULT_MODEL)
        if not model:
            raise ValueError(f"Default model {settings.AGENT_DEFAULT_MODEL} was not registered")

        root_dir = Path(f"./data/agent/{thread_id}")
        await (root_dir / "memory").mkdir(parents=True, exist_ok=True)
        await (root_dir / "skills").mkdir(parents=True, exist_ok=True)
        await (root_dir / "memory/memory.md").touch(exist_ok=True)
        await (root_dir / "AGENT.md").touch(exist_ok=True)

        return create_deep_agent(
            model=model,
            subagents=self.subagents,
            system_prompt=prompt_registry.get_system_prompt(AgentName.SNAPAGENT),
            permissions=[
                FilesystemPermission(
                    operations=["read"],
                    paths=["/**"],
                    mode="allow",
                ),
                FilesystemPermission(
                    operations=["write"],
                    paths=[
                        "/memory/**",
                        "/AGENT.md",
                        "/skills/**",
                    ],
                    mode="allow",
                ),
                # FilesystemPermission(
                #     operations=["write"],
                #     paths=["/**"],
                #     mode="interrupt",
                # ),
            ],
            checkpointer=self._checkpointer,
            backend=FilesystemBackend(root_dir=str(root_dir), virtual_mode=True),
            memory=[
                "/memory/memory.md",
                "/AGENT.md",
            ],
            skills=["/skills/"],
        )

    async def remove_agent(self, thread_id: str) -> None:
        root_dir = Path(f"./data/agent/{thread_id}")
        self.agents.pop(thread_id, None)
        if await root_dir.exists() and await root_dir.is_dir():
            shutil.rmtree(root_dir)
        if self._checkpointer:
            await self._checkpointer.adelete_thread(thread_id)

    async def get_agent(self, thread_id: str) -> CompiledStateGraph:
        agent: CompiledStateGraph | None = self.agents.get(thread_id)
        if agent is None:
            new_agent: CompiledStateGraph = await self._register_agent(thread_id=thread_id)
            self.agents[thread_id] = new_agent
            return new_agent
        return agent

    def get_approval_status(self, thread_id: str) -> ApprovalStatus:
        approval_status = self.approval_status.get(thread_id)
        if approval_status is None:
            approval_status = ApprovalStatus(approvals=[], decisions=[])
            self.approval_status[thread_id] = approval_status
        return approval_status

    async def _astream_agent_events(
        self, agent: CompiledStateGraph, config: AgentRuntimeConfig, payload: dict | Command
    ) -> AsyncGenerator[str, None]:
        final_response = ""
        async for event in agent.astream_events(payload, config=config.to_langgraph_config(), version="v2"):
            kind = event["event"]

            if kind == "on_tool_start":
                tool_name = event["name"]
                tool_input: dict = event["data"].get("input", {})
                if tool_name == "task":
                    tool_desc = tool_input.get("description", "开始规划任务")
                    yield tool_desc
                # yield f"[Tool Call] {tool_name}\n  args: {tool_input}"

            elif kind == "on_chat_model_end":
                output_msg = event["data"].get("output")

                if (
                    output_msg
                    and hasattr(output_msg, "content")
                    and output_msg.content
                    and not getattr(output_msg, "tool_calls", None)
                ):
                    final_response = output_msg.content
        yield final_response

    async def astream_agent_events(
        self,
        config: AgentRuntimeConfig,
        message: str,
    ) -> AsyncGenerator[str, None]:
        thread_id = config.thread_id
        agent = await self.get_agent(thread_id)
        approval_status = self.get_approval_status(thread_id)

        payload: Command | dict = build_user_message_payload(message)

        if approval_status.is_opened:
            decision_status = approval_status.set_next_decision(message)

            if decision_status and not approval_status.is_opened:
                payload = approval_status.get_approval_command()

            else:
                yield (approval_status.get_next_approval_desc() or "Something is wrong here.")
                return

        async for text in self._astream_agent_events(agent, config, payload):
            yield text

        approval_requests = get_agent_approval_requests(await get_agent_interrupt(agent, config))

        if approval_requests:
            approval_status.reflash(approval_requests)

            yield (approval_status.get_next_approval_desc() or "Something is wrong here.")


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
