import base64
from openai import OpenAI


def analyze_medicine_image(image_bytes):
    try:
        client = OpenAI()
        base64_image = base64.b64encode(image_bytes).decode("utf-8")

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "이 사진을 보고 아래 중 해당하는 내용을 분석해줘.\n"
                        "- 약봉투: 약 이름, 효능, 복용법, 주의사항\n"
                        "- 피부/신체 이상: 보이는 증상 묘사 (진단 아님)\n"
                        "- 멍/상처/화상: 상태 묘사 및 주의사항\n"
                        "- 기타 신체 부위: 보이는 것 묘사\n\n"
                        "반드시 엄마 말투로 답변해줘.\n"
                        "예) '어머, 이거 멍이 꽤 크게 들었네. 많이 아프겠다.'\n"
                        "의학적 진단은 하지 말고, 심각해 보이면 병원 권유해줘.\n"
                        "이미지에서 텍스트가 있으면 정확하게 읽어서 그대로 전달해줘.\n"
                        "절대 약 이름이나 내용을 추측하거나 지어내지 마.\n"
                    ),
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "이 사진을 분석해줘.",
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                            },
                        },
                    ],
                },
            ],
            max_tokens=1000,
        )
        return response.choices[0].message.content
    except Exception:
        return "사진을 분석하는데 문제가 생겼네. 사진이 잘 찍혔는지 확인하고 다시 올려줄래?"
