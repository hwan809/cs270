"""
USB 시리얼 ping-pong 반복 테스트

연결이 확인된 뒤 연속으로 ping을 보내 RTT와 안정성을 측정합니다.

사용법:
    python usb_ping.py COM3
    python usb_ping.py COM3 --interval 0.2
"""

import argparse
import json
import sys
import time

import serial
import serial.tools.list_ports

LEGO_VID = 0x0694
BAUD = 115200
TIMEOUT = 5.0


def auto_find_port() -> str | None:
    ports = list(serial.tools.list_ports.comports())
    lego = [p.device for p in ports if p.vid == LEGO_VID]
    candidates = lego or [p.device for p in ports]
    for port in candidates:
        try:
            with serial.Serial(port, BAUD, timeout=2.0, write_timeout=2.0,
                               xonxoff=False, rtscts=False, dsrdtr=False) as s:
                s.reset_input_buffer()
                s.write(b'{"cmd":"ping"}\n')
                s.flush()
                raw = s.readline()
                if raw and json.loads(raw.decode().strip()).get("status") == "ok":
                    return port
        except Exception:
            pass
    return None


def read_response(ser: serial.Serial, seq: int, timeout: float) -> dict | None:
    """
    SPIKE 허브는 센서 텔레메트리({"m":...})를 \r 로 끝내며 계속 흘려보냄.
    사용자 코드 출력은 \r\n 으로 끝남.
    버퍼를 누적해 모든 줄을 파싱하고, seq 가 일치하는 응답만 반환.
    """
    deadline = time.time() + timeout
    buf = b""

    while time.time() < deadline:
        chunk = ser.read(ser.in_waiting or 1)
        if chunk:
            buf += chunk

        # \r\n 과 \r 모두 줄 구분자로 처리
        lines = buf.replace(b"\r\n", b"\n").replace(b"\r", b"\n").split(b"\n")
        buf = lines[-1]  # 아직 완성되지 않은 마지막 조각 유지

        for line in lines[:-1]:
            line = line.strip()
            if not line:
                continue
            try:
                resp = json.loads(line)
                # 텔레메트리("m" 키) 무시, 우리 응답("status" 키)만 처리
                if "status" in resp and resp.get("seq") == seq:
                    return resp
            except json.JSONDecodeError:
                pass

    return None


def run(port: str, interval: float):
    print(f"연결 중: {port}  ({BAUD} baud) …", end=" ", flush=True)
    try:
        ser = serial.Serial(port, BAUD, timeout=0.1, write_timeout=3.0,
                            xonxoff=False, rtscts=False, dsrdtr=False)
    except Exception as e:
        print(f"\n포트 열기 실패: {e}")
        sys.exit(1)

    ser.reset_input_buffer()
    ser.reset_output_buffer()
    print("OK\n")
    print(f"{'seq':>6}  {'RTT(ms)':>8}  {'status'}")
    print("-" * 35)

    seq = 0
    ok_count = 0
    fail_count = 0

    try:
        while True:
            cmd = json.dumps({"cmd": "ping", "seq": seq}).encode() + b"\n"
            t0 = time.perf_counter()
            ser.write(cmd)
            ser.flush()

            resp = read_response(ser, seq, TIMEOUT)
            rtt_ms = (time.perf_counter() - t0) * 1000

            if resp is not None:
                status = resp.get("status", "?")
                print(f"{seq:>6}  {rtt_ms:>8.1f}  {status}")
                if status == "ok":
                    ok_count += 1
                else:
                    fail_count += 1
            else:
                print(f"{seq:>6}  {'TIMEOUT':>8}  —")
                fail_count += 1

            seq += 1
            time.sleep(interval)

    except KeyboardInterrupt:
        print(f"\n\n총 {seq}회  성공={ok_count}  실패={fail_count}")
    finally:
        ser.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("port", nargs="?", help="COM 포트 (예: COM3). 생략 시 자동 탐색")
    parser.add_argument("--interval", type=float, default=0.5, help="ping 간격(초), 기본 0.5")
    args = parser.parse_args()

    port = args.port
    if not port:
        print("포트 자동 탐색 중 …")
        port = auto_find_port()
        if not port:
            print("허브를 찾지 못했습니다. diagnose.py 를 먼저 실행하세요.")
            sys.exit(1)
        print(f"  발견: {port}\n")

    run(port, args.interval)


if __name__ == "__main__":
    main()
