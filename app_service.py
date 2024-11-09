from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import subprocess
import os
from datetime import datetime
from pydantic import BaseModel

app = FastAPI(title="Piper TTS API")

class TextToSpeechRequest(BaseModel):
    text: str
    speaker_id: int = 0

@app.post("/tts")
async def text_to_speech(request: TextToSpeechRequest):
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"/app/output/speech_{timestamp}.wav"
        
        cmd = [
            "/app/piper/bin/piper",
            "--model", "/app/models/en_US-kathleen-low.onnx",
            "--output_file", output_file,
            "--speaker", str(request.speaker_id)
        ]
        
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = process.communicate(input=request.text)
        
        if process.returncode != 0:
            raise HTTPException(status_code=500, detail=f"TTS Error: {stderr}")
            
        return FileResponse(
            output_file,
            media_type="audio/wav",
            filename=f"speech_{timestamp}.wav"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}