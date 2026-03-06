import re
import urllib.parse
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from prompts import get_system_prompt
from data_manager import load_medical_history, get_diary_entry
from datetime import date

SYMPTOM_DEPARTMENT_MAP = {
    "머리": "신경과", "두통": "신경과", "어지러": "신경과",
    "배가": "내과", "소화": "내과", "위염": "내과", "위가": "내과", "속이": "내과", "명치": "내과",
    "설사": "내과", "구토": "내과", "메스꺼": "내과", "체했": "내과", "열이": "내과",
    "감기": "내과", "기침": "내과", "몸살": "가정의학과", "피로": "가정의학과",
    "목이": "이비인후과", "코가": "이비인후과", "귀가": "이비인후과", "콧물": "이비인후과",
    "눈이": "안과", "시력": "안과",
    "피부가": "피부과", "발진": "피부과", "가려워": "피부과", "가렵": "피부과", "간지러": "피부과", "두드러기": "피부과",
    "허리": "정형외과", "무릎": "정형외과", "관절": "정형외과", "뼈가": "정형외과", "어깨": "정형외과", "삐었": "정형외과", "담이": "정형외과",
    "치아": "치과", "잇몸": "치과", "이빨": "치과",
    "가슴이": "내과", "심장": "내과", "숨이": "내과", "호흡": "내과",
    "우울": "정신건강의학과", "불안": "정신건강의학과", "스트레스": "정신건강의학과", "잠을": "정신건강의학과", "불면": "정신건강의학과",
    "생리": "산부인과", "질염": "산부인과", "자궁": "산부인과", "난소": "산부인과", "다낭성": "산부인과",
    "방광염": "비뇨의학과", "잔뇨": "비뇨의학과",
    # 진료과명 직접 언급 ("산부인과 병원 추천해줘" 등)
    "산부인과": "산부인과", "피부과": "피부과", "정형외과": "정형외과",
    "신경과": "신경과", "이비인후과": "이비인후과", "안과": "안과",
    "치과": "치과", "내과": "내과", "가정의학과": "가정의학과",
    "비뇨의학과": "비뇨의학과", "정신건강의학과": "정신건강의학과"
}


def get_naver_map_link(query):
    encoded = urllib.parse.quote(query)
    return f"https://map.naver.com/v5/search/{encoded}"


# 2. 버튼이 무조건 나올 수 있도록 병원 요청 키워드를 대폭 확장했습니다.
HOSPITAL_REQUEST_KEYWORDS = [
    "병원 추천", "병원 어디", "어디 병원", "어디가 좋을까", "병원 가야", "병원 갈래",
    "링크", "내과", "외과", "정형외과", "이비인후과", "가까운 병원", "근처 병원",
    "피부과", "신경과", "추천해줘", "찾아줘", "추천좀", "추천", "어느 병원", "예약"
]


def detect_medical_add_intent(user_message: str) -> str | None:
    """
    사용자 메시지에서 병력 추가 의도를 감지.
    명시적 추가 요청이 있으면 메시지 반환, 없으면 None 반환.
    """
    explicit = ["병력에 추가", "기록해줘", "저장해줘", "추가해줘"]
    if any(k in user_message for k in explicit):
        return user_message
    return None


def extract_disease_name(user_message: str, llm) -> str:
    """LLM을 사용해 메시지에서 질병명 또는 증상명 추출. 없으면 '없음' 반환."""
    from langchain_core.messages import HumanMessage
    prompt = (
        "다음 문장에서 질병명 또는 증상명만 추출해줘. "
        "한 단어 또는 짧은 명사로만 답해. 없으면 '없음'이라고 답해.\n"
        f"문장: {user_message}"
    )
    try:
        return llm.invoke([HumanMessage(content=prompt)]).content.strip()
    except Exception:
        return "없음"


def is_hospital_request(user_input):
    return any(kw in user_input for kw in HOSPITAL_REQUEST_KEYWORDS)


def find_department(user_input):
    for keyword, dept in SYMPTOM_DEPARTMENT_MAP.items():
        if keyword in user_input:
            return dept
    return None


def find_department_from_history(chat_history, limit=5):
    """최근 대화 이력(최대 limit개 메시지) 중 user 발화에서 진료과를 찾는다.
    현재 메시지보다 우선순위가 낮으므로, 현재 메시지에서 이미 찾은 경우 호출하지 않는다."""
    recent = chat_history[-limit:] if len(chat_history) > limit else chat_history
    for msg in reversed(recent):
        if msg["role"] == "user":
            dept = find_department(msg["content"])
            if dept:
                return dept
    return None


