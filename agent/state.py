from typing import TypedDict


class AgentState(TypedDict):
    user_message: str        # 사용자 입력
    medical_history: str     # 등록된 병력 문자열 (data_manager에서 변환)
    today_diary: str         # 오늘 건강일기 문자열
    plan: str                # Plan 노드 전략
    search_needed: bool      # 웹 검색 필요 여부
    search_query: str        # 검색 키워드
    search_results: str      # 검색 결과
    response: str            # Execute 노드 답변
    is_sufficient: bool      # Refine 품질 평가
    refinement_feedback: str # Refine 개선 피드백
    retry_count: int         # 재시도 횟수
    agent_steps: list        # 처리 단계 로그 (Streamlit 사이드바 표시용)
