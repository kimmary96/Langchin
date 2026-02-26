import urllib.parse
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from prompts import get_system_prompt
from data_manager import load_medical_history

SYMPTOM_DEPARTMENT_MAP = {
    "머리": "신경과",
    "두통": "신경과",
    "어지러": "신경과",
    "배": "내과",
    "소화": "내과",
    "위": "내과",
    "속": "내과",
    "설사": "내과",
    "구토": "내과",
    "메스꺼": "내과",
    "열": "내과",
    "감기": "내과",
    "기침": "내과",
    "목": "이비인후과",
    "코": "이비인후과",
    "귀": "이비인후과",
    "콧물": "이비인후과",
    "눈": "안과",
    "시력": "안과",
    "피부": "피부과",
    "발진": "피부과",
    "가려": "피부과",
    "두드러기": "피부과",
    "허리": "정형외과",
    "무릎": "정형외과",
    "관절": "정형외과",
    "뼈": "정형외과",
    "어깨": "정형외과",
    "치아": "치과",
    "잇몸": "치과",
    "이빨": "치과",
    "가슴": "순환기내과",
    "심장": "순환기내과",
    "숨": "호흡기내과",
    "호흡": "호흡기내과",
    "우울": "정신건강의학과",
    "불안": "정신건강의학과",
    "스트레스": "정신건강의학과",
    "잠": "정신건강의학과",
    "불면": "정신건강의학과",
}


def get_naver_map_link(query):
    encoded = urllib.parse.quote(query)
    return f"https://map.naver.com/v5/search/{encoded}"


HOSPITAL_REQUEST_KEYWORDS = ["병원 추천", "병원 어디", "어디 병원", "어디가 좋을까", "병원 가야"]


def is_hospital_request(user_input):
    return any(kw in user_input for kw in HOSPITAL_REQUEST_KEYWORDS)


def find_department(user_input):
    for keyword, dept in SYMPTOM_DEPARTMENT_MAP.items():
        if keyword in user_input:
            return dept
    return None


def find_department_from_history(chat_history):
    """대화 이력에서 가장 최근 증상 키워드의 진료과를 찾는다."""
    for msg in reversed(chat_history):
        if msg["role"] == "user":
            dept = find_department(msg["content"])
            if dept:
                return dept
    return None


class MomChatbot:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
        )

    def get_response(self, user_input, chat_history):
        medical_history = load_medical_history()
        system_prompt = get_system_prompt(medical_history)

        hospital_requested = is_hospital_request(user_input)

        # 현재 메시지에서 진료과 탐색, 없으면 대화 이력에서 탐색
        department = find_department(user_input)
        if not department and hospital_requested:
            department = find_department_from_history(chat_history)

        extra_context = ""
        if department:
            map_link = get_naver_map_link(f"내 주변 {department}")
            if hospital_requested:
                extra_context = (
                    f"\n\n[시스템 지시: 사용자가 병원을 직접 요청했습니다. "
                    f"즉시 '{department}' 진료과를 안내하고, "
                    f"아래 네이버 지도 링크를 반드시 포함해주세요. "
                    f"'지켜보자', '아직 이르다' 같은 말은 절대 하지 마세요.\n"
                    f"링크: {map_link}]"
                )
            else:
                extra_context = (
                    f"\n\n[시스템 참고: 사용자의 증상과 관련된 진료과는 '{department}'입니다. "
                    f"병원 방문을 권유할 때 이 네이버 지도 링크를 자연스럽게 포함해주세요: {map_link}]"
                )
        elif hospital_requested:
            extra_context = (
                "\n\n[시스템 지시: 사용자가 병원을 직접 요청했지만 아직 증상이 파악되지 않았습니다. "
                "'어디가 불편한지' 한 마디만 물어보세요. '지켜보자' 같은 말은 하지 마세요.]"
            )

        messages = [SystemMessage(content=system_prompt + extra_context)]

        for msg in chat_history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))

        messages.append(HumanMessage(content=user_input))

        try:
            response = self.llm.invoke(messages)
            result = response.content

            # 병원 직접 요청 + 진료과 파악됨 → 네이버 지도 버튼 자동 삽입
            if hospital_requested and department:
                map_link = get_naver_map_link(f"내 주변 {department}")
                if map_link not in result:
                    result += f'\n\n<a href="{map_link}" target="_blank" style="display:inline-block;padding:10px 20px;background:#03C75A;color:white;border-radius:8px;text-decoration:none;font-size:14px;">🏥 근처 {department} 찾기</a>'

            return result
        except Exception:
            return "아이고, 잠깐 문제가 생겼네. 다시 한번 말해줄래?"
