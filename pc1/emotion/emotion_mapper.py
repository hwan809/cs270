"""
Module 4 — Emotion + voice intent → drink recipe.
"""

from config import BASE_VOLUME_ML

EMOTION_BASE_RATIOS: dict[str, list[float]] = {
    "happy":     [0.20, 0.60, 0.20],
    "sad":       [0.55, 0.30, 0.15],
    "angry":     [0.45, 0.40, 0.15],
    "stressed":  [0.45, 0.30, 0.25],
    "surprised": [0.25, 0.45, 0.30],
    "neutral":   [0.33, 0.34, 0.33],
    "disgust":   [0.30, 0.45, 0.25],
}

MAX_SHIFT = 0.25


def map_emotion_to_recipe(emotion: str, intensity: float) -> dict[int, int]:
    base  = list(EMOTION_BASE_RATIOS.get(emotion, EMOTION_BASE_RATIOS["neutral"]))
    shift = (intensity - 0.5) * 2 * MAX_SHIFT
    base[0] = min(0.90, max(0.05, base[0] + shift))
    base[2] = min(0.90, max(0.05, base[2] - shift))
    total  = sum(base)
    ratios = [r / total for r in base]
    recipe = {i + 1: round(BASE_VOLUME_ML * ratios[i]) for i in range(3)}
    recipe[1] += BASE_VOLUME_ML - sum(recipe.values())
    return recipe


VOICE_KEYWORDS: dict[str, tuple] = {
    "약하게":    ("intensity", 0.2),
    "가볍게":    ("intensity", 0.2),
    "light":     ("intensity", 0.2),
    "보통":      ("intensity", 0.5),
    "medium":    ("intensity", 0.5),
    "강하게":    ("intensity", 0.9),
    "세게":      ("intensity", 0.9),
    "strong":    ("intensity", 0.9),
    "추천":      ("mode",      "auto"),
    "알아서":    ("mode",      "auto"),
    "recommend": ("mode",      "auto"),
    "소주":      ("drink",     1),
    "맥주":      ("drink",     2),
    "탄산":      ("drink",     3),
    "취소":      ("cancel",    None),
    "cancel":    ("cancel",    None),
    "stop":      ("cancel",    None),
    "그만":      ("cancel",    None),
}


def parse_voice(text: str) -> dict:
    text_lower = text.lower()
    result: dict = {"raw": text}
    for keyword, (key, value) in VOICE_KEYWORDS.items():
        if keyword in text_lower:
            result[key] = value
            break
    return result


def voice_to_recipe(command: dict) -> dict[int, int] | None:
    if command.get("cancel"):
        return None
    if "drink" in command:
        bottle = command["drink"]
        return {1: 0, 2: 0, 3: 0, bottle: BASE_VOLUME_ML}
    return map_emotion_to_recipe("neutral", command.get("intensity", 0.5))
