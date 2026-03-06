from agent.graph import build_graph
from agent.nodes import report_node
from agent.state import AgentState

_graph = None


def _get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


def run_agent(
    user_message: str,
    medical_history: str,
    today_diary: str = "",
) -> dict:
    """
    에이전트를 실행하고 최종 답변과 처리 단계 로그를 반환합니다.

    Returns:
        {"response": str, "agent_steps": list}
    """
    initial_state: AgentState = {
        "user_message": user_message,
        "medical_history": medical_history,
        "today_diary": today_diary,
        "plan": "",
        "search_needed": False,
        "search_query": "",
        "search_results": "",
        "response": "",
        "is_sufficient": False,
        "refinement_feedback": "",
        "retry_count": 0,
        "agent_steps": [],
    }

    result = _get_graph().invoke(initial_state)

    return {
        "response": result.get("response", ""),
        "agent_steps": result.get("agent_steps", []),
    }


def run_report(conversation_history: list) -> dict:
    """
    대화 기록을 분석해 하루 건강 리포트를 생성합니다.

    Args:
        conversation_history: [{"role": "user"/"assistant", "content": "..."}, ...]

    Returns:
        리포트 딕셔너리 {"symptoms", "condition_score", "moms_comment", "recommendation"}
    """
    # 대화 내용을 단일 문자열로 합산
    lines = []
    for msg in conversation_history:
        role = "사용자" if msg.get("role") == "user" else "AI"
        lines.append(f"{role}: {msg.get('content', '')}")
    conversation_text = "\n".join(lines)

    # report_node는 user_message와 response만 사용
    dummy_state: AgentState = {
        "user_message": conversation_text,
        "medical_history": "",
        "today_diary": "",
        "plan": "",
        "search_needed": False,
        "search_query": "",
        "search_results": "",
        "response": "",
        "is_sufficient": True,
        "refinement_feedback": "",
        "retry_count": 0,
        "agent_steps": [],
    }

    result = report_node(dummy_state)
    return result.get("report", {})
