"""
Clean Live Meeting Recorder - NO FAKE DATA
Records real microphone input and saves as document
"""

import sounddevice as sd
import numpy as np
import threading
import queue
import wave
import os
from datetime import datetime
import json

class RealMeetingRecorder:
    def __init__(self):
        self.is_recording = False
        self.audio_frames = []
        self.sample_rate = 16000
        self.channels = 1
        self.transcript = []
        
    def start_recording(self):
        """Start real recording from microphone"""
        self.is_recording = True
        self.audio_frames = []
        self.transcript = []
        
        # Start recording thread
        self.recording_thread = threading.Thread(target=self._record)
        self.recording_thread.start()
        
        return True
    
    def _record(self):
        """Record audio in real-time"""
        def callback(indata, frames, time, status):
            if self.is_recording:
                self.audio_frames.append(indata.copy())
        
        with sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            callback=callback
        ):
            while self.is_recording:
                sd.sleep(100)
    
    def stop_recording(self):
        """Stop recording and save"""
        self.is_recording = False
        
        if hasattr(self, 'recording_thread'):
            self.recording_thread.join(timeout=2)
        
        # Save audio file
        if self.audio_frames:
            audio_data = np.concatenate(self.audio_frames, axis=0)
            filename = f"meeting_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
            
            # Save as WAV
            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(2)
                wf.setframerate(self.sample_rate)
                wf.writeframes((audio_data * 32767).astype(np.int16).tobytes())
            
            return filename
        
        return None
    
    def add_transcript_line(self, text):
        """Add transcribed text to meeting record"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.transcript.append(f"[{timestamp}] {text}")
    
    def save_transcript(self, filename):
        """Save transcript as document"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"Meeting Transcript\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*50 + "\n\n")
            for line in self.transcript:
                f.write(line + "\n")
        return filename