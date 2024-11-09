import streamlit as st
import requests
import os
from pathlib import Path
import time
import json
from datetime import datetime

# Set page config
st.set_page_config(
    page_title="Piper TTS Tester",
    page_icon="🔊",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    </style>
""", unsafe_allow_html=True)

def check_service_health():
    try:
        health_check = requests.get("http://localhost:8000/health")
        if health_check.status_code == 200:
            health_data = health_check.json()
            return True, health_data
        return False, health_check.json()
    except Exception as e:
        return False, str(e)

def convert_text_to_speech(text):
    try:
        response = requests.post(
            "http://localhost:8000/tts",
            json={"text": text, "speaker_id": 0},
            timeout=30
        )
        
        if response.status_code == 200:
            # Save the audio content
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"output/speech_{timestamp}.wav"
            
            # Ensure output directory exists
            os.makedirs("output", exist_ok=True)
            
            # Save the audio file
            with open(output_path, "wb") as f:
                f.write(response.content)
            
            return True, output_path
        else:
            return False, f"Error: {response.status_code} - {response.text}"
    except Exception as e:
        return False, f"Failed to convert text: {str(e)}"

# Main UI
st.title("🔊 Piper Text-to-Speech Tester")

# Sidebar
with st.sidebar:
    st.header("System Status")
    is_healthy, health_info = check_service_health()
    
    if is_healthy:
        st.success("TTS Service: Online")
        if isinstance(health_info, dict):
            st.info(f"Piper Version: {health_info.get('piper_version', 'Unknown')}")
            st.info(f"Free Disk Space: {health_info.get('disk_space', 0)} MB")
    else:
        st.error(f"TTS Service: Offline\n{health_info}")
    
    st.header("Generated Files")
    output_dir = Path("output")
    if output_dir.exists():
        files = sorted(output_dir.glob("*.wav"), key=os.path.getmtime, reverse=True)
        if files:
            for file in files[:10]:  # Show only the 10 most recent files
                created_time = datetime.fromtimestamp(os.path.getmtime(file)).strftime("%Y-%m-%d %H:%M:%S")
                st.text(f"{file.name}\n└─ {created_time}")
                
                # Add play button for each file
                with open(file, "rb") as audio_file:
                    st.audio(audio_file.read(), format="audio/wav")
        else:
            st.text("No audio files generated yet")
    else:
        st.warning("Output directory not found")

# Main content
col1, col2 = st.columns([2, 1])

with col1:
    text_input = st.text_area(
        "Enter text to convert to speech:",
        "Hello, this is a test of text to speech.",
        height=150
    )

    if st.button("🎵 Convert to Speech", disabled=not is_healthy):
        if text_input.strip():
            with st.spinner("Converting text to speech..."):
                success, result = convert_text_to_speech(text_input)
                
                if success:
                    st.success("Audio generated successfully!")
                    
                    # Create audio player
                    with open(result, "rb") as file:
                        audio_bytes = file.read()
                        st.audio(audio_bytes, format="audio/wav")
                    
                    # Add download button
                    st.download_button(
                        label="⬇️ Download Audio",
                        data=audio_bytes,
                        file_name=os.path.basename(result),
                        mime="audio/wav"
                    )
                else:
                    st.error(result)
        else:
            st.warning("Please enter some text first!")

with col2:
    with st.expander("ℹ️ How to use", expanded=True):
        st.markdown("""
        1. Make sure the TTS service is online (check sidebar)
        2. Enter your text in the input area
        3. Click the 'Convert to Speech' button
        4. Wait for the conversion to complete
        5. Play the audio using the player
        6. Download the audio file if desired
        
        **Tips:**
        - Keep text length reasonable for better performance
        - Check system status in sidebar for service health
        - Recent generated files are shown in sidebar
        - Audio files are saved in the 'output' directory
        """)

    with st.expander("🛠️ Advanced Settings", expanded=False):
        st.markdown("""
        **Service Information:**
        - Endpoint: `http://localhost:8000`
        - Model: en_US-kathleen-low
        - Format: WAV audio
        """)

# Footer
st.markdown("---")
st.markdown(
    "Made with ❤️ using Streamlit and Piper TTS | "
    "[GitHub](https://github.com/rhasspy/piper) | "
    "[Documentation](https://github.com/rhasspy/piper/tree/master/docs)"
)