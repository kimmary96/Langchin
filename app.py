
import os
import time
import random
import base64
import streamlit as st
from datetime import datetime, date
from dotenv import load_dotenv

load_dotenv()

# Streamlit Cloud: st.secrets에서 API 키 로드 (.env 없을 때 fallback)
try:
    if not os.environ.get("OPENAI_API_KEY") and "OPENAI_API_KEY" in st.secrets:
        os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
except Exception:
    pass

from chatbot import MomChatbot


def detect_medical_add_intent(user_message: str):
    explicit = ["병력에 추가", "기록해줘", "저장해줘", "추가해줘"]
    if any(k in user_message for k in explicit):
        return user_message
    return None


def extract_disease_name(user_message: str, llm) -> str:
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
from vision import analyze_medicine_image
from data_manager import save_chat_history, get_chat_history, load_medical_history, save_medical_history
from agent.runner import summarize_history, update_summary
from components.sidebar import render_sidebar
from components.calendar_view import show_calendar_dialog

# 페이지 설정
st.set_page_config(
    page_title="어디가 아프니?",
    page_icon="",
    layout="centered",
)

# CSS 스타일
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500&family=Noto+Serif+KR:wght@600&display=swap');

    /* ── CSS 변수 ── */
    :root {
        --color-bg: #FAFAF7;
        --color-surface: #FFFFFF;
        --color-mom-bubble: #EEF6EE;
        --color-user-bubble: #FFF8E7;
        --color-primary: #5C9E6E;
        --color-primary-light: #8BC4A0;
        --color-text: #2D2D2D;
        --color-text-muted: #8A8A8A;
        --color-border: #E8EDE8;
        --color-danger: #E57373;
    }

    /* ── 전역 ── */
    * { font-family: 'Noto Sans KR', sans-serif; box-sizing: border-box; }

    body, .stApp {
        background-color: var(--color-bg) !important;
    }

    header[data-testid="stHeader"] {
        background: transparent;
    }

    /* ── 레이아웃 ── */
    .main .block-container {
        max-width: 480px !important;
        margin: 0 auto !important;
        padding: 0 16px 120px !important;
    }

    /* ── 채팅 영역 ── */
    .stChatMessageContainer {
        padding-bottom: 160px !important;
    }

    /* ── 말풍선 공통 ── */
    .mom-bubble, .user-bubble {
        display: inline-block;
        font-size: 15px;
        line-height: 1.6;
        color: var(--color-text);
        word-break: keep-all;
        overflow-wrap: break-word;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
        text-align: left;
    }
    .mom-bubble {
        background: var(--color-mom-bubble);
        border-radius: 4px 18px 18px 18px;
        padding: 13px 16px;
        max-width: 78%;
        min-width: 200px;
        margin: 2px 0 2px 8px;
    }
    .user-bubble {
        background: var(--color-user-bubble);
        border-radius: 18px 4px 18px 18px;
        padding: 13px 16px;
        max-width: 78%;
        min-width: 200px;
        margin: 2px 8px 2px 0;
    }

    /* ── 채팅 컨테이너 ── */
    .chat-container-left {
        display: flex;
        justify-content: flex-start;
        margin-bottom: 6px;
        clear: both;
    }
    .chat-container-right {
        display: flex;
        justify-content: flex-end;
        margin-bottom: 6px;
        clear: both;
    }

    /* ── 발신자 레이블 ── */
    .mom-label {
        font-size: 12px;
        color: var(--color-primary);
        font-weight: 500;
        margin-bottom: 4px;
        margin-left: 8px;
    }

    /* ── 채팅 입력창 ── */
    .stChatInput {
        position: fixed !important;
        bottom: 0 !important;
        left: 50% !important;
        transform: translateX(-50%) !important;
        width: 480px !important;
        z-index: 999 !important;
        background: var(--color-surface) !important;
        border-top: 1px solid var(--color-border) !important;
        padding: 8px 16px 12px !important;
    }
    .stChatInput > div {
        border-radius: 24px !important;
        border: 1.5px solid var(--color-border) !important;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06) !important;
        transition: border-color 0.2s !important;
    }
    .stChatInput > div:focus-within {
        border-color: var(--color-primary) !important;
    }

    /* ── 플로팅 버튼 ── */
    .btn-calendar {
        position: fixed;
        top: 16px;
        right: calc(50% - 240px + 16px);
        z-index: 1000;
    }
    .btn-photo {
        position: fixed;
        bottom: 80px;
        right: calc(50% - 240px + 16px);
        z-index: 1000;
    }
    .round-btn {
        width: 52px;
        height: 52px;
        border-radius: 50%;
        border: 1.5px solid var(--color-border);
        background: var(--color-surface);
        font-size: 22px;
        cursor: pointer;
        box-shadow: 0 4px 16px rgba(0,0,0,0.12);
        display: flex;
        align-items: center;
        justify-content: center;
        text-decoration: none;
        color: inherit;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .round-btn:hover {
        transform: scale(1.08);
        box-shadow: 0 6px 20px rgba(0,0,0,0.16);
    }

    /* ── 사이드바 ── */
    [data-testid="stSidebar"] {
        background: #F7F9F7 !important;
        border-right: 1px solid var(--color-border) !important;
    }

    /* ── 버튼 ── */
    .stButton > button {
        background: var(--color-primary) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        font-family: 'Noto Sans KR', sans-serif !important;
        transition: background 0.2s, transform 0.1s !important;
    }
    .stButton > button:hover {
        background: var(--color-primary-light) !important;
        transform: translateY(-1px) !important;
    }

    /* 캘린더 day 버튼: 기본 스타일 오버라이드 */
    [data-testid="stHorizontalBlock"] .stButton > button {
        background: var(--color-surface) !important;
        color: var(--color-text) !important;
        border: 1px solid var(--color-border) !important;
        border-radius: 8px !important;
        padding: 4px 2px !important;
        font-size: 13px !important;
        min-height: 36px !important;
        width: 100% !important;
        transform: none !important;
    }
    [data-testid="stHorizontalBlock"] .stButton > button:hover {
        background: var(--color-mom-bubble) !important;
        transform: none !important;
    }

    /* ── 모바일 반응형 (≤768px) ── */
    @media (max-width: 768px) {
        .main .block-container {
            max-width: 100% !important;
            padding: 0 12px 80px !important;
        }
        .mom-bubble { max-width: 82%; }
        .user-bubble { max-width: 78%; }
        .stChatInput {
            width: 100% !important;
            border-radius: 0 !important;
        }
        .btn-calendar { right: 16px; }
        .btn-photo { right: 16px; }
    }
</style>
""", unsafe_allow_html=True)


def get_greeting():
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "좋은 아침이야!<br>오늘 컨디션은 어때?"
    elif 12 <= hour < 18:
        return "점심은 잘 먹었어?<br>오늘 몸 상태는 어때?"
    else:
        return "오늘 하루도 수고했어~<br>어디 아픈 데는 없지?"


def init_session():
    if "messages" not in st.session_state:
        today = date.today().isoformat()
        history = get_chat_history(today)
        st.session_state.messages = history if history else []
        st.session_state.current_date = today
        st.session_state.greeted = bool(history)
    if "chatbot" not in st.session_state:
        st.session_state.chatbot = MomChatbot()
    if "current_date" not in st.session_state:
        st.session_state.current_date = date.today().isoformat()
    if "greeted" not in st.session_state:
        st.session_state.greeted = False
    if "last_uploaded" not in st.session_state:
        st.session_state.last_uploaded = ""
    if "agent_steps" not in st.session_state:
        st.session_state.agent_steps = []
    if "pending_disease" not in st.session_state:
        st.session_state.pending_disease = None
    if "conversation_summary" not in st.session_state:
        st.session_state.conversation_summary = ""


def check_date_change():
    today = date.today().isoformat()
    if st.session_state.current_date != today:
        if st.session_state.messages:
            save_chat_history(st.session_state.current_date, st.session_state.messages)
        old_history = get_chat_history(today)
        st.session_state.messages = old_history if old_history else []
        st.session_state.current_date = today
        st.session_state.greeted = False
        st.session_state.conversation_summary = ""


def render_chat_message(role, content, animate=False, searched=False):
    if role == "assistant":
        split_messages = [msg.replace("\n", " ").strip() for msg in content.split("|||") if msg.strip()]
        for i, clean_msg in enumerate(split_messages):
            if animate and i > 0:
                time.sleep(random.uniform(1.0, 2.0))
            if searched:
                bubble_extra = ' style="border: 1.5px solid var(--color-primary); background: #F0F9F3;"'
            else:
                bubble_extra = ""
            st.markdown(
                f'<div class="chat-container-left">'
                f'<div><div class="mom-label">🤱 엄마품</div>'
                f'<div class="mom-bubble"{bubble_extra}>{clean_msg}</div></div></div>',
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            f'<div class="chat-container-right">'
            f'<div class="user-bubble">{content}</div></div>',
            unsafe_allow_html=True,
        )


@st.dialog("📷 사진 검색")
def show_photo_dialog():
    st.write("약봉투, 피부, 상처 등 사진을 올려줘")
    uploaded = st.file_uploader(
        "사진 선택",
        type=["jpg", "jpeg", "png"],
        key="photo_upload",
        label_visibility="collapsed",
    )
    if uploaded and uploaded.name != st.session_state.get("last_uploaded"):
        image_bytes = uploaded.read()
        st.image(image_bytes, caption="업로드된 이미지", width=300)
        if st.button("분석하기", type="primary", use_container_width=True):
            with st.spinner("사진을 분석하고 있어... 잠깐만 기다려!"):
                result = analyze_medicine_image(image_bytes)
            st.session_state.last_uploaded = uploaded.name
            st.session_state.messages.append(
                {"role": "user", "content": "📷 [사진 분석 요청]"}
            )
            st.session_state.messages.append(
                {"role": "assistant", "content": result}
            )
            save_chat_history(st.session_state.current_date, st.session_state.messages)
            st.rerun()


def main():
    init_session()
    check_date_change()

    # ── 하단 바 액션 처리 ──
    action = st.query_params.get("action")
    if action:
        st.query_params.clear()
        if action == "calendar":
            st.session_state.show_calendar_dialog = True
        elif action == "photo":
            show_photo_dialog()

    if st.session_state.get("show_calendar_dialog"):
        st.session_state.show_calendar_dialog = False
        show_calendar_dialog()

    # ── 사이드바 (내 정보 + 알림) ──
    render_sidebar()

    # ── 타이틀: 메시지가 없을 때만 표시 ──
    def get_image_base64(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()

    # 2. 다운로드 받으신 이미지의 실제 경로를 적어주세요. (예: "assets/mom_icon.jpg")
    # 파이참 프로젝트 폴더 안에 이미지를 넣고 그 이름을 적어주시면 됩니다.
    image_path = "mom.png"
    img_base64 = get_image_base64(image_path)

    # 3. HTML 렌더링 (f-string 사용)
    if not st.session_state.messages:
        if img_base64:
            # 이미지가 있을 때 (HTML 태그 안의 줄바꿈을 모두 제거하여 한 줄로 연결했습니다)
            st.markdown(f"""
            <div style="text-align:center; padding:28px 0 16px; border-bottom:1px solid var(--color-border); margin-bottom:20px;">
                <img src="data:image/jpeg;base64,{img_base64}" style="width: 80px; height: 80px; border-radius: 50%; object-fit: cover; margin-bottom: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                <div style="font-family:'Noto Serif KR',serif; font-size:22px; font-weight:600; color:var(--color-text); letter-spacing:-0.3px;">어디가 아프니?</div>
                <div style="font-size:13px; color:var(--color-text-muted); margin-top:4px;">엄마처럼 챙겨주는 건강 챗봇</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            # 이미지가 없을 때
            st.markdown("""
            <div style="text-align:center; padding:28px 0 16px; border-bottom:1px solid var(--color-border); margin-bottom:20px;">
                <div style="font-family:'Noto Serif KR',serif; font-size:22px; font-weight:600; color:var(--color-text); letter-spacing:-0.3px;">어디가 아프니?</div>
                <div style="font-size:13px; color:var(--color-text-muted); margin-top:4px;">엄마처럼 챙겨주는 건강 챗봇</div>
            </div>
            """, unsafe_allow_html=True)

    # ── 첫 인사 ──
    if not st.session_state.greeted and not st.session_state.messages:
        greeting = get_greeting()
        st.session_state.messages.append(
            {"role": "assistant", "content": greeting}
        )
        st.session_state.greeted = True

    # ── 채팅 메시지 표시 ──
    animate_last = st.session_state.get("animate_last", False)
    searched_last = st.session_state.get("searched_last", False)
    for i, msg in enumerate(st.session_state.messages):
        is_last = (i == len(st.session_state.messages) - 1)
        should_animate = animate_last and is_last and msg["role"] == "assistant"
        should_searched = searched_last and is_last and msg["role"] == "assistant"
        render_chat_message(msg["role"], msg["content"], animate=should_animate, searched=should_searched)
    if animate_last:
        st.session_state.animate_last = False
    if searched_last:
        st.session_state.searched_last = False

    # ── 병력 추가 성공 메시지 ──
    if st.session_state.get("disease_added_msg"):
        st.success(st.session_state.pop("disease_added_msg"))

    # ── 병력 추가 확인 UI ──
    if st.session_state.get("pending_disease"):
        pending_disease = st.session_state["pending_disease"]
        st.info(f"'{pending_disease}' 병력에 추가할까? 추가하면 앞으로 대화에 반영할게.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("추가할게", key="add_disease_btn", use_container_width=True):
                history = load_medical_history()
                history.append({
                    "disease": pending_disease,
                    "date": date.today().isoformat(),
                    "memo": "",
                })
                save_medical_history(history)
                st.session_state.pending_disease = None
                st.session_state["disease_added_msg"] = f"'{pending_disease}' 병력에 추가했어!"
                st.rerun()
        with col2:
            if st.button("괜찮아", key="skip_disease_btn", use_container_width=True):
                st.session_state.pending_disease = None
                st.rerun()

    # ── 하단 플로팅 버튼 ──
    st.markdown("""
    <a href="?action=calendar" target="_self" class="round-btn btn-calendar">📅</a>
    <a href="?action=photo" target="_self" class="round-btn btn-photo">📷</a>
    """, unsafe_allow_html=True)

    # ── 채팅 입력 ──
    if user_input := st.chat_input("어디가 아프니? 말해봐~"):
        if not user_input.strip():
            st.stop()
        st.session_state.messages.append({"role": "user", "content": user_input})
        render_chat_message("user", user_input)

        with st.spinner("타자치는 중..."):
            result = st.session_state.chatbot.get_response(
                user_input,
                st.session_state.messages[-7:-1],  # 최근 6개 히스토리
                conversation_summary=st.session_state.conversation_summary,
            )

        response = result["response"]
        agent_steps = result.get("agent_steps", [])
        st.session_state.agent_steps = agent_steps
        st.session_state.messages.append({"role": "assistant", "content": response})
        save_chat_history(st.session_state.current_date, st.session_state.messages)
        st.session_state.animate_last = True
        st.session_state.searched_last = any("Tavily 검색 실행됨" in s for s in agent_steps)

        # 6개 대화마다 자동 요약
        if len(st.session_state.messages) % 6 == 0:
            with st.spinner("대화 내용 정리 중..."):
                new_summary = summarize_history(st.session_state.messages)
                st.session_state.conversation_summary = update_summary(
                    st.session_state.conversation_summary,
                    new_summary,
                )
            print(f"[요약 업데이트] {st.session_state.conversation_summary}")

        # 병력 추가 의도 감지
        if detect_medical_add_intent(user_input):
            with st.spinner("병명 확인 중..."):
                disease_name = extract_disease_name(user_input, st.session_state.chatbot.llm)
            if disease_name and disease_name != "없음":
                existing = load_medical_history()
                existing_diseases = [item.get("disease", "") for item in existing]
                if disease_name not in existing_diseases:
                    st.session_state.pending_disease = disease_name

        st.rerun()


if __name__ == "__main__":
    main()
