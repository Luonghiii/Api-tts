from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import subprocess
import urllib.request
import hashlib

app = FastAPI()

# Mở CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Thư mục tạm trên Vercel (chỉ có /tmp là ghi được)
TMP_DIR = "/tmp"
MODEL_ONNX = os.path.join(TMP_DIR, "vi_VN-hoai_cao-medium.onnx")
MODEL_JSON = os.path.join(TMP_DIR, "vi_VN-hoai_cao-medium.onnx.json")

MODEL_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/vi/vi_VN/hoai_cao/medium/vi_VN-hoai_cao-medium.onnx"
CONFIG_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/vi/vi_VN/hoai_cao/medium/vi_VN-hoai_cao-medium.onnx.json"

def download_model():
    if not os.path.exists(MODEL_ONNX):
        urllib.request.urlretrieve(MODEL_URL, MODEL_ONNX)
        urllib.request.urlretrieve(CONFIG_URL, MODEL_JSON)

@app.get("/")
def read_root():
    return {"message": "Piper TTS API on Vercel is running!"}

@app.get("/tts")
async def text_to_speech(text: str):
    if not text:
        return JSONResponse({"error": "No text provided"}, status_code=400)
    
    # Đảm bảo model đã có trong /tmp
    download_model()
    
    file_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
    output_file = os.path.join(TMP_DIR, f"{file_hash}.wav")
    
    try:
        # Lưu ý: Vercel không cài sẵn piper. 
        # Bạn có thể cần dùng piper-tts (python package) thay vì subprocess binary
        # Ở đây mình giả định dùng package piper-tts đã cài qua pip
        import sys
        
        # Lệnh chạy piper thông qua module python
        cmd = [
            sys.executable, "-m", "piper",
            "--model", MODEL_ONNX,
            "--output_file", output_file
        ]
        
        process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process.communicate(input=text.encode('utf-8'))
        
        if os.path.exists(output_file):
            return FileResponse(output_file, media_type="audio/wav")
        else:
            return JSONResponse({"error": "Failed to generate audio"}, status_code=500)
            
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

# Vercel cần export app
