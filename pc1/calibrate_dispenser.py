"""
디스펜서 유속 보정 스크립트 — 반복 측정 + 선형 회귀

사용법:
    python -m pc1.calibrate_dispenser --bottle 1   # 소주
    python -m pc1.calibrate_dispenser --bottle 2   # 맥주
    python -m pc1.calibrate_dispenser --bottle 3   # 탄산음료

동작:
    [Enter]       → 밸브 열림 (물 시작)
    [Enter] 다시  → 밸브 닫힘 (물 멈춤)
    ml 입력       → 측정값 기록 + 표 + 선형 회귀 갱신
    q + [Enter]   → 종료 (결과 CSV 저장)

팁: 매 측정마다 컵을 채우는 양을 달리하면 (반 컵, 한 컵, 한 컵 반...)
    회귀 정확도가 높아집니다.
"""

import asyncio
import argparse
import csv
import time
from datetime import datetime
from pathlib import Path

import numpy as np

from config import HUB_BOTTLE_NAME, DRINKS
from pc1.hub_client import HubClient

# ── 상수 ──────────────────────────────────────────────────────────────────────

R2_GOOD   = 0.995   # R² ≥ 이 값이면 "우수"로 표시
MIN_FOR_R = 2       # 선형 회귀에 필요한 최소 측정 횟수

# ── 결과 표시 ─────────────────────────────────────────────────────────────────

def _regression(times: list, volumes: list):
    """numpy polyfit 으로 선형 회귀. (slope, intercept, r2) 반환."""
    t = np.array(times,   dtype=float)
    v = np.array(volumes, dtype=float)
    slope, intercept = np.polyfit(t, v, 1)
    y_pred = slope * t + intercept
    ss_res = np.sum((v - y_pred) ** 2)
    ss_tot = np.sum((v - v.mean()) ** 2)
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 1e-12 else 1.0
    return slope, intercept, r2


def _show(measurements: list[tuple[float, float]], bottle: int):
    """측정 테이블 + 선형 회귀 결과를 콘솔에 출력."""
    W = 60
    print(f"\n{'─' * W}")
    print(f"  {'#':>3}  {'시간(s)':>9}  {'부피(ml)':>9}  {'단순 유속':>11}")
    print(f"  {'─'*3}  {'─'*9}  {'─'*9}  {'─'*11}")
    for i, (t, v) in enumerate(measurements, 1):
        print(f"  {i:>3}  {t:>9.3f}  {v:>9.1f}  {v/t:>10.3f} ml/s")

    n = len(measurements)
    times   = [t for t, _ in measurements]
    volumes = [v for _, v in measurements]

    if n >= MIN_FOR_R:
        slope, intercept, r2 = _regression(times, volumes)
        quality = "✓ 우수" if r2 >= R2_GOOD else ("△ 보통" if r2 >= 0.98 else "✗ 측정 추가 필요")
        sign    = "+" if intercept >= 0 else "-"

        print(f"\n  [선형 회귀 — n={n}]")
        print(f"    V  =  {slope:.4f} × t  {sign}  {abs(intercept):.4f}")
        print(f"    R² =  {r2:.5f}   {quality}")
        print(f"\n  >>> FLOW_RATE[{bottle}] = {slope:.4f}  # ml/s  ({DRINKS[bottle]})")
    else:
        remaining = MIN_FOR_R - n
        print(f"\n  (회귀를 위해 {remaining}회 더 측정하세요)")

    print(f"{'─' * W}\n")


def _save_csv(measurements: list[tuple[float, float]], bottle: int) -> Path:
    """측정 데이터를 CSV 로 저장."""
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = Path(f"calibration_bottle{bottle}_{ts}.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["#", "time_s", "volume_ml", "flow_rate_ml_per_s"])
        for i, (t, v) in enumerate(measurements, 1):
            w.writerow([i, round(t, 4), round(v, 2), round(v / t, 4)])
    return path


# ── 메인 ─────────────────────────────────────────────────────────────────────

async def calibrate(bottle: int):
    hub = HubClient(HUB_BOTTLE_NAME)
    if not await hub.connect():
        print("[ERROR] Bottle Hub 에 연결할 수 없습니다.")
        return

    print("허브 READY 신호 대기 중 (허브 버튼을 눌러 프로그램을 시작하세요)...")
    await hub.ready_event.wait()

    drink = DRINKS[bottle]
    print(f"\n{'═' * 60}")
    print(f"  병 {bottle}  ({drink})  유속 보정  —  선형 회귀 모드")
    print(f"  컵을 채우는 양을 매번 달리하면 정확도가 올라갑니다.")
    print(f"{'═' * 60}")

    measurements: list[tuple[float, float]] = []
    n = 1

    while True:
        prompt = await asyncio.to_thread(
            input,
            f"\n[측정 {n}]  빈 컵을 놓고 [Enter]  /  종료 → q + [Enter] :  ",
        )
        if prompt.strip().lower() == "q":
            break

        # ── 밸브 열기 ─────────────────────────────────────────────────────────
        await hub.send(f"VALVE_OPEN:{bottle}")
        await hub.wait_for(f"VALVE_OPENED:{bottle}")
        t_start = time.perf_counter()
        print("  ▶  물 나오는 중...")

        # ── 컵이 찼을 때 Enter ────────────────────────────────────────────────
        await asyncio.to_thread(input, "     컵이 다 차면 [Enter] : ")
        t_stop = time.perf_counter()

        # ── 밸브 닫기 ─────────────────────────────────────────────────────────
        await hub.send(f"VALVE_CLOSE:{bottle}")
        await hub.wait_for(f"VALVE_CLOSED:{bottle}")

        elapsed = t_stop - t_start
        print(f"  ◼  {elapsed:.3f}s 경과.")

        # ── 부피 입력 ─────────────────────────────────────────────────────────
        try:
            raw = await asyncio.to_thread(input, "     실제 담긴 양 (ml) : ")
            volume = float(raw.strip())
            if volume <= 0:
                raise ValueError
        except ValueError:
            print("  [오류] 양수 숫자를 입력하세요. 이 측정은 건너뜁니다.")
            continue

        measurements.append((elapsed, volume))
        _show(measurements, bottle)
        n += 1

    # ── 종료 처리 ─────────────────────────────────────────────────────────────
    if not measurements:
        print("측정 데이터가 없습니다. 보정 중단.")
    else:
        print("\n===  최종 결과  ===")
        _show(measurements, bottle)

        csv_path = _save_csv(measurements, bottle)
        print(f"  측정 데이터 저장: {csv_path}")

    try:
        await hub.send("bye")
        await asyncio.sleep(0.3)
    except Exception:
        pass
    await hub.disconnect()
    print("보정 완료.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="디스펜서 유속 보정 (선형 회귀)")
    parser.add_argument(
        "--bottle", type=int, required=True, choices=[1, 2, 3],
        help="보정할 병 번호 (1=소주  2=맥주  3=탄산음료)",
    )
    args = parser.parse_args()
    asyncio.run(calibrate(args.bottle))
