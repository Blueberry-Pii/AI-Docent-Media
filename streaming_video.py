import re
import os
import requests
from dotenv import load_dotenv

load_dotenv(override=True)
DID_API_KEY = os.getenv("DID_API_KEY")

def request_video_stream(stream_id, session_id, full_text):
    """
    GPT의 응답(태그 포함)을 받아 Voice ID를 매핑하고, 
    태그가 제거된 텍스트로 D-ID 스트리밍을 요청합니다.
    """
    
    # 1. 짧은 태그를 실제 D-ID Voice ID로 변환하는 매핑 테이블
    voice_map = {
        "KO": "ko-KR-SunHiNeural",
        "EN": "en-US-JennyNeural",
        "ES": "es-ES-ElviraNeural"
    }

    # 2. 정규표현식으로 [KO], [EN], [ES] 태그 추출
    match = re.match(r"\[(KO|EN|ES)\]\s*(.*)", full_text.strip(), re.IGNORECASE)
    
    if match:
        tag = match.group(1).upper()      # "KO", "EN", "ES" 중 하나
        clean_text = match.group(2).strip() # 태그가 제외된 순수 답변 텍스트
        voice_id = voice_map.get(tag, "ko-KR-SunHiNeural") # 매핑된 ID 가져오기
    else:
        # 태그가 없거나 형식이 다를 경우 기본값(한국어) 적용
        voice_id = "ko-KR-SunHiNeural"
        clean_text = full_text.strip()

    # 3. D-ID API 요청 설정
    url = f"https://api.d-id.com/talks/streams/{stream_id}"
    headers = {
        "Authorization": f"Basic {DID_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "script": {
            "type": "text",
            "input": clean_text, # 화면에 출력되고 읽어줄 태그 없는 텍스트
            "provider": {
                "type": "microsoft", 
                "voice_id": voice_id # 짧은 태그 대신 풀 보이스 ID 전달
            }
        },
        "config": {"fluent": True},
        "session_id": session_id 
    }
    
    # 4. API 전송
    response = requests.post(url, json=payload, headers=headers)
    
    print(f"--- 스트리밍 요청 정보 ---")
    print(f"입력 태그: {tag if match else 'None'}")
    print(f"최종 Voice ID: {voice_id}")
    print(f"최종 출력 텍스트: {clean_text}")
    print(f"응답 상태: {response.status_code}")
    
    return response.json()
