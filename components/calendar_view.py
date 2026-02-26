import streamlit as st
import calendar
from datetime import datetime, date
from data_manager import (
    get_diary_entry,
    save_diary_entry,
    get_dates_with_records,
)

# ── 건강일기 카테고리 정의 ──
CONDITIONS = ["😄 매우 좋음", "😊 좋음", "😐 보통", "😔 나쁨", "😫 매우 나쁨"]

SYMPTOMS = [
    "🤕 두통", "🤢 구역감", "💩 복통", "🌡️ 발열",
    "😴 극심한 피로", "🤧 콧물/기침", "💊 근육통", "😵 어지러움",
]

BOWEL = ["✅ 건강함", "💧 설사", "🟢 초록똥", "🔒 변비", "❓ 기록 안 함"]

EXERCISE = [
    "🚶 걷기", "🏃 달리기", "🚴 실내자전거",
    "🧘 스트레칭/요가", "💪 근력운동", "❌ 운동 안 함",
]

HOSPITAL = ["💉 주사 처방", "🩸 피검사", "💊 약 처방", "🏥 입원", "❌ 방문 안 함"]


def _render_diary_form(selected_date):
    """아이콘 선택 방식 건강일기 폼"""
    existing = get_diary_entry(selected_date)

    # 기존 데이터 로드 (하위 호환)
    def _get_list(entry, key):
        if not entry:
            return []
        val = entry.get(key, [])
        if isinstance(val, str):
            return [val] if val else []
        return val

    raw_condition = existing.get("condition", None) if existing else None
    default_condition = raw_condition if raw_condition in CONDITIONS else None
    default_symptoms = [s for s in _get_list(existing, "symptoms") if s in SYMPTOMS]
    raw_bowel = existing.get("bowel", None) if existing else None
    default_bowel = raw_bowel if raw_bowel in BOWEL else None
    default_sleep = existing.get("sleep_hours", 7.0) if existing else 7.0
    default_exercise = [e for e in _get_list(existing, "exercise") if e in EXERCISE]
    default_hospital = [h for h in _get_list(existing, "hospital") if h in HOSPITAL]
    default_memo = existing.get("memo", "") if existing else ""

    st.divider()
    st.markdown(f"### 📋 {selected_date} 건강일기")

    # 컨디션 (1개 선택)
    st.markdown("**컨디션**")
    condition = st.pills(
        "컨디션 선택", CONDITIONS,
        selection_mode="single",
        default=default_condition,
        key="diary_condition",
        label_visibility="collapsed",
    )

    # 증상 (복수 선택)
    st.markdown("**증상**")
    symptoms = st.pills(
        "증상 선택", SYMPTOMS,
        selection_mode="multi",
        default=default_symptoms,
        key="diary_symptoms",
        label_visibility="collapsed",
    )

    # 배변 (1개 선택)
    st.markdown("**배변**")
    bowel = st.pills(
        "배변 선택", BOWEL,
        selection_mode="single",
        default=default_bowel,
        key="diary_bowel",
        label_visibility="collapsed",
    )

    # 수면
    st.markdown("**수면**")
    sleep_hours = st.slider(
        "수면 시간",
        min_value=0.0, max_value=12.0, value=float(default_sleep), step=0.5,
        format="%.1f시간",
        key="diary_sleep",
        label_visibility="collapsed",
    )

    # 운동 (복수 선택)
    st.markdown("**운동**")
    exercise = st.pills(
        "운동 선택", EXERCISE,
        selection_mode="multi",
        default=default_exercise,
        key="diary_exercise",
        label_visibility="collapsed",
    )

    # 병원 방문 (복수 선택)
    st.markdown("**병원 방문**")
    hospital = st.pills(
        "병원 방문 선택", HOSPITAL,
        selection_mode="multi",
        default=default_hospital,
        key="diary_hospital",
        label_visibility="collapsed",
    )

    # 메모
    memo = st.text_area("메모 (선택)", value=default_memo, key="diary_memo")

    # 저장 버튼
    if st.button("💾 저장하기", key="save_diary", type="primary", use_container_width=True):
        entry = {
            "condition": condition,
            "symptoms": list(symptoms) if symptoms else [],
            "bowel": bowel,
            "sleep_hours": sleep_hours,
            "exercise": list(exercise) if exercise else [],
            "hospital": list(hospital) if hospital else [],
            "memo": memo,
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        save_diary_entry(selected_date, entry)
        st.session_state.diary_editing = False
        st.session_state.show_calendar_dialog = False
        st.rerun()


def _render_diary_view(selected_date):
    """기존 건강일기 조회 (읽기 전용)"""
    existing = get_diary_entry(selected_date)
    if not existing:
        return False

    st.divider()
    st.markdown(f"### 📋 {selected_date} 건강일기")

    if existing.get("condition"):
        st.markdown(f"**컨디션:** {existing['condition']}")

    symptoms = existing.get("symptoms", [])
    if isinstance(symptoms, str):
        symptoms = [symptoms] if symptoms else []
    if symptoms:
        st.markdown(f"**증상:** {', '.join(symptoms)}")

    if existing.get("bowel"):
        st.markdown(f"**배변:** {existing['bowel']}")
    if existing.get("sleep_hours") is not None:
        st.markdown(f"**수면:** {existing['sleep_hours']}시간")

    exercise = existing.get("exercise", [])
    if exercise:
        st.markdown(f"**운동:** {', '.join(exercise)}")

    hospital = existing.get("hospital", [])
    if hospital:
        st.markdown(f"**병원:** {', '.join(hospital)}")

    if existing.get("memo"):
        st.markdown(f"**메모:** {existing['memo']}")

    return True


@st.dialog("📅 건강 캘린더", width="large")
def show_calendar_dialog():
    today = date.today()
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_year = st.selectbox(
            "년도",
            range(2024, today.year + 2),
            index=today.year - 2024,
            key="cal_year",
        )
    with col2:
        selected_month = st.selectbox(
            "월",
            range(1, 13),
            index=today.month - 1,
            key="cal_month",
        )

    days_in_month = calendar.monthrange(selected_year, selected_month)[1]
    dates_with_records = get_dates_with_records()
    day_options = list(range(1, days_in_month + 1))
    day_labels = [
        f"{d}일" + (" 📝" if f"{selected_year}-{selected_month:02d}-{d:02d}" in dates_with_records else "")
        for d in day_options
    ]
    default_day = min(today.day, days_in_month) - 1
    with col3:
        selected_day_idx = st.selectbox(
            "일",
            range(len(day_options)),
            index=default_day,
            format_func=lambda i: day_labels[i],
            key="cal_day",
        )
    selected_date_str = f"{selected_year}-{selected_month:02d}-{day_options[selected_day_idx]:02d}"
    st.session_state.selected_diary_date = selected_date_str
    cal = calendar.monthcalendar(selected_year, selected_month)
    weekdays = ["월", "화", "수", "목", "금", "토", "일"]

    # CSS grid 스타일
    st.markdown("""
    <style>
    .calendar-grid {
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        gap: 4px;
        width: 100%;
    }
    .calendar-day {
        aspect-ratio: 1;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 8px;
        border: 1px solid #ddd;
        font-size: 14px;
        min-width: 0;
        background: white;
    }
    .calendar-day-header {
        font-weight: bold;
        font-size: 13px;
        text-align: center;
        border: none;
        background: transparent;
    }
    .calendar-day-has-record {
        background: #E8F5E9;
        border-color: #4CAF50;
    }
    .calendar-day-empty {
        border: none;
        background: transparent;
    }
    </style>
    """, unsafe_allow_html=True)

    # HTML grid 렌더링
    html = '<div class="calendar-grid">'
    for day_name in weekdays:
        html += f'<div class="calendar-day calendar-day-header">{day_name}</div>'
    for week in cal:
        for day in week:
            if day == 0:
                html += '<div class="calendar-day calendar-day-empty"></div>'
            else:
                date_str = f"{selected_year}-{selected_month:02d}-{day:02d}"
                has_record = date_str in dates_with_records
                cls = "calendar-day calendar-day-has-record" if has_record else "calendar-day"
                html += f'<div class="{cls}">{day}</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

    # 선택된 날짜의 건강일기
    if "selected_diary_date" in st.session_state:
        sel_date = st.session_state.selected_diary_date
        has_existing = get_diary_entry(sel_date) is not None

        if has_existing and not st.session_state.get("diary_editing"):
            _render_diary_view(sel_date)
            if st.button("✏️ 수정하기", key="edit_diary"):
                st.session_state.diary_editing = True
                st.rerun()
        else:
            _render_diary_form(sel_date)