def convert_links_to_html(text):
    """마크다운 링크 [text](url)를 클릭 가능한 HTML <a> 태그로 변환"""
    return re.sub(
        r'\[([^\]]+)\]\((https?://[^\)]+)\)',
        r'<a href="\2" target="_blank" style="color:#03C75A;font-weight:bold;text-decoration:underline;">\1</a>',
        text
    )


class MomChatbot:
    def __init__(self, use_agent: bool = True):
        self.use_agent = use_agent
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
        )

    # ── 데이터 변환 헬퍼 ────────────────────────────────────────────────────

    @staticmethod
    def _build_medical_history_str(medical_history_list: list) -> str:
        """병력 리스트 → agent에 전달할 문자열로 변환."""
        if not medical_history_list:
            return ""
        diseases = [item.get("disease", "") for item in medical_history_list if item.get("disease")]
        memos = [item.get("memo", "") for item in medical_history_list if item.get("memo")]
        text = f"진단: {', '.join(diseases) if diseases else '없음'} / 복용약: 없음 / 알레르기: 없음"
        if memos:
            text += f" / 메모: {'; '.join(memos)}"
        return text

    @staticmethod
    def _build_diary_str(diary_entry: dict) -> str:
        """건강일기 딕셔너리 → agent에 전달할 문자열로 변환."""
        if not diary_entry:
            return ""
        parts = []
        if diary_entry.get("condition"):
            parts.append(f"컨디션: {diary_entry['condition']}")
        symptoms = diary_entry.get("symptoms", [])
        if symptoms:
            parts.append(f"증상: {', '.join(symptoms)}")
        if diary_entry.get("bowel"):
            parts.append(f"배변: {diary_entry['bowel']}")
        if diary_entry.get("sleep_hours") is not None:
            parts.append(f"수면: {diary_entry['sleep_hours']}시간")
        exercise = diary_entry.get("exercise", [])
        if exercise:
            parts.append(f"운동: {', '.join(exercise)}")
        hospital = diary_entry.get("hospital", [])
        if hospital:
            parts.append(f"병원: {', '.join(hospital)}")
        if diary_entry.get("memo"):
            parts.append(f"메모: {diary_entry['memo']}")
        return " / ".join(parts)

    # ── 후처리 (기존 HTML 변환 + 병원 버튼 로직 그대로) ─────────────────────

    @staticmethod
    def _postprocess(text: str, hospital_requested: bool, department: str) -> str:
        result = re.sub(
            r'\[([^\]]+)\]\((https?://[^\)]+)\)',
            r'<a href="\2" target="_blank" style="color:#8BC34A;font-weight:bold;text-decoration:underline;">\1</a>',
            text
        )

        # --- 수정된 부분: 파이썬 코드가 무조건 안전하게 버튼을 추가 ---
        # 병원 직접 요청 + 진료과 파악됨 → 무조건 네이버 지도 버튼 삽입
        if hospital_requested and department:
            url = f"https://map.naver.com/v5/search/{urllib.parse.quote('내 주변 ' + department)}"
            link_html = f'<div style="margin-top:10px;"><a href="{url}" target="_blank" style="display:inline-block;padding:8px 16px;background:#8BC34A;color:white;border-radius:8px;text-decoration:none;font-size:14px;font-weight:bold;">🏥 근처 {department} 찾기</a></div>'
            result += link_html

        return result

    # ── 공개 메서드 ──────────────────────────────────────────────────────────

    def get_response(self, user_input: str, chat_history: list, conversation_summary: str = "") -> dict:
        """
        Returns:
            {"response": str, "agent_steps": list}
        """
        medical_history_list = load_medical_history()
        diary_entry = get_diary_entry(date.today().isoformat())

        hospital_requested = is_hospital_request(user_input)
        department = find_department(user_input)
        if not department and hospital_requested:
            department = find_department_from_history(chat_history)

        if self.use_agent:
            return self._response_via_agent(
                user_input, medical_history_list, diary_entry,
                hospital_requested, department,
                chat_history,
                conversation_summary=conversation_summary,
            )
        return self._response_via_legacy(
            user_input, chat_history, medical_history_list, diary_entry,
            hospital_requested, department,
        )

    # ── agent 경로 ───────────────────────────────────────────────────────────

    def _response_via_agent(
        self,
        user_input: str,
        medical_history_list: list,
        diary_entry: dict,
        hospital_requested: bool,
        department: str,
        chat_history: list,
        conversation_summary: str = "",
    ) -> dict:
        from agent.runner import run_agent

        medical_history_str = self._build_medical_history_str(medical_history_list)
        today_diary_str = self._build_diary_str(diary_entry)

        # 병원 요청 컨텍스트를 user_message에 첨부
        message_with_context = user_input
        if hospital_requested and department:
            message_with_context += (
                "\n\n[시스템 참고: 사용자가 병원을 찾고 있습니다. "
                "지도 버튼은 시스템이 자동으로 추가하니, 다정하게 병원 방문만 권유하세요.]"
            )
        elif hospital_requested and not department:
            message_with_context += (
                "\n\n[시스템 참고: 사용자가 병원을 찾고 있지만 증상이 파악되지 않았습니다. "
                "어디가 불편한지 다정하게 물어보세요.]"
            )

        try:
            agent_result = run_agent(
                user_message=message_with_context,
                medical_history=medical_history_str,
                today_diary=today_diary_str,
                recent_history=chat_history[-6:],
                conversation_summary=conversation_summary,
            )
            raw_response = agent_result.get("response", "")
            agent_steps = agent_result.get("agent_steps", [])
        except Exception as e:
            print(f"[MomChatbot] agent 실행 실패, legacy로 폴백: {e}")
            return self._response_via_legacy(
                user_input, chat_history, medical_history_list, diary_entry,
                hospital_requested, department,
            )

        result = self._postprocess(raw_response, hospital_requested, department)
        return {"response": result, "agent_steps": agent_steps}

    # ── legacy 경로 (기존 LangChain 방식, 폴백용) ────────────────────────────

    def _response_via_legacy(
        self,
        user_input: str,
        chat_history: list,
        medical_history_list: list,
        diary_entry: dict,
        hospital_requested: bool,
        department: str,
    ) -> dict:
        system_prompt = get_system_prompt(medical_history_list)

        if diary_entry:
            diary_context = "\n\n[오늘의 건강일기 기록]\n"
            if diary_entry.get("condition"):
                diary_context += f"- 컨디션: {diary_entry['condition']}\n"
            symptoms = diary_entry.get("symptoms", [])
            if symptoms:
                diary_context += f"- 증상: {', '.join(symptoms)}\n"
            if diary_entry.get("bowel"):
                diary_context += f"- 배변: {diary_entry['bowel']}\n"
            if diary_entry.get("sleep_hours") is not None:
                diary_context += f"- 수면: {diary_entry['sleep_hours']}시간\n"
            exercise = diary_entry.get("exercise", [])
            if exercise:
                diary_context += f"- 운동: {', '.join(exercise)}\n"
            hospital = diary_entry.get("hospital", [])
            if hospital:
                diary_context += f"- 병원: {', '.join(hospital)}\n"
            if diary_entry.get("memo"):
                diary_context += f"- 메모: {diary_entry['memo']}\n"
            system_prompt += diary_context

        extra_context = ""
        if hospital_requested and department:
            extra_context = (
                f"\n\n[시스템 지시: 사용자가 병원을 직접 찾고 있습니다. 지도 버튼은 시스템이 자동으로 추가합니다. "
                f"당신은 진료과·병원 종류 이름을 절대 언급하지 말고, "
                f"'근처에 갈 만한 곳 찾아봤어. 늦지 않게 가보자'라는 식으로 다정하게 병원 방문만 권유하세요.]"
            )
        elif hospital_requested and not department:
            extra_context = (
                "\n\n[시스템 지시: 사용자가 병원을 찾고 있지만 아직 증상을 모릅니다. "
                "어디가 어떻게 불편한지 다정하게 물어보세요.]"
            )
        elif department:
            extra_context = (
                f"\n\n[시스템 참고: 사용자의 증상과 관련된 진료과는 '{department}'입니다. "
                f"대화 맥락상 필요하다면 자연스럽게 병원 방문을 제안해 보세요.]"
            )

        messages = [SystemMessage(content=system_prompt + extra_context)]
        for msg in chat_history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))
        messages.append(HumanMessage(content=user_input))

        try:
            raw_response = self.llm.invoke(messages).content
        except Exception:
            return {
                "response": "아이고, 잠깐 문제가 생겼네. 다시 한번 말해줄래?",
                "agent_steps": [],
            }

        result = self._postprocess(raw_response, hospital_requested, department)
        return {"response": result, "agent_steps": []}
