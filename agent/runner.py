from langchain_core.messages import SystemMessage, HumanMessage
from agent.graph import build_graph
from agent.llm import get_llm
from agent.nodes import report_node
from agent.state import AgentState

_graph = None


def _get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


def summarize_history(messages: list) -> str:
    """최근 6개 대화를 3문장으로 요약"""
    if not messages:
        return ""

    conversation = "\n".join([
        f"{'사용자' if m['role'] == 'user' else '엄마품'}: {m['content']}"
        for m in messages[-6:]
    ])

    llm = get_llm(temperature=0.3)
    response = llm.invoke([
        SystemMessage(content="""다음 대화를 3문장 이내로 요약해줘.
반드시 아래 항목 위주로만 작성해:
- 언급된 증상
- 언급된 병명
- 사용자 감정 상태
- 특별한 요청사항
200자를 넘지 말 것."""),
        HumanMessage(content=conversation)
    ])
    return response.content


def update_summary(existing_summary: str, new_summary: str) -> str:
    """기존 요약과 새 요약을 합쳐서 200자 이내로 유지"""
    combined = f"{existing_summary} / {new_summary}".strip(" /")
    return combined[-200:]  # 최근 200자만 유지


def run_agent(
    user_message: str,
    medical_history: str,
    today_diary: str = "",
    recent_history: list = [],
    conversation_summary: str = "",
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
        "recent_history": recent_history,
        "conversation_summary": conversation_summary,
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
        "recent_history": [],
        "conversation_summary": "",
    }

    result = report_node(dummy_state)
    return result.get("report", {})
