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

from snapbot.core.middleware.service import build_memory_context, get_memory_ids


class FileMemoryMiddleware(AgentMiddleware[AgentState[Any], ContextT, ResponseT]):
    def modify_request(self, request: ModelRequest[ContextT]) -> ModelRequest[ContextT]:
        config = get_config()
        thread_id, user_id = get_memory_ids(config)
        memory_context = build_memory_context(thread_id, user_id)
        if not memory_context:
            return request

        base_content = request.system_message.text if request.system_message else ""
        system_message = SystemMessage(content=f"{base_content}\n\n{memory_context}")

        return request.override(system_message=system_message)

    def wrap_model_call(
        self,
        request: ModelRequest[ContextT],
        handler: Callable[[ModelRequest[ContextT]], ModelResponse[ResponseT]],
    ) -> ModelResponse[ResponseT]:
        return handler(self.modify_request(request))

    async def awrap_model_call(
        self,
        request: ModelRequest[ContextT],
        handler: Callable[[ModelRequest[ContextT]], Awaitable[ModelResponse[ResponseT]]],
    ) -> ModelResponse[ResponseT]:
        return await handler(self.modify_request(request))
