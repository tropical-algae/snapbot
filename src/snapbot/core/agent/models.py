from dataclasses import dataclass
from enum import StrEnum

from langchain_core.runnables.config import RunnableConfig
from langgraph.types import Command
from pydantic import BaseModel, ConfigDict


class AgentName(StrEnum):
    SNAPAGENT = "snap-agent"
    SEARCHAGENT = "info_searcher"


class AgentRuntimeConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    thread_id: str

    def to_langgraph_config(self) -> RunnableConfig:
        return RunnableConfig(configurable=self.model_dump())


@dataclass(frozen=True)
class ApprovalRequest:
    interrupt_id: str
    name: str
    description: str
    allowed_decisions: list[str]


@dataclass
class ApprovalStatus:
    # interrupt: Interrupt
    approvals: list[ApprovalRequest]
    decisions: list[str]

    def reflash(self, approvals: list[ApprovalRequest]) -> None:
        self.approvals = approvals
        self.decisions = []

    @property
    def is_opened(self) -> bool:
        return len(self.decisions) < len(self.approvals)

    def get_next_approval(self) -> ApprovalRequest | None:
        if not self.is_opened:
            return None
        index = len(self.decisions)
        return self.approvals[index]

    def get_next_approval_desc(self) -> str | None:
        approval = self.get_next_approval()
        if approval is None:
            return None

        allowed_decisions = "\n".join(f"{index}: {ad}" for index, ad in enumerate(approval.allowed_decisions))
        return f"执行敏感操作【{approval.name}】请批示:\n{allowed_decisions}\n\n回复决策或编号以继续"

    def set_next_decision(self, message: str) -> bool:
        """设置下一审批项的决策

        Args:
            message (str): 用户输入

        Returns:
            bool: 决策是否不合法, 不合法则不予更新
        """
        approval = self.get_next_approval()
        if approval is None:
            return False

        try:
            decision_index = int(message)
            decision = approval.allowed_decisions[decision_index]
            self.decisions.append(decision)
            return True
        except (ValueError, IndexError):
            if message in approval.allowed_decisions:
                self.decisions.append(message)
                return True
            return False

    def get_approval_command(self) -> Command:
        return Command(resume={"decisions": [{"type": decision} for decision in self.decisions]})
