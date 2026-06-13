"""
Module 6b — TTS 피드백.
"""

import pyttsx3
from config import DRINKS


class Speaker:
    def __init__(self):
        self._engine = pyttsx3.init()
        self._engine.setProperty("rate", 160)
        self._set_korean_voice()

    def _set_korean_voice(self):
        for voice in self._engine.getProperty("voices"):
            if any(k in voice.name.lower() or k in voice.id.lower()
                   for k in ("korean", "ko", "한국")):
                self._engine.setProperty("voice", voice.id)
                return

    def _say(self, text: str):
        self._engine.say(text)
        self._engine.runAndWait()

    def listening(self):        self._say("말씀해 주세요.")
    def recipe_ready(self):     self._say("음료를 만들기 시작합니다. 잠시만 기다려 주세요.")
    def done(self):             self._say("음료가 완성됐습니다! 맛있게 드세요.")
    def cancelled(self):        self._say("취소됐습니다.")
    def error(self):            self._say("죄송합니다, 오류가 발생했습니다. 다시 시도해 주세요.")

    def emotion_detected(self, emotion: str, intensity: float):
        strength = "강한" if intensity > 0.6 else ("약한" if intensity < 0.4 else "")
        self._say(f"{strength} {emotion} 감정이 느껴지시는군요. 음료를 준비할게요.")

    def dispensing(self, bottle: int, volume_ml: int):
        self._say(f"{DRINKS[bottle]} {volume_ml}밀리리터를 따르는 중입니다.")

    def countdown(self, seconds: int):
        self._say(f"{seconds}초 후 음료를 만들겠습니다. 취소하려면 '취소'라고 말해 주세요.")
