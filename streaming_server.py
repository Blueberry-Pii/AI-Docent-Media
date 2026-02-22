import os
import re
import json
import requests
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# 기존 모듈 임포트
from streaming_gpt import generate_ari_answer
from streaming_video import request_video_stream 

# 1. 환경 변수 및 설정 로드
load_dotenv(override=True)
DID_API_KEY = os.getenv("DID_API_KEY")

app = FastAPI()

# 2. CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. 데이터 모델 정의
class ChatRequest(BaseModel):
    text: str        # 프론트에서 전달된 STT 텍스트
    stream_id: str   # D-ID WebRTC 스트림 ID
    session_id: str  # D-ID 세션 ID

# --- 헬스체크 및 루트 엔드포인트 ---

@app.get("/")
async def root():
    """UptimeRobot 및 서버 상태 확인용 루트 페이지"""
    return {
        "status": "online",
        "message": "ARI AI Docent Server is running!",
        "version": "1.0.0"
    }

# --- D-ID 스트리밍 관련 엔드포인트 ---

@app.post("/start-session")
async def start_session():
    url = "https://api.d-id.com/talks/streams"
    headers = {
        "Authorization": f"Basic {DID_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "source_url": "https://github.com/user-attachments/assets/68cd270e-75b0-4b0a-881a-78e4f423cefe",
        "config": {"stitch": True},
        "face": {"top_left": [700, 72], "size": 1632}
    }
    
    response = requests.post(url, json=payload, headers=headers)
    res_data = response.json()
    
    print("=== D-ID API RESPONSE START ===")
    print(json.dumps(res_data, indent=4)) 
    print("=== D-ID API RESPONSE END ===")

    return res_data

@app.post("/submit-ice")
async def submit_ice(data: dict):
    stream_id = data.get("stream_id")
    url = f"https://api.d-id.com/talks/streams/{stream_id}/ice"
    headers = {
        "Authorization": f"Basic {DID_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        sdp_mid = data.get("sdpMid")
        sdp_mline_index = data.get("sdpMLineIndex")

        payload = {
            "candidate": str(data.get("candidate")),
            "sdpMid": str(sdp_mid) if sdp_mid is not None else "v",
            "sdpMLineIndex": int(sdp_mline_index) if sdp_mline_index is not None else 0,
            "session_id": data.get("session_id")
        }
        
        print(f"--- [DEBUG] ICE Payload: {payload} ---")
        response = requests.post(url, json=payload, headers=headers)
        return response.json()
        
    except Exception as e:
        print(f"ICE 처리 에러: {e}")
        return {"error": str(e)}

@app.post("/submit-sdp")
async def submit_sdp(data: dict):
    stream_id = data.get("stream_id")
    url = f"https://api.d-id.com/talks/streams/{stream_id}/sdp"
    headers = {
        "Authorization": f"Basic {DID_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "answer": data.get("answer"),
        "session_id": data.get("session_id")
    }
    response = requests.post(url, json=payload, headers=headers)
    return response.json()

# --- 메인 채팅 엔드포인트 ---

@app.post("/ask-ari")
async def ask_ari(req: ChatRequest):
    print(f"프론트 수신: {req.text}")
    
    # 1. GPT 답변 생성 (태그 포함된 원본)
    raw_answer = generate_ari_answer(req.text)
    
    # 2. D-ID 스트리밍 명령 (내부에서 voice_id 매핑 및 텍스트 정제 수행)
    video_res = request_video_stream(req.stream_id, req.session_id, raw_answer)
    
    # 3. 프론트엔드 표시용 텍스트 정제 ([KO] 등 태그 제거)
    clean_display_text = re.sub(r"\[(KO|EN|ES)\]", "", raw_answer).strip()
    
    print(f"최종 정제 답변: {clean_display_text}")

    return {
        "status": "success", 
        "answer": clean_display_text,
        "video_status": video_res.get("status")
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
