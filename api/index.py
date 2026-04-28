```python
from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import subprocess
import urllib.request
import hashlib

app = FastAPI()

# Cấu hình CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Thư mục tạm trên Vercel
TMP_DIR = "/tmp"
MODEL_ONNX = os.path.join(TMP_DIR, "vi_VN-hoai_cao-medium.onnx")
MODEL_JSON = os.path.join(TMP_DIR, "vi_VN-hoai_cao-medium.onnx.json")

# URL CHUẨN (Đã kiểm tra lại trên Hugging Face)
MODEL_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/vi/vi_VN/hoai_cao/medium/vi_VN-hoai_cao-medium.onnx"
CONFIG_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/vi/vi_VN/hoai_cao/medium/vi_VN-hoai_cao-medium.onnx.json"

def download_model():
    """Tải model vào /tmp nếu chưa tồn tại"""
    if not os.path.exists(MODEL_ONNX):
        try:
            print("Downloading model...")
            urllib.request.urlretrieve(MODEL_URL, MODEL_ONNX)
            urllib.request.urlretrieve(CONFIG_URL, MODEL_JSON)
            print("Download complete.")
        except Exception as e:
            print(f"Download failed: {e}")
            raise e

@app.get("/")
def home():
    return {"status": "online", "model": "vi_VN-hoai_cao-medium"}

@app.get("/tts")
async def text_to_speech(text: str = Query(..., min_length=1)):
    try:
        # 1. Đảm bảo model đã sẵn sàng
        download_model()
        
        # 2. Tạo tên file duy nhất dựa trên nội dung text
        file_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        output_file = os.path.join(TMP_DIR, f"{file_hash}.wav")
        
        # 3. Nếu đã có trong cache /tmp thì trả về luôn
        if os.path.exists(output_file):
            return FileResponse(output_file, media_type="audio/wav")

        # 4. Chạy Piper qua lệnh hệ thống (Sử dụng module python)
        # Lưu ý: Vercel có thể thiếu một số thư viện libonnxruntime, 
        # chúng ta dùng module piper để nó tự xử lý.
        import sys
        command = [
            sys.executable, "-m", "piper",
            "--model", MODEL_ONNX,
            "--output_file", output_file
        ]
        
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate(input=text.encode('utf-8'), timeout=15)

        if process.returncode != 0:
            return JSONResponse({"error": "Piper error", "details": stderr.decode()}, status_code=500)

        if os.path.exists(output_file):
            return FileResponse(output_file, media_type="audio/wav")
        
        return JSONResponse({"error": "File not generated"}, status_code=500)

    except subprocess.TimeoutExpired:
        return JSONResponse({"error": "Processing timeout"}, status_code=504)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

```
