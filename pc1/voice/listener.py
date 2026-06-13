"""
Module 6a — Speech-to-text listener.
"""

import speech_recognition as sr
from pc1.emotion.emotion_mapper import parse_voice
from config import SPEECH_LANG, LISTEN_TIMEOUT, COMMAND_TIMEOUT

USE_WHISPER = False


class VoiceListener:
    def __init__(self):
        self._rec = sr.Recognizer()
        self._mic = sr.Microphone()
        if USE_WHISPER:
            import whisper
            self._whisper = whisper.load_model("base")
        with self._mic as source:
            self._rec.adjust_for_ambient_noise(source, duration=1.5)

    def _transcribe(self, audio: sr.AudioData) -> str | None:
        try:
            if USE_WHISPER:
                import io, soundfile
                wav_bytes = audio.get_wav_data()
                audio_array, _ = soundfile.read(io.BytesIO(wav_bytes))
                result = self._whisper.transcribe(audio_array, language="ko")
                return result["text"].lower().strip()
            return self._rec.recognize_google(audio, language=SPEECH_LANG).lower().strip()
        except (sr.UnknownValueError, sr.RequestError):
            return None

    def listen_command(self) -> dict | None:
        with self._mic as source:
            try:
                audio = self._rec.listen(source, timeout=COMMAND_TIMEOUT)
                text  = self._transcribe(audio)
                return parse_voice(text) if text else None
            except sr.WaitTimeoutError:
                return None
