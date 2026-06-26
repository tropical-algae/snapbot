from collections.abc import AsyncGenerator

from langgraph.graph.state import Command, CompiledStateGraph

from snapbot.core.agent.models import AgentRuntimeConfig, ApprovalStatus
from snapbot.core.agent.service import build_user_message_payload, get_agent_approval_requests, get_agent_interrupt


class AgentExecutor:
    def __init__(self):
        self.approval_status: dict[str, ApprovalStatus] = {}

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
        agent: CompiledStateGraph,
        config: AgentRuntimeConfig,
        message: str,
    ) -> AsyncGenerator[str, None]:
        thread_id = config.thread_id
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
