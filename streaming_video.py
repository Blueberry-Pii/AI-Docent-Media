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

    speech_text = clean_text
    if tag == "KO":
        # 한국어는 하이픈(-)을 '다시'로 읽음
        speech_text = speech_text.replace("-", " 다시 ")
    else:
        # 영어(EN)와 스페인어(ES)는 하이픈(-)을 공백으로 치환하여 자연스럽게 넘김
        speech_text = speech_text.replace("-", " ")
    
    # 특수 기호 제거: 괄호 등을 읽지 않도록 클리닝
    speech_text = re.sub(r'[\(\)\[\]]', '', speech_text)
    
    # 기존 payload를 이렇게 변경해 보세요
    payload = {
        "script": {
            "type": "text",
            "input": speech_text,
            "provider": {
                "type": "microsoft",
                "voice_id": voice_id
            }
        },
        "config": {
            "fluent": True,
            "driver_name": "built-in", 
            "normalization": False  # TTS 자동 교정 기능 끄기
        },
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
