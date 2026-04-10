"""
Speech to Text - Convert recorded audio to transcript
Uses OpenAI Whisper (free, local, no API key needed)
"""

import whisper
import os

class SpeechToText:
    def __init__(self):
        self.model = None
    
    def load_model(self):
        """Load Whisper model (first time takes a moment)"""
        if self.model is None:
            print("Loading speech recognition model...")
            self.model = whisper.load_model("base")
        return self.model
    
    def transcribe(self, audio_file):
        """Convert audio file to text"""
        model = self.load_model()
        result = model.transcribe(audio_file)
        return result["text"]
    
    def transcribe_with_timestamps(self, audio_file):
        """Get transcript with timestamps"""
        model = self.load_model()
        result = model.transcribe(audio_file, word_timestamps=True)
        return result