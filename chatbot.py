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
    "생리": "산부인과", "질염": "산부인과", "자궁": "산부인과", "방광염": "비뇨의학과", "잔뇨": "비뇨의학과"
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


def convert_links_to_html(text):
    """마크다운 링크 [text](url)를 클릭 가능한 HTML <a> 태그로 변환"""
    return re.sub(
        r'\[([^\]]+)\]\((https?://[^\)]+)\)',
        r'<a href="\2" target="_blank" style="color:#03C75A;font-weight:bold;text-decoration:underline;">\1</a>',
        text
    )


class MomChatbot:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
        )

    def get_response(self, user_input, chat_history):
        medical_history = load_medical_history()
        system_prompt = get_system_prompt(medical_history)

        diary_entry = get_diary_entry(date.today().isoformat())
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

        hospital_requested = is_hospital_request(user_input)

        # 현재 메시지에서 진료과 탐색, 없으면 대화 이력에서 탐색
        department = find_department(user_input)
        if not department and hospital_requested:
            department = find_department_from_history(chat_history)

        # extra_context = ""
        # if department:
        #     map_link = get_naver_map_link(f"내 주변 {department}")
        #     if hospital_requested:
        #         extra_context = (
        #             f"\n\n[시스템 지시: 사용자가 병원을 직접 요청했습니다. "
        #             f"즉시 '{department}' 진료과를 안내하고, "
        #             f"아래 네이버 지도 링크를 반드시 포함해주세요. "
        #             f"'지켜보자', '아직 이르다' 같은 말은 절대 하지 마세요.\n"
        #             f"링크: {map_link}]"
        #         )
        #     else:
        #         extra_context = (
        #             f"\n\n[시스템 참고: 사용자의 증상과 관련된 진료과는 '{department}'입니다. "
        #             f"병원 방문을 권유할 때 이 네이버 지도 링크를 자연스럽게 포함해주세요: {map_link}]"
        #         )
        # elif hospital_requested:
        #     extra_context = (
        #         "\n\n[시스템 지시: 사용자가 병원을 직접 요청했지만 아직 증상이 파악되지 않았습니다. "
        #         "'어디가 불편한지' 한 마디만 물어보세요. '지켜보자' 같은 말은 하지 마세요.]"
        #     )

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
            response = self.llm.invoke(messages)
            result = response.content
            # result = convert_links_to_html(result)
            result = re.sub(
                r'\[([^\]]+)\]\((https?://[^\)]+)\)',
                r'<a href="\2" target="_blank" style="color:#8BC34A;font-weight:bold;text-decoration:underline;">\1</a>',
                result
            )

            # 병원 직접 요청 + 진료과 파악됨 → 네이버 지도 링크 fallback
            # if hospital_requested and department:
            #     if "map.naver.com" not in result:
            #         url = f"https://map.naver.com/v5/search/{urllib.parse.quote(department)}"
            #         link_html = f'<a href="{url}" target="_blank" style="color:#03C75A;font-weight:bold;">🏥 근처 {department} 찾기</a>'
            #         result += f"<br><br>{link_html}"

            # --- 수정된 부분: 파이썬 코드가 무조건 안전하게 버튼을 추가 ---
            # 병원 직접 요청 + 진료과 파악됨 → 무조건 네이버 지도 버튼 삽입
            if hospital_requested and department:
                url = f"https://map.naver.com/v5/search/{urllib.parse.quote('내 주변 ' + department)}"
                link_html = f'<div style="margin-top:10px;"><a href="{url}" target="_blank" style="display:inline-block;padding:8px 16px;background:#8BC34A;color:white;border-radius:8px;text-decoration:none;font-size:14px;font-weight:bold;">🏥 근처 {department} 찾기</a></div>'
                result += link_html

            return result
        except Exception:
            return "아이고, 잠깐 문제가 생겼네. 다시 한번 말해줄래?"
