"""
거리 보정 스크립트 — 엔코더 기반 (Cup Hub BLE 연결)

홈 엔드스탑에서 각 스테이션까지 거리를 인터랙티브하게 측정합니다.
  +N  : N mm 앞으로 이동
  -N  : N mm 뒤로 이동
  Enter : 현재 위치를 해당 스테이션으로 확정

사용법:
    python -m pc1.calibrate_distance
"""

import asyncio
import re
from pathlib import Path

from config import HUB_CUP_NAME, HUB2_SPEED, DRINKS
from pc1.hub_client import HubClient

CONFIG_PATH = Path(__file__).resolve().parents[1] / "config.py"

STATIONS = [
    ("1",   f"병 1 ({DRINKS[1]})"),
    ("2",   f"병 2 ({DRINKS[2]})"),
    ("3",   f"병 3 ({DRINKS[3]})"),
    ("mix", "믹싱"),
]


async def get_dist(hub: HubClient) -> int:
    await hub.send_and_wait("GET_DIST", "DIST:")
    return int(hub.latest_response.split(":")[1])


async def nudge(hub: HubClient, mm: int) -> int:
    await hub.send_and_wait(f"NUDGE:{mm}", "NUDGE_DONE:")
    return int(hub.latest_response.split(":")[1])


async def calibrate():
    hub = HubClient(HUB_CUP_NAME)
    if not await hub.connect():
        print("[ERROR] Cup Hub에 연결할 수 없습니다.")
        return

    print("허브 READY 신호 대기 중 (허브 버튼을 눌러 시작)...")
    await hub.ready_event.wait()

    await hub.send_and_wait(
        f"CONFIG:SPEED={HUB2_SPEED},D1=0,D2=0,D3=0,Dmix=0", "CONFIG_OK"
    )

    print(f"\n{'═'*56}")
    print("  엔코더 거리 보정")
    print("  홈(엔드스탑)을 기준으로 각 스테이션 위치를 잡습니다.")
    print(f"{'═'*56}\n")

    # 홈 복귀
    print("  홈 복귀 중 (엔드스탑까지 후진)...")
    await hub.send_and_wait("HOME", "HOME_DONE")
    print("  홈 완료. 엔코더 = 0 mm\n")

    results: dict[str, int] = {}

    for key, label in STATIONS:
        print(f"  ── [{label}] ──────────────────────────────")
        print("  +N / -N 입력으로 이동, Enter 로 위치 확정")

        while True:
            dist = await get_dist(hub)
            raw = await asyncio.to_thread(
                input, f"  현재 {dist:>5} mm  >  "
            )
            raw = raw.strip()
            if raw == "":
                results[key] = dist
                print(f"  → [{label}] = {dist} mm 확정\n")
                break
            try:
                mm = int(raw)
                new_dist = await nudge(hub, mm)
                print(f"  이동 완료 → {new_dist} mm")
            except ValueError:
                print("  숫자를 입력하세요. (예: +50, -10)")

    # ── 결과 출력 ────────────────────────────────────────────────────────────
    print(f"\n{'─'*56}")
    print("  측정 결과 (홈 기준):\n")
    for key, label in STATIONS:
        print(f"    {label:20s}: {results[key]:>5} mm")

    # ── 순서 검증 (1 < 2 < 3 < mix) ─────────────────────────────────────────
    vals = [results[k] for k, _ in STATIONS]
    if vals != sorted(vals):
        print("\n  ⚠  거리 순서가 예상(작음→큼)과 다릅니다. 스테이션 배치를 확인하세요.")

    # ── config.py 자동 갱신 ──────────────────────────────────────────────────
    ans = await asyncio.to_thread(
        input, "\n  config.py 에 자동으로 저장할까요? [y/N] : "
    )
    if ans.strip().lower() == "y":
        _update_config(results)
        print("  config.py 저장 완료.")
    else:
        print("\n  >>> config.py 에 직접 붙여넣으세요:\n")
        print("  HUB2_STATION_DISTANCES = {   # mm from home endstop")
        for key, label in STATIONS:
            print(f'      "{key}":    {results[key]},   # {label}')
        print("  }")

    print(f"{'─'*56}\n")

    try:
        await hub.send("bye")
        await asyncio.sleep(0.3)
    except Exception:
        pass
    await hub.disconnect()
    print("보정 완료.")


def _update_config(results: dict[str, int]):
    text = CONFIG_PATH.read_text(encoding="utf-8")
    new_block = (
        "HUB2_STATION_DISTANCES = {   # mm from home endstop — CALIBRATION_NEEDED\n"
        + "".join(
            f'    "{k}":    {results[k]},\n'
            for k, _ in STATIONS
        )
        + "}"
    )
    text = re.sub(
        r"HUB2_STATION_DISTANCES\s*=\s*\{[^}]*\}",
        new_block,
        text,
        flags=re.DOTALL,
    )
    CONFIG_PATH.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(calibrate())
