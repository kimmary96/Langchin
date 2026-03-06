import json
import os
import re
import yaml
from langchain_core.messages import SystemMessage, HumanMessage
from agent.llm import get_llm, get_search_tool
from agent.state import AgentState

_prompts = None


def _load_prompts() -> dict:
    global _prompts
    if _prompts is None:
        path = os.path.join(os.path.dirname(__file__), "prompts.yaml")
        with open(path, "r", encoding="utf-8") as f:
            _prompts = yaml.safe_load(f)
    return _prompts


# ── Plan ────────────────────────────────────────────────────────────────────

def plan_node(state: AgentState) -> dict:
    print("[plan_node] 실행 중...")
    prompts = _load_prompts()

    try:
        llm = get_llm(temperature=0.3)
        user_context = (
            f"사용자 메시지: {state['user_message']}\n"
            f"병력: {state['medical_history'] or '없음'}\n"
            f"오늘 일기: {state['today_diary'] or '없음'}"
        )
        messages = [
            SystemMessage(content=prompts["plan"]),
            HumanMessage(content=user_context),
        ]
        plan_text = llm.invoke(messages).content
    except Exception as e:
        print(f"[plan_node] LLM 호출 실패, 기본 전략으로 폴백: {e}")
        plan_text = (
            "- 전략 요약: 공감 우선 후 일반 건강 조언 제공\n"
            "- 공감 접근: 불편함에 대한 위로\n"
            "- 정보 방향: 일반적인 증상 완화 방법\n"
            "- 검색 필요: 아니오\n"
            "- 위험 플래그: 없음"
        )

    search_needed = "검색 필요: 예" in plan_text
    search_query = ""
    if search_needed:
        for line in plan_text.split("\n"):
            if "검색 키워드:" in line:
                search_query = line.split("검색 키워드:")[-1].strip()
                break

    steps = list(state.get("agent_steps", []))
    steps.append("Plan 완료: 전략 수립됨")

    return {
        "plan": plan_text,
        "search_needed": search_needed,
        "search_query": search_query,
        "search_results": "",
        "agent_steps": steps,
    }


# ── Execute ──────────────────────────────────────────────────────────────────

def execute_node(state: AgentState) -> dict:
    retry_count = state.get("retry_count", 0)
    print(f"[execute_node] 실행 중... (시도 {retry_count + 1}회차)")
    prompts = _load_prompts()
    llm = get_llm(temperature=0.8)

    # search_needed=True인데 아직 검색 결과가 없으면 여기서 검색 실행
    search_results = state.get("search_results", "")
    if state.get("search_needed") and not search_results:
        query = state.get("search_query", state["user_message"])
        search_tool = get_search_tool()
        if search_tool:
            try:
                raw = search_tool.invoke(query)
                if isinstance(raw, list):
                    search_results = "\n".join(
                        f"- {r.get('title', '')}: {r.get('content', '')[:200]}"
                        for r in raw
                    )
                else:
                    search_results = str(raw)
                print(f"[execute_node] Tavily 검색 완료: '{query}'")
            except Exception as e:
                print(f"[execute_node] Tavily 검색 실패: {e}")

    context_parts = [
        f"사용자 메시지: {state['user_message']}",
        f"병력: {state['medical_history'] or '없음'}",
        f"오늘 일기: {state['today_diary'] or '없음'}",
        f"전략: {state.get('plan', '')}",
    ]
    if search_results:
        context_parts.append(f"참고 정보:\n{search_results}")

    # 재시도: 이전 답변 + 피드백 포함
    if retry_count > 0:
        prev_response = state.get("response", "")
        feedback = state.get("refinement_feedback", "")
        if prev_response:
            context_parts.append(f"이전 답변: {prev_response}")
        if feedback:
            context_parts.append(f"개선 요청: {feedback}")

    messages = [
        SystemMessage(content=prompts["execute"]),
        HumanMessage(content="\n".join(context_parts)),
    ]
    response = llm.invoke(messages).content

    steps = list(state.get("agent_steps", []))
    if retry_count > 0:
        steps.append(f"재시도 {retry_count}회차: 답변 개선 중")
    else:
        steps.append("Execute 완료: 답변 생성됨")

    return {
        "response": response,
        "search_results": search_results,
        "agent_steps": steps,
    }


# ── Refine ───────────────────────────────────────────────────────────────────

def refine_node(state: AgentState) -> dict:
    print("[refine_node] 실행 중...")
    prompts = _load_prompts()
    llm = get_llm(temperature=0.1)

    evaluation_input = (
        f"답변: {state['response']}\n"
        f"사용자 메시지: {state['user_message']}\n"
        f"병력: {state['medical_history'] or '없음'}\n"
        f"오늘 일기: {state['today_diary'] or '없음'}"
    )
    messages = [
        SystemMessage(content=prompts["refine"]),
        HumanMessage(content=evaluation_input),
    ]
    raw = llm.invoke(messages).content.strip()
    steps = list(state.get("agent_steps", []))

    is_sufficient = True
    feedback = ""
    score = 7

    try:
        # 정규식으로 {...} JSON 블록 추출
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if not match:
            raise ValueError("JSON 블록을 찾을 수 없음")
        result = json.loads(match.group())
        score = int(result.get("score", 7))
        is_sufficient = score >= 7
        feedback = result.get("feedback", "")
        steps.append(f"Refine 완료: 점수 {score}점, {'충분' if is_sufficient else '재시도 필요'}")
    except Exception as e:
        print(f"[refine_node] JSON 파싱 실패, 통과 처리: {e}")
        steps.append("Refine 완료: 파싱 실패 → 통과 처리")

    return {
        "is_sufficient": is_sufficient,
        "refinement_feedback": feedback,
        "retry_count": state["retry_count"] + 1,
        "agent_steps": steps,
    }


# ── Report ───────────────────────────────────────────────────────────────────

_DEFAULT_REPORT = {
    "symptoms": "오늘 대화에서 증상 정보를 확인할 수 없습니다.",
    "condition_score": 3,
    "moms_comment": "오늘 하루도 수고했어. 몸 잘 챙겨~",
    "recommendation": "충분한 휴식을 취하세요.",
}


def report_node(state: AgentState) -> dict:
    print("[report_node] 실행 중...")
    prompts = _load_prompts()
    llm = get_llm(temperature=0.3)

    conversation = (
        f"사용자: {state['user_message']}\n"
        f"AI: {state.get('response', '')}"
    )
    messages = [
        SystemMessage(content=prompts["report"]),
        HumanMessage(content=conversation),
    ]

    try:
        raw = llm.invoke(messages).content.strip()
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if not match:
            raise ValueError("JSON 블록을 찾을 수 없음")
        report = json.loads(match.group())
    except Exception as e:
        print(f"[report_node] JSON 파싱 실패, 기본 리포트 반환: {e}")
        report = _DEFAULT_REPORT.copy()

    return {"report": report}
