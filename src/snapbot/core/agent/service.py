from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Interrupt

from snapbot.core.agent.models import AgentRuntimeConfig, ApprovalRequest


def build_user_message_payload(message: str) -> dict:
    return {
        "messages": [
            {
                "role": "user",
                "content": message,
            }
        ]
    }


async def get_agent_interrupt(agent: CompiledStateGraph, config: AgentRuntimeConfig) -> Interrupt | None:
    state = await agent.aget_state(config.to_langgraph_config())
    if state.next:
        interrupts = [task.interrupts for task in state.tasks if task.interrupts]

        if interrupts:
            return interrupts[0][0]

    return None


def get_agent_approval_requests(interrupt: Interrupt | None) -> list[ApprovalRequest]:
    approvals: list[ApprovalRequest] = []
    if interrupt is None:
        return approvals

    interrupt_value = interrupt.value
    if isinstance(interrupt_value, dict):
        action_requests: list[dict] = interrupt_value.get("action_requests", [])
        review_configs: list[dict] = interrupt_value.get("review_configs", [])
        review_configs_map: dict[str, dict] = {cfg["action_name"]: cfg for cfg in review_configs}

        for action_request in action_requests:
            review_config = review_configs_map.get(action_request["name"], {})
            approvals.append(
                ApprovalRequest(
                    interrupt_id=interrupt.id,
                    name=action_request["name"],
                    description=action_request["description"],
                    allowed_decisions=review_config.get("allowed_decisions", []),
                )
            )

    return approvals
