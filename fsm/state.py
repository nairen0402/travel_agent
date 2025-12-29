# fsm/state.py

from dataclasses import dataclass
from typing import Optional, List


@dataclass
class FSMResult:
    state: str                 # "A" | "B" | "C"
    reason: str                # 為什麼進入此 state
    allowed_actions: List[str] # 系統允許的下一步行為


def determine_state(country: str, budget: Optional[int]) -> FSMResult:
    """
    FSM 規則：
    C：非日本 → 拒絕
    A：日本 + 有預算 → budget_plan
    B：日本 + 無預算 → tier_plan
    """

    if not country or country.strip() == "":
        return FSMResult(
            state="C",
            reason="未輸入國家",
            allowed_actions=[]
        )

    country = country.strip().lower()

    if country not in ["japan", "日本", "jp"]:
        return FSMResult(
            state="C",
            reason="僅支援日本旅遊",
            allowed_actions=[]
        )

    if budget is not None and budget > 0:
        return FSMResult(
            state="A",
            reason="使用者有提供預算",
            allowed_actions=["budget_plan"]
        )

    return FSMResult(
        state="B",
        reason="使用者未提供預算",
        allowed_actions=["tier_plan"]
    )
