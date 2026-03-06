import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from agent.runner import run_agent

TESTS = [
    {
        "label": "테스트 1 - 약 이름 정보 질문 (Tavily 검색 + 정보 중심 답변)",
        "user_message": "내가 듀파스톤이라는 약을 먹고있는데 뭔지 알아?",
        "medical_history": "진단: 생리불순",
        "today_diary": "",
    },
    {
        "label": "테스트 2 - 감정 공유 (반말 유지, 검색 없음)",
        "user_message": "그냥 좀 멍해",
        "medical_history": "",
        "today_diary": "",
    },
]


def run_test(test: dict):
    print("=" * 60)
    print(f"  {test['label']}")
    print("=" * 60)
    print(f"[입력] 사용자 메시지 : {test['user_message']}")
    print(f"[입력] 병력          : {test['medical_history'] or '없음'}")
    print(f"[입력] 오늘 일기     : {test['today_diary'] or '없음'}")
    print("=" * 60)

    result = run_agent(
        user_message=test["user_message"],
        medical_history=test["medical_history"],
        today_diary=test["today_diary"],
    )

    print()
    print("─" * 60)
    print("▶ 최종 응답")
    print("─" * 60)
    print(result["response"])

    print()
    print("─" * 60)
    print("▶ 처리 단계 (agent_steps)")
    print("─" * 60)
    for i, step in enumerate(result["agent_steps"], start=1):
        print(f"  {i}. {step}")

    has_search = any("Tavily 검색 실행됨" in s for s in result["agent_steps"])
    has_banmal_violation = any(
        suffix in result["response"]
        for suffix in ["죠", "요.", "습니다", "군요", "네요"]
    )
    print()
    print(f"▶ Tavily 검색 포함: {'✅ 예' if has_search else '❌ 아니오'}")
    print(f"▶ 존댓말 위반 감지: {'⚠️ 위반 있음' if has_banmal_violation else '✅ 반말 유지'}")
    print("=" * 60)


def main():
    for test in TESTS:
        run_test(test)
        print()


if __name__ == "__main__":
    main()
