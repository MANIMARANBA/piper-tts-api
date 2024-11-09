from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import subprocess
import os
from datetime import datetime
from pydantic import BaseModel
import logging
import shutil

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI(title="Piper TTS API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

class TextToSpeechRequest(BaseModel):
    text: str
    speaker_id: int = 0

@app.post("/tts")
async def text_to_speech(request: TextToSpeechRequest):
    try:
        # Verify piper exists
        piper_path = "/app/piper/bin/piper"
        if not os.path.exists(piper_path):
            raise HTTPException(status_code=500, detail=f"Piper binary not found at {piper_path}")

        # Verify model exists
        model_path = "/app/models/en_US-kathleen-low.onnx"
        if not os.path.exists(model_path):
            raise HTTPException(status_code=500, detail=f"Model file not found at {model_path}")

        # Create output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"/app/output/speech_{timestamp}.wav"
        
        logger.debug(f"Creating speech file: {output_file}")
        
        # Prepare command
        cmd = [
            piper_path,
            "--model", model_path,
            "--output_file", output_file
        ]
        
        logger.debug(f"Running command: {' '.join(cmd)}")
        
        # Run piper
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Send text to piper
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
        # Check piper binary
        piper_path = "/app/piper/bin/piper"
        if not os.path.exists(piper_path):
            return JSONResponse(
                status_code=503,
                content={"status": "unhealthy", "error": f"Piper binary not found at {piper_path}"}
            )

        # Check model file
        model_path = "/app/models/en_US-kathleen-low.onnx"
        if not os.path.exists(model_path):
            return JSONResponse(
                status_code=503,
                content={"status": "unhealthy", "error": f"Model file not found at {model_path}"}
            )

        # Check piper functionality
        cmd = [piper_path, "--help"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return JSONResponse(
                status_code=503,
                content={"status": "unhealthy", "error": result.stderr}
            )

        # Check output directory
        output_dir = "/app/output"
        if not os.path.exists(output_dir):
            return JSONResponse(
                status_code=503,
                content={"status": "unhealthy", "error": f"Output directory not found at {output_dir}"}
            )

        # All checks passed
        return JSONResponse(
            status_code=200,
            content={
                "status": "healthy",
                "piper_version": result.stdout.split('\n')[0],
                "disk_space": shutil.disk_usage(output_dir).free // (1024 * 1024)  # Free space in MB
            }
        )
    except Exception as e:
        logger.exception("Health check failed")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )

@app.get("/")
async def root():
    return {"message": "Piper TTS API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)