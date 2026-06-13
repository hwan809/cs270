"""
소맥메이커 메인 오케스트레이터 — PC 1대 + Hub 2대 (BLE)

모드:
  face  — Space → 현재 감정 즉시 인식 → 음료 제조
  voice — Space → 음성 명령 수신 → 음료 제조

키:
  Space : 트리거 (음료 제조 시작)
  M     : face / voice 모드 전환

연결 토폴로지:
    bottle_hub ↔ [BLE] ↔ PC ↔ [BLE] ↔ cup_hub

실행:
    python -m pc1.main
    python -m pc1.main --mode voice
"""

import asyncio
import argparse
import sys
import threading
import msvcrt

from config import HUB_CUP_NAME, HUB_BOTTLE_NAME, DRINKS
from pc1.hub_client import HubClient
from pc1.dispenser import Dispenser
from pc1.rail import Rail
from pc1.emotion.face_detector import FaceDetector
from pc1.emotion.emotion_mapper import map_emotion_to_recipe, voice_to_recipe
from pc1.voice.listener import VoiceListener
from pc1.voice.speaker import Speaker
from pc1.ui import display as ui

_making  = False
_mode    = "face"   # "face" | "voice"
_trigger = threading.Event()


def _keyboard_listener():
    """Space: 트리거 / M: 모드 전환."""
    global _mode
    while True:
        key = msvcrt.getch()
        if key == b' ':
            _trigger.set()
        elif key in (b'm', b'M'):
            _mode = "voice" if _mode == "face" else "face"
            label = "얼굴 인식" if _mode == "face" else "LLM 음성"
            ui.log(f"[모드 전환] → {label} 모드", "info")


async def make_drink(recipe: dict, dispenser: Dispenser, rail: Rail, speaker: Speaker):
    global _making
    _making = True
    try:
        speaker.recipe_ready()
        ui.log("홈 포지션 이동 중...", "info")
        await rail.home()

        total_ml = sum(recipe.values())
        poured   = 0

        for bottle, ml in recipe.items():
            if ml <= 0:
                continue
            ui.log(f"{DRINKS[bottle]} {ml}ml 디스펜싱 중...", "info")
            speaker.dispensing(bottle, ml)
            await rail.move_to(bottle)
            await dispenser.dispense(bottle, ml)
            poured += ml
            ui.show_dispensing(bottle, ml, poured, total_ml)

        ui.newline()
        ui.log("믹싱 스테이션으로 이동 중...", "info")
        await rail.mix()
        ui.log("믹싱 중...", "info")
        await dispenser.mix()
        await rail.home()
        speaker.done()
        ui.log("완료! 음료를 가져가세요.", "ok")
        ui.divider()
    except Exception as e:
        speaker.error()
        ui.log(f"오류: {e}", "error")
    finally:
        _making = False


async def run_voice_flow(
    listener: VoiceListener, speaker: Speaker,
    dispenser: Dispenser, rail: Rail, loop: asyncio.AbstractEventLoop,
):
    speaker.listening()
    ui.log("음성 명령을 듣는 중...", "info")
    cmd = await loop.run_in_executor(None, listener.listen_command)
    if not cmd:
        ui.log("음성을 인식하지 못했습니다.", "warn")
        return
    recipe = voice_to_recipe(cmd)
    if recipe is None:
        speaker.cancelled()
        ui.log("취소됐습니다.", "warn")
        return
    ui.show_recipe(recipe, DRINKS)
    asyncio.ensure_future(make_drink(recipe, dispenser, rail, speaker))


async def run_face_flow(
    detector: FaceDetector, speaker: Speaker,
    dispenser: Dispenser, rail: Rail,
):
    result = detector.get_emotion()
    if not result:
        ui.log("얼굴 감정을 인식하지 못했습니다.", "warn")
        return
    emotion, intensity = result
    recipe = map_emotion_to_recipe(emotion, intensity)
    ui.show_emotion(emotion, intensity)
    ui.show_recipe(recipe, DRINKS)
    asyncio.ensure_future(make_drink(recipe, dispenser, rail, speaker))


async def main():
    global _mode

    parser = argparse.ArgumentParser()
    parser.add_argument("--cup-hub",    default=HUB_CUP_NAME,    help="Cup Hub BLE 이름")
    parser.add_argument("--bottle-hub", default=HUB_BOTTLE_NAME, help="Bottle Hub BLE 이름")
    parser.add_argument("--mode",       default="face", choices=["face", "voice"],
                        help="시작 모드 (기본: face)")
    args = parser.parse_args()
    _mode = args.mode

    ui.clear()
    ui.banner()

    cup_hub    = HubClient(args.cup_hub)
    bottle_hub = HubClient(args.bottle_hub)

    ui.log("BLE 허브 연결 중...", "info")
    connected = await asyncio.gather(cup_hub.connect(), bottle_hub.connect())
    if not all(connected):
        ui.log("허브 연결 실패. 프로그램을 종료합니다.", "error")
        sys.exit(1)

    ui.log("두 허브의 READY 신호 대기 중 (허브 버튼을 눌러 시작)...", "info")
    await asyncio.gather(
        cup_hub.ready_event.wait(),
        bottle_hub.ready_event.wait(),
    )
    ui.log("모든 허브 준비 완료.", "ok")

    dispenser = Dispenser(bottle_hub)
    rail      = Rail(cup_hub)

    ui.log("허브 설정 전송 중...", "info")
    await asyncio.gather(dispenser.configure(), rail.configure())
    ui.log("설정 완료.", "ok")

    ui.log("레일 홈 복귀 중...", "info")
    await rail.home()
    ui.log("준비 완료.", "ok")

    detector = FaceDetector()
    listener = VoiceListener()
    speaker  = Speaker()
    loop     = asyncio.get_running_loop()

    threading.Thread(target=_keyboard_listener, daemon=True).start()

    ui.divider()
    label = "얼굴 인식" if _mode == "face" else "LLM 음성"
    ui.log(f"시작 모드: {label}  |  Space: 실행  |  M: 모드 전환", "ok")
    ui.divider()

    try:
        while True:
            if _making:
                await asyncio.sleep(0.1)
                continue

            current_mode = _mode
            label = "얼굴 인식" if current_mode == "face" else "LLM 음성"
            ui.log(f"[{label}] Space 를 누르세요...", "info")

            await loop.run_in_executor(None, _trigger.wait)
            _trigger.clear()

            if _making:
                continue

            if current_mode == "face":
                await run_face_flow(detector, speaker, dispenser, rail)
            else:
                await run_voice_flow(listener, speaker, dispenser, rail, loop)

    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        ui.log("종료 중...", "info")
        try:
            await asyncio.wait_for(
                asyncio.gather(
                    cup_hub.send("bye"),
                    bottle_hub.send("bye"),
                    return_exceptions=True,
                ),
                timeout=2.0,
            )
            await asyncio.sleep(0.5)
        except asyncio.TimeoutError:
            pass
        await cup_hub.disconnect()
        await bottle_hub.disconnect()
        detector.release()
        ui.log("종료됐습니다.", "info")


if __name__ == "__main__":
    asyncio.run(main())
