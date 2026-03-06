import streamlit as st
import calendar
from datetime import datetime, date
from data_manager import (
    get_diary_entry,
    save_diary_entry,
    delete_diary_entry,
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


def _render_diary_view(selected_date):
    """기존 건강일기 조회 (읽기 전용)"""
    existing = get_diary_entry(selected_date)
    if not existing:
        return False

    st.markdown(f"""
    <div style="background:#5C9E6E; border-radius:2px; padding:2px;
                margin-top:6px; box-shadow:0 2px 12px rgba(0,0,0,0.06);
                border:6px solid #3A7A50;">
        <div style="font-family:'Noto Serif KR',serif; font-size:15px;
                    font-weight:100; margin-bottom:6px;">    📋 {selected_date} 건강일기</div>
    </div>
    """, unsafe_allow_html=True)

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

    # 년/월 선택 (2열)
    col1, col2 = st.columns(2)
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

    # 선택된 날짜 초기화 (기본값: 오늘)
    if "selected_diary_date" not in st.session_state:
        st.session_state.selected_diary_date = today.isoformat()

    dates_with_records = get_dates_with_records()
    cal = calendar.monthcalendar(selected_year, selected_month)
    weekdays = ["월", "화", "수", "목", "금", "토", "일"]
    # 캘린더 버튼 CSS
    st.markdown("""
    <style>
    .cal-header-row {
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        gap: 1px;
        margin-bottom: 1px;
    }
    .cal-header-cell {
        text-align: center;
        font-size: 12px;
        font-weight: 600;
        color: #8A8A8A;
        padding: 4px 0;
    }
    </style>
    """, unsafe_allow_html=True)

    # 요일 헤더
    st.markdown(
        '<div class="cal-header-row">' +
        ''.join(f'<div class="cal-header-cell">{d}</div>' for d in weekdays) +
        '</div>',
        unsafe_allow_html=True,
    )

    # [순서 1] 버튼 렌더링 (스타일 없이)
    for week in cal:
        cols = st.columns(7)
        for j, day in enumerate(week):
            with cols[j]:
                if day == 0:
                    st.markdown(
                        "<div style='height:36px'></div>",
                        unsafe_allow_html=True,
                    )
                else:
                    date_str = f"{selected_year}-{selected_month:02d}-{day:02d}"
                    if st.button(
                        str(day),
                        key=f"cal_{selected_year}_{selected_month}_{day}",
                        use_container_width=True,
                        help=str(day),
                    ):
                        st.session_state.selected_diary_date = date_str
                        st.session_state.diary_editing = False

    # [순서 2] 버튼 루프 후 최신 selected_diary_date 기준으로 재계산
    selected_date_str = st.session_state.selected_diary_date
    date_style_map = {}
    for week in cal:
        for day in week:
            if day == 0:
                continue
            date_str = f"{selected_year}-{selected_month:02d}-{day:02d}"
            has_record = date_str in dates_with_records
            is_today = date_str == today.isoformat()
            is_selected = date_str == selected_date_str
            if is_selected and has_record:
                date_style_map[day] = "selected-record"
            elif is_selected:
                date_style_map[day] = "selected"
            elif has_record:
                date_style_map[day] = "has-record"
            elif is_today:
                date_style_map[day] = "today"

    # [순서 3] date_style_map 기준 CSS 생성 및 주입
    css_rules = ""
    for day, style_type in date_style_map.items():
        sel = f'div:has(button[title="{day}"]) button, div:has(button[aria-label="{day}"]) button'
        if style_type == "has-record":
            css_rules += f"{sel} {{ background-color:#5C9E6E!important; color:white!important; border-color:#5C9E6E!important; }}\n"
        elif style_type == "today":
            css_rules += f"{sel} {{ color:#5C9E6E!important; font-weight:700!important; outline:2px solid #5C9E6E!important; outline-offset:-2px!important; }}\n"
        elif style_type == "selected":
            css_rules += f"{sel} {{ background:white!important; color:#5C9E6E!important; outline:2px solid #5C9E6E!important; outline-offset:-2px!important; font-weight:700!important; }}\n"
        elif style_type == "selected-record":
            css_rules += f"{sel} {{ background:#3A7A50!important; color:white!important; border-color:#3A7A50!important; font-weight:700!important; }}\n"
    if css_rules:
        st.markdown(f"<style>{css_rules}</style>", unsafe_allow_html=True)

    # 선택된 날짜의 건강일기
    sel_date = st.session_state.selected_diary_date
    has_existing = get_diary_entry(sel_date) is not None

    if has_existing and not st.session_state.get("diary_editing"):
        _render_diary_view(sel_date)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✏️ 수정하기", key="edit_diary", use_container_width=True):
                st.session_state.diary_editing = True
        with col2:
            if st.button("🗑️ 삭제하기", key="delete_diary", use_container_width=True):
                delete_diary_entry(sel_date)
                st.rerun()
    else:
        _render_diary_form(sel_date)
