"""
Hub 인터랙티브 테스트 CLI

허브가 지원하는 모든 명령어를 CMD에서 직접 입력해 동작을 확인합니다.

사용법:
    python -m testing.hub_test --hub bottle
    python -m testing.hub_test --hub cup
    python -m testing.hub_test --hub bottle --name "My Bottle Hub"
    python -m testing.hub_test --hub cup    --name "My Cup Hub"

특수 명령어 (허브로 전송되지 않음):
    help   — 사용 가능한 명령어 목록 출력
    quit   — 허브에 bye 없이 연결만 종료
    bye    — 허브 프로그램 종료 후 연결 종료
"""

import asyncio
import argparse
from config import HUB_BOTTLE_NAME, HUB_CUP_NAME
from pc1.hub_client import HubClient
from pc1.dispenser import Dispenser
from pc1.rail import Rail


# ── 허브별 명령어 정의 ───────────────────────────────────────────────────────

BOTTLE_COMMANDS = [
    ("DISPENSE:<병번호>:<시간ms>",  "예) DISPENSE:1:1500  — 지정 시간 동안 디스펜싱 (병: 1=소주/F, 2=맥주/D, 3=탄산/B)"),
    ("VALVE_OPEN:<병번호>",         "예) VALVE_OPEN:2     — 밸브 열기 (수동 닫기 전까지 열림)"),
    ("VALVE_CLOSE:<병번호>",        "예) VALVE_CLOSE:2    — 열린 밸브 닫기"),
    ("MIX:<시간ms>",                "예) MIX:3000         — 숟가락 내리기→회전→올리기"),
    ("bye",                         "허브 프로그램 종료"),
]

CUP_COMMANDS = [
    ("HOME",          "홈 위치 색깔 마커 또는 스톨 감지로 홈 복귀"),
    ("MOVE:<포지션>", "예) MOVE:1 / MOVE:2 / MOVE:3 / MOVE:mix  — 색깔 마커 감지 시 정지"),
    ("SCAN",          "현재 거리 센서 값 반환 (mm) — 스테이션 보정 확인용"),
    ("GET_POS",       "현재 기억된 위치 반환"),
    ("bye",           "허브 프로그램 종료"),
]

# 클라이언트 쪽에서 허용된 명령어 접두사 (경고 필터용)
BOTTLE_PREFIXES = {"DISPENSE:", "VALVE_OPEN:", "VALVE_CLOSE:", "MIX:", "bye"}
CUP_PREFIXES    = {"HOME", "MOVE:", "SCAN", "GET_POS", "bye"}


def _print_help(hub_type: str):
    cmds = BOTTLE_COMMANDS if hub_type == "bottle" else CUP_COMMANDS
    hub_label = "Bottle Hub (디스펜서)" if hub_type == "bottle" else "Cup Hub (레일)"
    print(f"\n{'─'*50}")
    print(f"  {hub_label} — 사용 가능한 명령어")
    print(f"{'─'*50}")
    for cmd, desc in cmds:
        print(f"  {cmd:<32}  {desc}")
    print(f"{'─'*50}")
    print("  help   — 이 목록 다시 보기")
    print("  quit   — 연결 종료 (허브 프로그램 유지)")
    print(f"{'─'*50}\n")


def _warn_if_unknown(command: str, hub_type: str):
    prefixes = BOTTLE_PREFIXES if hub_type == "bottle" else CUP_PREFIXES
    if not any(command.startswith(p) for p in prefixes):
        print(f"  [경고] '{command}' 는 이 허브가 지원하지 않는 명령어일 수 있습니다.")


async def run_repl(hub: HubClient, hub_type: str):
    loop = asyncio.get_running_loop()
    _print_help(hub_type)

    while True:
        try:
            raw = await loop.run_in_executor(None, input, "> ")
        except EOFError:
            break

        command = raw.strip()
        if not command:
            continue

        if command.lower() == "help":
            _print_help(hub_type)
            continue

        if command.lower() == "quit":
            print("연결을 종료합니다. (허브 프로그램은 계속 실행 중)")
            break

        _warn_if_unknown(command, hub_type)

        # 명령 전송
        try:
            await hub.send(command)
        except Exception as e:
            print(f"  [전송 오류] {e}")
            continue

        # 허브가 READY 를 다시 보낼 때까지 대기 (명령 처리 완료 신호)
        try:
            await asyncio.wait_for(hub.ready_event.wait(), timeout=30.0)
        except asyncio.TimeoutError:
            print("  [타임아웃] 허브 응답이 30초 내에 오지 않았습니다.")

        if command == "bye":
            print("허브 프로그램이 종료됐습니다.")
            break


async def main():
    parser = argparse.ArgumentParser(description="Hub 인터랙티브 테스트 CLI")
    parser.add_argument(
        "--hub", required=True, choices=["bottle", "cup"],
        help="테스트할 허브 종류",
    )
    parser.add_argument(
        "--name", default=None,
        help="BLE 허브 이름 (생략 시 config.py 기본값 사용)",
    )
    args = parser.parse_args()

    if args.name:
        hub_name = args.name
    elif args.hub == "bottle":
        hub_name = HUB_BOTTLE_NAME
    else:
        hub_name = HUB_CUP_NAME

    hub = HubClient(hub_name)
    print(f"[{hub_name}] BLE 연결 중...")
    if not await hub.connect():
        print("연결 실패. BLE 허브 이름을 확인하세요.")
        return

    print(f"허브 READY 신호 대기 중 (허브 버튼을 눌러 프로그램을 시작하세요)...")
    await hub.ready_event.wait()
    print(f"[{hub_name}] 준비 완료.")

    print("config.py 설정 전송 중...")
    if args.hub == "bottle":
        await Dispenser(hub).configure()
    else:
        rail = Rail(hub)
        await rail.configure()
        print("레일 홈 복귀 중...")
        await rail.home()
    print("설정 완료.\n")

    try:
        await run_repl(hub, args.hub)
    finally:
        await hub.disconnect()
        print("BLE 연결 종료.")


if __name__ == "__main__":
    asyncio.run(main())
