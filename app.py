
import os
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
from vision import analyze_medicine_image
from data_manager import save_chat_history, get_chat_history
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
    .stApp {
        background-color: #FFFFF0;
    }

    header[data-testid="stHeader"] {
        background: transparent;
    }

    /* 모바일 세로 해상도 고정 */
    .main .block-container {
        max-width: 390px !important;
        min-width: 390px !important;
        margin: 0 auto !important;
        padding: 0 !important;
    }

    /* 채팅 영역 하단 여백 확보 */
    .stChatMessageContainer {
        padding-bottom: 160px !important;
    }

    .mom-bubble {
        background-color: #E8F5E9;
        border-radius: 15px 15px 15px 0px;
        padding: 12px 16px;
        margin: 8px 0;
        max-width: 85%;
        display: inline-block;
        font-size: 15px;
        line-height: 1.5;
    }
    .user-bubble {
        background-color: #FFF9C4;
        border-radius: 15px 15px 0px 15px;
        padding: 12px 16px;
        margin: 8px 0;
        max-width: 85%;
        display: inline-block;
        float: right;
        font-size: 15px;
        line-height: 1.5;
    }
    .chat-container-left {
        display: flex;
        justify-content: flex-start;
        margin-bottom: 4px;
        clear: both;
    }
    .chat-container-right {
        display: flex;
        justify-content: flex-end;
        margin-bottom: 4px;
        clear: both;
    }
    .mom-label {
        font-size: 13px;
        color: #666;
        margin-bottom: 2px;
    }

    /* 웰컴 타이틀 스타일 */
    .welcome-title {
        font-size: 2rem;
        font-weight: 700;
        text-align: center;
        margin-top: 20vh;
        color: #2E7D32;
    }
    .welcome-subtitle {
        font-size: 1.1rem;
        text-align: center;
        color: #666;
        margin-top: 8px;
        margin-bottom: 2rem;
    }

    /* 채팅 입력창 고정 */
    .stChatInput {
        position: fixed !important;
        bottom: 0 !important;
        left: 50% !important;
        transform: translateX(-50%) !important;
        width: 390px !important;
        z-index: 999 !important;
    }

    /* 동그란 플로팅 버튼 좌우 분리 */
    .btn-calendar {
        position: fixed;
        top: 16px;
        right: calc(50% - 195px + 16px);
        z-index: 1000;
    }
    .btn-photo {
        position: fixed;
        bottom: 80px;
        right: calc(50% - 195px + 16px);
        z-index: 1000;
    }
    .round-btn {
        width: 52px;
        height: 52px;
        border-radius: 50%;
        border: 1px solid #ddd;
        background: white;
        font-size: 22px;
        cursor: pointer;
        box-shadow: 0 2px 6px rgba(0,0,0,0.15);
        display: flex;
        align-items: center;
        justify-content: center;
        text-decoration: none;
        color: inherit;
    }
    .round-btn:hover {
        background: #f0f0f0;
        box-shadow: 0 3px 8px rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)


def get_greeting():
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "좋은 아침이야! \n오늘은 어디 불편한 데 없어?"
    elif 12 <= hour < 18:
        return "점심은 잘 먹었어? \n오늘 몸 상태는 어때?"
    else:
        return "오늘 하루도 수고했어~ \n어디 아픈 데는 없지?"


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


def check_date_change():
    today = date.today().isoformat()
    if st.session_state.current_date != today:
        if st.session_state.messages:
            save_chat_history(st.session_state.current_date, st.session_state.messages)
        old_history = get_chat_history(today)
        st.session_state.messages = old_history if old_history else []
        st.session_state.current_date = today
        st.session_state.greeted = False


def render_chat_message(role, content):
    if role == "assistant":
        split_messages = [msg.strip() for msg in content.split("|||") if msg.strip()]
        for clean_msg in split_messages:
            st.markdown(
                f'<div class="chat-container-left">'
                f'<div><div class="mom-label">🤱 엄마품</div>'
                f'<div class="mom-bubble">{clean_msg}</div></div></div>',
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
    if not st.session_state.messages:
        st.markdown('<div class="welcome-title">어디가 아프니?</div>', unsafe_allow_html=True)
        st.markdown('<div class="welcome-subtitle">엄마 품으로 오렴 💚</div>', unsafe_allow_html=True)

    # ── 첫 인사 ──
    if not st.session_state.greeted and not st.session_state.messages:
        greeting = get_greeting()
        st.session_state.messages.append(
            {"role": "assistant", "content": greeting}
        )
        st.session_state.greeted = True

    # ── 채팅 메시지 표시 ──
    for msg in st.session_state.messages:
        render_chat_message(msg["role"], msg["content"])

    # ── 하단 플로팅 버튼 ──
    st.markdown("""
    <a href="?action=calendar" target="_self" class="round-btn btn-calendar">📅</a>
    <a href="?action=photo" target="_self" class="round-btn btn-photo">📷</a>
    """, unsafe_allow_html=True)

    # ── 채팅 입력 ──
    if user_input := st.chat_input("어디가 아프니? 말해봐~"):
        st.session_state.messages.append({"role": "user", "content": user_input})
        render_chat_message("user", user_input)

        with st.spinner("타자치는 중..."):
            result = st.session_state.chatbot.get_response(
                user_input, st.session_state.messages[:-1]
            )

        response = result["response"]
        st.session_state.agent_steps = result.get("agent_steps", [])
        st.session_state.messages.append({"role": "assistant", "content": response})
        save_chat_history(st.session_state.current_date, st.session_state.messages)
        st.rerun()


if __name__ == "__main__":
    main()
