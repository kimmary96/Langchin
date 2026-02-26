import streamlit as st
from datetime import datetime
from data_manager import load_medical_history, save_medical_history
from components.alarm_ui import render_alarm_ui


def render_sidebar():
    """Streamlit 기본 사이드바에 병력관리 + 알림 렌더링"""
    with st.sidebar:
        st.header("🏥 내 병력 관리")

        medical_history = load_medical_history()

        if medical_history:
            st.subheader("등록된 병력")
            for i, item in enumerate(medical_history):
                col1, col2 = st.columns([4, 1])
                with col1:
                    text = f"**{item.get('disease', '')}**"
                    if item.get('date'):
                        text += f" ({item['date']})"
                    if item.get('memo'):
                        text += f"\n{item['memo']}"
                    st.markdown(text)
                with col2:
                    if st.button("🗑️", key=f"del_{i}"):
                        medical_history.pop(i)
                        save_medical_history(medical_history)
                        st.rerun()
                st.divider()
        else:
            st.info("등록된 병력이 없어요.")

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

        st.divider()
        render_alarm_ui()
