"""
소맥 전체 로봇 테스트

엔터를 누를 때마다 소맥을 한 잔 만듭니다.
종료: Ctrl+C

사용법:
    python -m testing.somaek_test
"""

import asyncio
import sys
from config import HUB_CUP_NAME, HUB_BOTTLE_NAME, DRINKS
from pc1.hub_client import HubClient
from pc1.dispenser import Dispenser
from pc1.rail import Rail

# 소맥 레시피 (ml) — config.py 에서 조정 가능
SOMAEK_RECIPE = {
    3: 50,   # 소주 (bottle 3)
    2: 50,  # 맥주 (bottle 2)
    1: 50
}


async def make_somaek(dispenser: Dispenser, rail: Rail, count: int):
    print(f"\n[{count}번째 소맥] 제조 시작")

    print("  홈 복귀 중...")
    await rail.home()

    for bottle, ml in SOMAEK_RECIPE.items():
        name = DRINKS.get(bottle, f"bottle {bottle}")
        print(f"  {name} {ml}ml 디스펜싱...")
        await rail.move_to(bottle)
        await dispenser.dispense(bottle, ml)

    print("  믹싱 스테이션으로 이동...")
    await rail.mix()
    print("  믹싱 중...")
    await dispenser.mix()

    print("  홈 복귀...")
    await rail.home()

    print(f"[{count}번째 소맥] 완료! 음료를 가져가세요.")


async def main():
    cup_hub    = HubClient(HUB_CUP_NAME)
    bottle_hub = HubClient(HUB_BOTTLE_NAME)

    print("BLE 허브 연결 중...")
    connected = await asyncio.gather(
        cup_hub.connect(),
        bottle_hub.connect(),
    )
    if not all(connected):
        print("허브 연결 실패.")
        sys.exit(1)

    print("두 허브의 READY 신호 대기 중 (허브 버튼을 눌러 프로그램을 시작하세요)...")
    await asyncio.gather(
        cup_hub.ready_event.wait(),
        bottle_hub.ready_event.wait(),
    )
    print("모든 허브 준비 완료.")

    dispenser = Dispenser(bottle_hub)
    rail      = Rail(cup_hub)

    print("config.py 설정 전송 중...")
    await asyncio.gather(
        dispenser.configure(),
        rail.configure(),
    )
    print("설정 완료.")

    print("레일 홈 복귀 중...")
    await rail.home()
    print("준비 완료.\n")

    print("── 소맥 레시피 ──────────────────────")
    for bottle, ml in SOMAEK_RECIPE.items():
        print(f"  {DRINKS.get(bottle, f'bottle {bottle}')}: {ml}ml")
    print("─────────────────────────────────────")
    print("엔터를 누를 때마다 소맥을 만듭니다. 종료: Ctrl+C\n")

    loop  = asyncio.get_running_loop()
    count = 0
    try:
        while True:
            await loop.run_in_executor(None, input, "엔터 > ")
            count += 1
            await make_somaek(dispenser, rail, count)
    except (KeyboardInterrupt, asyncio.CancelledError, EOFError):
        pass
    finally:
        print("\n종료 중...")
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
        print("종료됐습니다.")


if __name__ == "__main__":
    asyncio.run(main())
