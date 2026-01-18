import re
import os
import requests
from dotenv import load_dotenv

load_dotenv(override=True)
DID_API_KEY=os.getenv("DID_API_KEY")

def request_video_stream(stream_id, session_id, full_text):
    # 1. 텍스트에서 [목소리ID] 추출 (예: [ko-KR-SunHiNeural] 안녕하세요 -> ko-KR-SunHiNeural 추출)
    voice_match = re.search(r"\[(.*?)\]", full_text)
    
    if voice_match:
        voice_id = voice_match.group(1) # 대괄호 안의 ID 추출
        answer_text = full_text.replace(f"[{voice_id}]", "").strip() # ID 제거한 실제 답변만 추출
    else:
        # 기본값 설정 (추출 실패 시)
        voice_id = "ko-KR-SunHiNeural"
        answer_text = full_text

    url = f"https://api.d-id.com/talks/streams/{stream_id}"
    headers = {
        "Authorization": f"Basic {DID_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "script": {
            "type": "text",
            "input": answer_text,
            "provider": {
                "type": "microsoft", 
                "voice_id": voice_id 
            }
        },
        "config": {"fluent": True},
        "session_id": session_id 
    }
    
    response = requests.post(url, json=payload, headers=headers)
    print(f"사용된 목소리: {voice_id}")
    return response.json()