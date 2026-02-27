# 어디가 아프니? 🤱

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B?logo=streamlit&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-0.x-1C3C3C?logo=langchain&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-412991?logo=openai&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

**30~50대 여성을 위한 엄마 같은 AI 건강 케어 챗봇**

---

## 서비스 소개

**어디가 아프니?** 는 30~50대 여성 타겟의 AI 건강 케어 서비스입니다.

> *"그냥 아프다고만 하면 어디가 어떻게 아픈지 꼼꼼히 물어봐 주는, 걱정 많은 엄마 같은 AI"*

- **타겟 유저**: 30~50대 여성
- **페르소나**: 공감 먼저, 잔소리 없는 엄마 말투의 AI
- **핵심 가치**: 공감 → 증상 파악 → 진료과 안내 → 건강 기록

---

## 핵심 기능

| # | 기능 | 상태 |
|---|------|------|
| 1 | 🤱 AI 채팅 (공감 대화 + 병원 안내) | ✅ |
| 2 | 📷 사진 분석 (약 포장지, 상처, 피부 이상) | ✅ |
| 3 | 📅 건강일기 캘린더 (7개 카테고리) | ✅ |
| 4 | 🏥 병력 관리 | ✅ |
| 5 | ⏰ 복약 알림 | 🚧 WIP |
| 6 | 🗑️ 전체 초기화 (데모용) | ✅ |

---

### 1. 🤱 AI 채팅

- **LangChain + GPT-4o-mini** 기반 공감 대화
- 증상 키워드 자동 감지 → 진료과 매핑 (내과, 산부인과, 정형외과 등 20개+)
- 병원 방문 요청 시 **네이버 지도** 링크 버튼 자동 삽입
- 등록된 병력 + 오늘의 건강일기를 시스템 프롬프트에 자동 반영
- 대화 이력을 날짜별 JSON으로 자동 저장

### 2. 📷 사진 분석

- **OpenAI Vision API (GPT-4o)** 사용
- 분석 가능 대상: 약 봉투/포장지, 피부 이상, 멍·상처·화상
- 엄마 말투로 결과 전달 ("어머, 이거 멍이 꽤 크게 들었네.")
- 의학적 진단 없이 묘사 + 심각 시 병원 권유

### 3. 📅 건강일기 캘린더

7개 카테고리를 아이콘 선택(pills) 방식으로 간편 입력:

| 카테고리 | 내용 |
|---|---|
| 컨디션 | 😄 매우 좋음 ~ 😫 매우 나쁨 (5단계) |
| 증상 | 두통, 구역감, 복통, 발열, 피로, 콧물/기침, 근육통, 어지러움 |
| 배변 | 건강함, 설사, 초록똥, 변비 |
| 수면 | 0~12시간 슬라이더 (0.5h 단위) |
| 운동 | 걷기, 달리기, 실내자전거, 스트레칭/요가, 근력운동 |
| 병원 방문 | 주사/피검사/약 처방/입원 |
| 메모 | 자유 텍스트 |

기록이 있는 날짜는 캘린더에 📝 표시 및 초록색 하이라이트.

### 4. 🏥 병력 관리

- 사이드바에서 질병/수술명, 시기, 메모 등록
- AI 채팅 시 등록된 병력이 시스템 프롬프트에 자동 포함
- 항목별 개별 삭제 가능

### 5. ⏰ 복약 알림 (WIP)

- UI: 약 이름, 아침/점심/저녁 복용 시간, 메모 입력 폼 구현
- 백엔드 알림 발송 미구현 (세션 내 목록 표시만 동작)

### 6. 🗑️ 전체 초기화

- 병력, 건강일기, 모든 채팅 기록 일괄 삭제
- 2단계 확인(confirm) 방식으로 실수 방지

---

## 기술 스택

| 영역 | 기술 |
|---|---|
| Frontend | Streamlit |
| LLM | LangChain + GPT-4o-mini |
| Vision | OpenAI Vision API (GPT-4o) |
| Storage | Local JSON 파일 |
| Env | python-dotenv |

---

## 프로젝트 구조

```
Langchin_chatBot/
├── app.py                    # Streamlit 앱 진입점, UI 메인
├── chatbot.py                # MomChatbot 클래스, 진료과 매핑, LangChain 체인
├── prompts.py                # 시스템 프롬프트 생성
├── data_manager.py           # JSON 파일 CRUD (병력, 건강일기, 채팅)
├── vision.py                 # OpenAI Vision API 이미지 분석
├── components/
│   ├── sidebar.py            # 병력 관리 + 복약 알림 + 전체 초기화 사이드바
│   ├── alarm_ui.py           # 복약 알림 UI (WIP)
│   └── calendar_view.py      # 건강일기 캘린더 다이얼로그
├── data/                     # 로컬 데이터 저장소 (자동 생성)
│   ├── medical_history.json
│   ├── health_diary.json
│   └── chat_YYYY-MM-DD.json
└── .env                      # OPENAI_API_KEY
```

---

## 설치 및 실행

```bash
git clone <repo-url>
cd Langchin_chatBot
pip install -r requirements.txt
```

`.env` 파일 생성:

```
OPENAI_API_KEY=sk-...
```

앱 실행:

```bash
streamlit run app.py
```

---

## 데이터 구조

### `medical_history.json`

```json
[
  {
    "disease": "고혈압",
    "date": "2022-03",
    "memo": "현재 약 복용 중",
    "created_at": "2024-01-15 10:30:00"
  }
]
```

### `health_diary.json`

```json
{
  "2024-03-15": {
    "condition": "😊 좋음",
    "symptoms": ["🤕 두통"],
    "bowel": "✅ 건강함",
    "sleep_hours": 7.0,
    "exercise": ["🚶 걷기"],
    "hospital": ["❌ 방문 안 함"],
    "memo": "오늘은 좀 나은 것 같다",
    "updated_at": "2024-03-15 20:00:00"
  }
}
```

### `chat_YYYY-MM-DD.json`

```json
[
  {"role": "assistant", "content": "어디 불편한 데 있어?"},
  {"role": "user", "content": "머리가 너무 아파"}
]
```

---

## 화면 구성

| 영역 | 설명 |
|---|---|
| 메인 채팅 | 모바일 390px 중앙 정렬 채팅 UI |
| 플로팅 버튼 | 📅 캘린더 다이얼로그, 📷 사진 업로드 |
| 사이드바 | 🏥 병력 관리 / ⏰ 복약 알림 / 🗑️ 전체 초기화 |

---

## 제약사항 / 향후 계획

- **복약 알림 백엔드 미구현**: UI만 존재, 실제 알림 발송 없음
- **단일 사용자**: 로그인/인증 없음, 데이터는 로컬 저장
- **OpenAI API 키 필요**: 사용량에 따라 비용 발생
- **향후 계획**: 복약 알림 푸시 구현, 다중 사용자 지원, 모바일 앱 전환

---

## 라이선스

[MIT License](LICENSE)
