import streamlit as st
from datetime import datetime
from data_manager import load_medical_history, save_medical_history, reset_all_data
from components.alarm_ui import render_alarm_ui
from agent.runner import run_report


def render_sidebar():
    """Streamlit 기본 사이드바에 병력관리 + 알림 렌더링"""
    with st.sidebar:
        st.header("🏥 내 병력 관리")

        # 사이드바 전용 CSS
        st.markdown("""
        <style>
            /* === 폼 요소 높이 1/2 축소 (병력추가, 약복용알림) === */
            [data-testid="stSidebar"] [data-testid="stForm"] input {
                padding-top: 3px !important;
                padding-bottom: 3px !important;
                height: 32px !important;
                font-size: 13px !important;
            }
            [data-testid="stSidebar"] [data-testid="stForm"] textarea {
                padding-top: 4px !important;
                padding-bottom: 4px !important;
                min-height: 40px !important;
                font-size: 13px !important;
                line-height: 1.4 !important;
            }
            [data-testid="stSidebar"] [data-testid="stForm"] [data-testid="stFormSubmitButton"] button {
                padding: 0.2rem 0.5rem !important;
                height: 32px !important;
                min-height: 0 !important;
                font-size: 0.8rem !important;
                line-height: 1.2 !important;
            }
            /* === 삭제 버튼 소형 유지 (컬럼 내 비전체너비) === */
            [data-testid="stSidebar"] [data-testid="column"]:last-child .stButton > button:not([style*="width: 100%"]) {
                padding: 0.1rem 0.15rem !important;
                min-height: 0 !important;
                height: 28px !important;
                font-size: 0.8rem !important;
                line-height: 1 !important;
            }
            /* === 대형 액션 버튼 2배 높이 (리포트 만들기, 전체 초기화 등) === */
            [data-testid="stSidebar"] .stButton > button[style*="width: 100%"] {
                min-height: 3.5rem !important;
                padding: 0.8rem 0.5rem !important;
                font-size: 0.9rem !important;
            }
            .sidebar-section-title {
                font-family: 'Noto Serif KR', serif;
                font-size: 15px;
                font-weight: 600;
                color: #2D2D2D;
                margin: 20px 0 12px;
                padding-bottom: 8px;
                border-bottom: 1px solid #E8EDE8;
            }
            .medical-tag {
                display: inline-block;
                background: #EEF6EE;
                border: 1px solid #E8EDE8;
                border-radius: 20px;
                padding: 5px 12px;
                font-size: 13px;
                color: #2D2D2D;
                margin: 3px 2px;
            }
        </style>
        """, unsafe_allow_html=True)

        medical_history = load_medical_history()

        # 1) 병력 추가 폼 (상단)
        st.subheader("병력 추가")
        with st.form("add_medical_history", clear_on_submit=True):
            disease = st.text_input("질병/수술명")
            date = st.text_input("시기 (예: 2024-01)", value="")
            memo = st.text_area("메모", value="", height=60)
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
            score = r.get('condition_score', 3)
            stars = '⭐' * score
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#EEF6EE 0%,#F7FBF7 100%);
                        border-radius:16px; padding:18px; border:1px solid #E8EDE8; margin:8px 0;">
                <div style="font-family:'Noto Serif KR',serif; font-size:15px;
                            font-weight:600; margin-bottom:12px; color:#2D2D2D;">오늘의 건강 리포트</div>
                <div style="font-size:13px; color:#8A8A8A; margin-bottom:4px;">컨디션</div>
                <div style="font-size:16px; margin-bottom:10px;">{stars} <span style="font-size:13px;color:#8A8A8A;">({score}/5)</span></div>
                <div style="font-size:13px; color:#8A8A8A; margin-bottom:2px;">증상 요약</div>
                <div style="font-size:14px; margin-bottom:10px; color:#2D2D2D;">{r.get('symptoms', '')}</div>
                <div style="font-size:14px; color:#5C9E6E; margin-bottom:8px;">💬 {r.get('moms_comment', '')}</div>
                <div style="font-size:13px; background:white; border-radius:10px;
                            padding:10px 12px; color:#2D2D2D; border:1px solid #E8EDE8;">
                    {r.get('recommendation', '')}
                </div>
            </div>
            """, unsafe_allow_html=True)

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
