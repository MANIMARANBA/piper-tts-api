from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import subprocess
import os
from datetime import datetime
from pydantic import BaseModel
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI(title="Piper TTS API")

class TextToSpeechRequest(BaseModel):
    text: str
    speaker_id: int = 0

@app.post("/tts")
async def text_to_speech(request: TextToSpeechRequest):
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"/app/output/speech_{timestamp}.wav"
        
        logger.debug(f"Creating speech file: {output_file}")
        
        cmd = [
            "/app/piper/bin/piper",
            "--model", "/app/models/en_US-kathleen-low.onnx",
            "--output_file", output_file
        ]
        
        logger.debug(f"Running command: {' '.join(cmd)}")
        
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = process.communicate(input=request.text)
        
        logger.debug(f"Process output - stdout: {stdout}, stderr: {stderr}")
        
        if process.returncode != 0:
            error_msg = f"TTS Error: {stderr}"
            logger.error(error_msg)
            raise HTTPException(status_code=500, detail=error_msg)
        
        if not os.path.exists(output_file):
            error_msg = f"Output file not created: {output_file}"
            logger.error(error_msg)
            raise HTTPException(status_code=500, detail=error_msg)
            
        logger.debug(f"Returning file: {output_file}")
        return FileResponse(
            output_file,
            media_type="audio/wav",
            filename=f"speech_{timestamp}.wav"
        )
        
    except Exception as e:
        logger.exception("Error in text_to_speech")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    try:
        # Test if piper is accessible
        cmd = ["/app/piper/bin/piper", "--help"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return {"status": "unhealthy", "error": result.stderr}
        return {"status": "healthy"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}