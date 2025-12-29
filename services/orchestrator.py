# services/orchestrator.py

from fsm.state import determine_state, FSMResult
from services.search_service import llm_search


def run_pipeline(
    location: str,
    days: int,
    budget: int,
    people: int,
    query: str,
    start_date: str = None,
    end_date: str = None,
    accommodation: str = None,
    interests: list = None
) -> dict:
    """
    系統主控流程：
    UI → FSM（只判斷預算）→ LLM
    
    參數:
        location: 目的地城市
        days: 停留天數
        budget: 每人預算（台幣）
        people: 旅遊人數
        query: 旅遊偏好/特殊需求（已包含興趣和住宿資訊）
        start_date: 出發日期 (optional)
        end_date: 回程日期 (optional)
        accommodation: 住宿偏好 (optional)
        interests: 興趣標籤列表 (optional)
    """

    # FSM：國家固定為日本
    fsm_result: FSMResult = determine_state(
        country="日本",
        budget=budget
    )

    if not fsm_result.allowed_actions:
        return {
            "state": fsm_result.state,
            "reason": fsm_result.reason,
            "response": "❌ 系統不支援此請求"
        }

    response = llm_search(
        location=location,
        days=days,
        budget=budget,
        query=query,
        people=people,
        fsm_result=fsm_result,
        start_date=start_date,
        end_date=end_date,
        accommodation=accommodation,
        interests=interests
    )

    return {
        "state": fsm_result.state,
        "reason": fsm_result.reason,
        "response": response
    }
