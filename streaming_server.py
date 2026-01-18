from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import os
import requests
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# 1. 환경 변수 로드
load_dotenv(override=True)
DID_API_KEY = os.getenv("DID_API_KEY")

app = FastAPI()

# 2. CORS 설정 (프론트엔드 localhost 접속 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 기존 모듈 임포트
from streaming_gpt import generate_ari_answer
from streaming_video import request_video_stream 

# 데이터 모델 정의
class ChatRequest(BaseModel):
    text: str        # 프론트가 보낸 STT 텍스트
    stream_id: str   # D-ID WebRTC 스트림 ID
    session_id: str  # D-ID 세션 ID

# --- 추가/수정된 부분 시작 ---

# 1. 세션 시작 엔드포인트 (이미지 주소 포함)
@app.post("/start-session")
async def start_session():
    url = "https://api.d-id.com/talks/streams"
    headers = {
        "Authorization": f"Basic {DID_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        # 깃허브 Public 레포지토리의 직접 이미지 링크
        "source_url": "https://github.com/user-attachments/assets/68cd270e-75b0-4b0a-881a-78e4f423cefe" 
    }
    
    response = requests.post(url, json=payload, headers=headers)

    res_data = response.json()
    print("=== D-ID API RESPONSE START ===")
    print(res_data) 
    print("=== D-ID API RESPONSE END ===")

    return response.json()

# 2. ICE Candidate 중계 엔드포인트 (최종 보완)
@app.post("/submit-ice")
async def submit_ice(data: dict):
    stream_id = data.get("stream_id")
    url = f"https://api.d-id.com/talks/streams/{stream_id}/ice"
    headers = {
        "Authorization": f"Basic {DID_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        # [핵심] sdpMid에 "0"을 기본값으로 주지 마세요. 
        # 프론트에서 넘어온 "v"나 "a" 같은 값을 그대로 유지해야 합니다.
        sdp_mid = data.get("sdpMid")
        sdp_mline_index = data.get("sdpMLineIndex")

        payload = {
            "candidate": str(data.get("candidate")),
            "sdpMid": str(sdp_mid) if sdp_mid is not None else "v", # 값이 없으면 비디오(v)를 기본으로
            "sdpMLineIndex": int(sdp_mline_index) if sdp_mline_index is not None else 0,
            "session_id": data.get("session_id")
        }
        
        print(f"--- [DEBUG] D-ID로 쏘는 실제 데이터: {payload} ---")
        
        response = requests.post(url, json=payload, headers=headers)
        return response.json()
        
    except Exception as e:
        print(f"ICE 처리 에러: {e}")
        return {"error": str(e)}

# 3. SDP Answer 중계 엔드포인트 (새로 추가)
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

# --- 추가/수정된 부분 끝 ---

@app.post("/ask-ari")
async def ask_ari(req: ChatRequest):
    print(f"프론트 수신: {req.text}")
    
    # 1. GPT로 답변 생성
    answer = generate_ari_answer(req.text)
    print(f"아리 답변: {answer}")
    
    # 2. D-ID에 영상 스트리밍 명령
    request_video_stream(req.stream_id, req.session_id, answer)
    
    return {
        "status": "success", 
        "answer": answer
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)