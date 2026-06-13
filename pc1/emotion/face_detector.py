"""
Module 1 — Real-time facial emotion detection with live preview window.
"""

import threading
import numpy as np
import cv2
from collections import deque
from pathlib import Path
from deepface import DeepFace
from PIL import Image, ImageDraw, ImageFont

DEEPFACE_TO_INTERNAL = {
    "happy":    "happy",
    "sad":      "sad",
    "angry":    "angry",
    "fear":     "stressed",
    "surprise": "surprised",
    "neutral":  "neutral",
    "disgust":  "disgust",
}

EMOTION_KO = {
    "happy":     "행복",
    "sad":       "슬픔",
    "angry":     "화남",
    "stressed":  "스트레스",
    "surprised": "놀람",
    "neutral":   "무표정",
    "disgust":   "불쾌",
}

SMOOTHING_FRAMES = 5
WINDOW_NAME = "Somaek Maker - Face"

# Windows 한글 폰트 경로 우선순위
_FONT_CANDIDATES = [
    "C:/Windows/Fonts/malgun.ttf",    # 맑은 고딕
    "C:/Windows/Fonts/gulim.ttc",
    "C:/Windows/Fonts/batang.ttc",
]

def _load_font(size: int) -> ImageFont.FreeTypeFont:
    for path in _FONT_CANDIDATES:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()

_FONT_LG = _load_font(28)
_FONT_SM = _load_font(18)


class FaceDetector:
    def __init__(self):
        self._cap = cv2.VideoCapture(0)
        self._history: deque[tuple[str, float]] = deque(maxlen=SMOOTHING_FRAMES)
        self._lock = threading.Lock()
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def _draw(self, frame, emotion: str, intensity: float, region: dict):
        h, w = frame.shape[:2]

        # 얼굴 박스 (OpenCV — ASCII만 사용)
        rx, ry, rw, rh = (region.get(k, 0) for k in ("x", "y", "w", "h"))
        if rw > 0:
            cv2.rectangle(frame, (rx, ry), (rx + rw, ry + rh), (0, 220, 100), 2)

        # 한글 텍스트 — PIL로 렌더링
        pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil)

        label = f"{EMOTION_KO.get(emotion, emotion)}  {intensity * 100:.0f}%"
        draw.text((rx, max(ry - 34, 2)), label, font=_FONT_LG, fill=(0, 220, 100))
        draw.text((10, h - 30), "Space → 음료 제조  |  M → 모드 전환",
                  font=_FONT_SM, fill=(200, 200, 200))

        frame[:] = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)

    def _loop(self):
        while self._running:
            ret, frame = self._cap.read()
            if not ret:
                continue

            emotion, intensity, region = "neutral", 0.0, {}
            try:
                result   = DeepFace.analyze(frame, actions=["emotion"],
                                            enforce_detection=False, silent=True)
                emotions = result[0]["emotion"]
                raw      = max(emotions, key=emotions.get)
                intensity = emotions[raw] / 100.0
                mapped    = DEEPFACE_TO_INTERNAL.get(raw, "neutral")
                region    = result[0].get("region", {})
                emotion   = mapped
                with self._lock:
                    self._history.append((mapped, intensity))
            except Exception:
                pass

            self._draw(frame, emotion, intensity, region)
            cv2.imshow(WINDOW_NAME, frame)
            cv2.waitKey(1)

    def get_emotion(self) -> tuple[str, float] | None:
        with self._lock:
            if len(self._history) < 3:
                return None
            emotions = [e for e, _ in self._history]
            dominant = max(set(emotions), key=emotions.count)
            avg_intensity = float(
                np.mean([i for e, i in self._history if e == dominant])
            )
            return dominant, avg_intensity

    def release(self):
        self._running = False
        self._cap.release()
        cv2.destroyAllWindows()
