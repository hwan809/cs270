"""
Console UI — ANSI terminal display.
"""

import sys
import time

RST    = "\033[0m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
CYAN   = "\033[96m"
BLUE   = "\033[94m"
MAG    = "\033[95m"
WHITE  = "\033[97m"

EMOTION_COLOR = {
    "happy":     YELLOW,
    "sad":       BLUE,
    "angry":     RED,
    "stressed":  MAG,
    "surprised": CYAN,
    "neutral":   WHITE,
    "disgust":   DIM,
}
DRINK_ICONS = {1: "🍶", 2: "🍺", 3: "🥤"}


def _ts():   return time.strftime("%H:%M:%S")
def clear(): sys.stdout.write("\033[2J\033[H"); sys.stdout.flush()
def newline(): print()
def divider(): print(f"{DIM}{'─' * 44}{RST}")


def banner():
    print(f"{CYAN}{BOLD}")
    print("╔══════════════════════════════════════╗")
    print("║          소맥메이커  🍻               ║")
    print("║   LEGO SPIKE Bartender Robot          ║")
    print("╚══════════════════════════════════════╝")
    print(RST)


def log(msg: str, level: str = "info"):
    color = {"info": CYAN, "ok": GREEN, "warn": YELLOW, "error": RED}.get(level, RST)
    print(f"{DIM}[{_ts()}]{RST} {color}{msg}{RST}")


def show_emotion(emotion: str, intensity: float):
    color = EMOTION_COLOR.get(emotion, WHITE)
    bar   = "█" * int(intensity * 24) + "░" * (24 - int(intensity * 24))
    print(f"\n{BOLD}감정{RST}  {color}{emotion:<12}{RST}  [{YELLOW}{bar}{RST}] {intensity:.0%}")


def show_recipe(recipe: dict[int, int], drinks: dict[int, str]):
    print(f"\n{BOLD}레시피{RST}")
    total = max(sum(recipe.values()), 1)
    for bottle, ml in recipe.items():
        if ml <= 0:
            continue
        bar = "█" * int(ml / total * 28)
        print(f"  {DRINK_ICONS.get(bottle,'🍹')} {drinks[bottle]:<8}  {CYAN}{bar:<28}{RST}  {ml:>3}ml")
    print()


def show_dispensing(bottle: int, ml: int, poured: int, total: int):
    pct    = poured / max(total, 1)
    filled = int(pct * 36)
    bar    = "█" * filled + "░" * (36 - filled)
    sys.stdout.write(f"\r  {DRINK_ICONS.get(bottle,'🍹')} [{GREEN}{bar}{RST}]  {poured}/{total}ml")
    sys.stdout.flush()


def show_countdown(seconds: int):
    print(f"{YELLOW}  ⏱  {seconds}초 후 제조 시작. 취소: '취소' 또는 Ctrl+C{RST}")
