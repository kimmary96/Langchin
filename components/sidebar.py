import streamlit as st
from datetime import datetime
from data_manager import load_medical_history, save_medical_history, reset_all_data
from components.alarm_ui import render_alarm_ui
from agent.runner import run_report


def render_sidebar():
    """Streamlit 기본 사이드바에 병력관리 + 알림 렌더링"""
    with st.sidebar:
        st.header("🏥 내 병력 관리")

        # 삭제 버튼 축소 CSS
        st.markdown("""
        <style>
            [data-testid="stSidebar"] button[kind="secondary"] {
                padding: 0.15rem 0.1rem;
                min-height: 0;
                font-size: 0.8rem;
                line-height: 1;
            }
        </style>
        """, unsafe_allow_html=True)

        medical_history = load_medical_history()

        # 1) 병력 추가 폼 (상단)
        st.subheader("병력 추가")
        with st.form("add_medical_history", clear_on_submit=True):
            disease = st.text_input("질병/수술명")
            date = st.text_input("시기 (예: 2024-01)", value="")
            memo = st.text_area("메모", value="")
            submitted = st.form_submit_button("추가하기")

            if submitted and disease:
                new_entry = {
                    "disease": disease,
                    "date": date,
                    "memo": memo,
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
                medical_history.append(new_entry)
                save_medical_history(medical_history)
                st.success(f"'{disease}' 병력이 추가되었어요!")
                st.rerun()

        # 2) 등록된 병력 목록 (하단)
        if medical_history:
            st.markdown("**등록된 병력**")
            for i, item in enumerate(medical_history):
                col1, col2 = st.columns([5, 1])
                with col1:
                    text = f"**{item.get('disease', '')}**"
                    if item.get('date'):
                        text += f" ({item['date']})"
                    if item.get('memo'):
                        text += f"\n{item['memo']}"
                    st.markdown(text)
                with col2:
                    if st.button("🗑️", key=f"del_{i}", use_container_width=False):
                        medical_history.pop(i)
                        save_medical_history(medical_history)
                        st.rerun()
                st.divider()
        else:
            st.info("등록된 병력이 없어요.")

        st.divider()
        render_alarm_ui()

        st.divider()
        st.subheader("📋 오늘의 건강 리포트")

        messages = st.session_state.get("messages", [])
        user_turn_count = sum(1 for m in messages if m["role"] == "user")

        if st.button("리포트 만들기", use_container_width=True):
            if user_turn_count < 5:
                st.info("아직 대화가 충분하지 않아. 조금 더 이야기하고 다시 눌러줘!")
            else:
                with st.spinner("리포트 작성 중..."):
                    report = run_report(messages)
                st.session_state.today_report = report
                st.rerun()

        if st.session_state.get("today_report"):
            r = st.session_state.today_report
            st.markdown(f"**증상 요약:** {r.get('symptoms', '')}")
            st.markdown(f"**컨디션 점수:** {'⭐' * r.get('condition_score', 3)} ({r.get('condition_score', 3)}/5)")
            st.markdown(f"💬 {r.get('moms_comment', '')}")
            st.markdown(f"**권고:** {r.get('recommendation', '')}")

        st.divider()
        st.subheader("⚠️ 데모 초기화")
        if st.button("🗑️ 전체 초기화", use_container_width=True):
            st.session_state.confirm_reset = True

        if st.session_state.get("confirm_reset"):
            st.warning("병력, 건강일기, 대화 기록이 모두 삭제됩니다. 계속할까요?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ 확인", type="primary", use_container_width=True):
                    reset_all_data()
                    st.session_state.messages = []
                    st.session_state.greeted = False
                    st.session_state.confirm_reset = False
                    st.rerun()
            with col2:
                if st.button("❌ 취소", use_container_width=True):
                    st.session_state.confirm_reset = False
                    st.rerun()
