import streamlit as st


def render_alarm_ui():
    st.markdown("### ⏰ 약 복용 알림")
    st.caption("🚧 알림 기능은 준비 중이에요!")

    if "alarms" not in st.session_state:
        st.session_state.alarms = []

    with st.form("add_alarm", clear_on_submit=True):
        medicine_name = st.text_input("약 이름")

        # 복용 시간 선택 (아침/점심/저녁 체크박스)
        st.write("복용 시간")
        t_col1, t_col2, t_col3 = st.columns(3)
        with t_col1:
            morning = st.checkbox("🌅 아침")
        with t_col2:
            lunch = st.checkbox("☀️ 점심")
        with t_col3:
            evening = st.checkbox("🌙 저녁")

        memo = st.text_input("메모 (선택)")
        submitted = st.form_submit_button("알림 추가")

        if submitted and medicine_name:
            times = []
            if morning:
                times.append("🌅 아침")
            if lunch:
                times.append("☀️ 점심")
            if evening:
                times.append("🌙 저녁")

            st.session_state.alarms.append({
                "medicine": medicine_name,
                "times": times,
                "memo": memo,
            })
            st.success(f"'{medicine_name}' 알림이 추가되었어요!")
            st.rerun()

    if st.session_state.alarms:
        st.markdown("**등록된 알림**")
        for i, alarm in enumerate(st.session_state.alarms):
            col1, col2 = st.columns([4, 1])
            with col1:
                times_str = ", ".join(alarm.get("times", []))
                # 하위 호환: 기존 time 키 지원
                if not times_str and alarm.get("time"):
                    times_str = alarm["time"]
                text = f"💊 **{alarm['medicine']}** - {times_str}"
                if alarm.get("memo"):
                    text += f"\n{alarm['memo']}"
                st.markdown(text)
            with col2:
                if st.button("🗑️", key=f"del_alarm_{i}"):
                    st.session_state.alarms.pop(i)
                    st.rerun()
    else:
        st.info("등록된 알림이 없어요.")
