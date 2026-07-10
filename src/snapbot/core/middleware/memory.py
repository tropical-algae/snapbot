from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from langchain.agents.middleware.types import (
    AgentMiddleware,
    AgentState,
    ContextT,
    ModelRequest,
    ModelResponse,
    ResponseT,
)
from langchain_core.messages import SystemMessage
from langgraph.config import get_config

from snapbot.common.configs import settings
from snapbot.common.model import ToolArtifactType
from snapbot.common.utils.file import get_memory_workspace_path, read_file
from snapbot.core.prompts.registry import prompt_registry


class FileMemoryMiddleware(AgentMiddleware[AgentState[Any], ContextT, ResponseT]):
    async def modify_request(self, request: ModelRequest[ContextT]) -> ModelRequest[ContextT]:
        memory_context: str = ""
        sections: list[str] = []
        config = get_config()
        configurable = config.get("configurable", {})
        user_id = str(configurable.get("user_id", None))

        identity_memory = await read_file(
            await get_memory_workspace_path(config, ToolArtifactType.IDENTITY_MEMORY), auto_create=True
        )
        preference_memory = await read_file(
            await get_memory_workspace_path(config, ToolArtifactType.PREFERENCE_MEMORY), auto_create=True
        )
        context_template = await prompt_registry.get_other_prompt(settings.prompt.memory_filename)

        if preference_memory:
            sections.append(f"## Agent Preference\n{preference_memory}")
        if user_id:
            sections.append(f"## User Identity\n本次对话的用户ID: {user_id}\n{identity_memory}")

        if len(sections) > 0:
            payload = "\n\n".join(sections)
            memory_context = context_template.format(memory=payload) if context_template else payload
            base_content = request.system_message.text if request.system_message else ""
            system_message = SystemMessage(content=f"{base_content}\n\n{memory_context}")
            return request.override(system_message=system_message)

        return request

    async def awrap_model_call(
        self,
        request: ModelRequest[ContextT],
        handler: Callable[[ModelRequest[ContextT]], Awaitable[ModelResponse[ResponseT]]],
    ) -> ModelResponse[ResponseT]:
        modified_request = await self.modify_request(request)
        return await handler(modified_request)
