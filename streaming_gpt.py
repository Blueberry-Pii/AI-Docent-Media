from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(override=True)
import os

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_ari_answer(user_input):
    """
    프론트에서 온 STT 텍스트를 받아 GPT 답변을 생성합니다.
    """
    ari_prompt = """
    너는 MWC 2026 한국관 AI 도슨트 '아리'야.
    사용자의 언어에 맞춰 한국어, 영어, 스페인어로 답변해줘.
    답변 시작할 때 반드시 아래 대괄호에 해당 목소리 ID를 붙여서 대답해.
    
    - 한국어 질문: [ko-KR-SunHiNeural] 답변내용
    - 영어 질문: [en-US-JennyNeural] 답변내용
    - 스페인어 질문: [es-ES-ElviraNeural] 답변내용
    
    규칙: 전시장 소음이 심하니 한 번에 '두 문장' 이내로 핵심만 말해줘.
    """
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": ari_prompt},
            {"role": "user", "content": user_input}
        ]
    )
    
    return response.choices[0].message.content