# src/tools/voice_tools.py

import speech_recognition as sr
from gtts import gTTS
import tempfile
import os

# Optional: Only import if CrewAI is available
try:
    from crewai import Tool
except ImportError:
    Tool = None  # fallback for Streamlit-only use

# -------------------------------
# Base Function: Voice Input
# -------------------------------
def get_voice_input_from_file(file_path):
    recognizer = sr.Recognizer()
    with sr.AudioFile(file_path) as source:
        audio_data = recognizer.record(source)
        try:
            return recognizer.recognize_google(audio_data, language="hi-IN")
        except sr.UnknownValueError:
            return "Could not understand the audio."
        except sr.RequestError:
            return "API error. Try again later."

# -------------------------------
# Base Function: Voice Output
# -------------------------------
def generate_speech_mp3(text, lang="hi"):
    tts = gTTS(text=text, lang=lang)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        tts.save(fp.name)
        return fp.name  # path to use in st.audio()
    
# -------------------------------
# Optional CrewAI Tool Wrappers
# -------------------------------
if Tool is not None:
    speech_to_text_tool = Tool(
        name="speech_to_text",
        description="Transcribe user voice (Hindi/English) from a .wav file",
        func=get_voice_input_from_file
    )

    text_to_speech_tool = Tool(
        name="text_to_speech",
        description="Convert agent's response text to speech using gTTS",
        func=generate_speech_mp3
    )
