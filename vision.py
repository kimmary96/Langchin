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
                        "이 사진을 보고 내용을 분석해줘. "
                        "약봉투면 약 이름, 효능, 복용법, 주의사항을 알려줘. "
                        "피부나 신체 이상이면 보이는 증상을 묘사해줘(진단 아님). "
                        "멍이나 상처, 화상이면 상태와 주의사항을 알려줘. "
                        "그 외 신체 부위는 보이는 것을 묘사해줘.\n\n"
                        "반드시 엄마 말투로 대화하듯 자연스럽게 풀어서 답변해줘. "
                        "번호 매기기(1. 2. 3.)나 불릿 포인트(-, •) 없이 문장으로만 써줘. "
                        "예) '어머, 이거 멍이 꽤 크게 들었네. 많이 아프겠다.'\n"
                        "의학적 진단은 하지 말고, 심각해 보이면 병원 권유해줘. "
                        "이미지에서 텍스트가 있으면 정확하게 읽어서 그대로 전달해줘. "
                        "절대 약 이름이나 내용을 추측하거나 지어내지 마."
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
