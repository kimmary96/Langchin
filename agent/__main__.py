import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from agent.runner import run_agent

TEST_USER_MESSAGE = "오늘 아침부터 배가 너무 아파. 설사도 하고 기운이 없어"
TEST_MEDICAL_HISTORY = "진단: 과민성대장증후군, 위염 / 복용약: 없음 / 알레르기: 없음"
TEST_TODAY_DIARY = "컨디션: 나쁨, 수면: 6시간"


def main():
    print("=" * 60)
    print("  LangGraph 에이전트 테스트")
    print("=" * 60)
    print(f"[입력] 사용자 메시지 : {TEST_USER_MESSAGE}")
    print(f"[입력] 병력          : {TEST_MEDICAL_HISTORY}")
    print(f"[입력] 오늘 일기     : {TEST_TODAY_DIARY}")
    print("=" * 60)

    result = run_agent(
        user_message=TEST_USER_MESSAGE,
        medical_history=TEST_MEDICAL_HISTORY,
        today_diary=TEST_TODAY_DIARY,
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

    retry_count = sum(
        1 for step in result["agent_steps"]
        if step.startswith("재시도")
    )
    print()
    print(f"▶ 총 재시도 횟수: {retry_count}회")
    print("=" * 60)


if __name__ == "__main__":
    main()
