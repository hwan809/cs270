"""
PC → Hub 초음파 거리 센서 읽기

사용법:
    python pc_distance.py COM12           # 포트 A, 연속 측정
    python pc_distance.py COM12 --port B  # 포트 B
    python pc_distance.py COM12 --once    # 한 번만
"""

import argparse
import json
import sys
import time
import serial

BAUD = 115200
READ_TIMEOUT = 5.0


def read_response(ser: serial.Serial, timeout: float = READ_TIMEOUT) -> dict | None:
    deadline = time.time() + timeout
    buf = b""
    while time.time() < deadline:
        chunk = ser.read(ser.in_waiting or 1)
        if chunk:
            buf += chunk
        lines = buf.replace(b"\r\n", b"\n").replace(b"\r", b"\n").split(b"\n")
        buf = lines[-1]
        for line in lines[:-1]:
            line = line.strip()
            if not line:
                continue
            try:
                resp = json.loads(line)
                if "status" in resp:
                    return resp
            except json.JSONDecodeError:
                pass
    return None


def connect(com_port: str) -> serial.Serial:
    print(f"연결 중: {com_port} …", end=" ", flush=True)
    try:
        ser = serial.Serial(com_port, BAUD, timeout=0.1, write_timeout=3.0,
                            xonxoff=False, rtscts=False, dsrdtr=False)
    except Exception as e:
        print(f"\n포트 열기 실패: {e}")
        sys.exit(1)
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    time.sleep(0.2)
    ser.reset_input_buffer()
    print("OK")
    return ser


def get_distance(ser: serial.Serial, sensor_port: str) -> dict | None:
    cmd = json.dumps({"cmd": "get_distance", "port": sensor_port}).encode() + b"\n"
    ser.write(cmd)
    ser.flush()
    return read_response(ser)


def run(com_port: str, sensor_port: str, once: bool, interval: float):
    ser = connect(com_port)

    if once:
        resp = get_distance(ser, sensor_port)
        if resp and resp.get("status") == "ok":
            dist = resp.get("distance_cm")
            print(f"포트 {sensor_port}: {dist} cm" if dist is not None else f"포트 {sensor_port}: 범위 밖")
        else:
            print(f"오류: {resp}")
        ser.close()
        return

    print(f"\n포트 {sensor_port} 거리 연속 측정 — Ctrl+C 종료\n")
    print(f"{'#':>5}  {'거리(cm)':>10}")
    print("-" * 20)
    n = 0
    try:
        while True:
            resp = get_distance(ser, sensor_port)
            if resp and resp.get("status") == "ok":
                dist = resp.get("distance_cm")
                val = f"{dist:.1f}" if dist is not None else "범위 밖"
                print(f"{n:>5}  {val:>10} cm")
            else:
                print(f"{n:>5}  {'오류':>10}")
            n += 1
            time.sleep(interval)
    except KeyboardInterrupt:
        print(f"\n총 {n}회 측정 완료")
    finally:
        ser.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("com_port", help="COM 포트 (예: COM12)")
    parser.add_argument("--port", default="A", help="센서 연결 허브 포트 (A~F), 기본 A")
    parser.add_argument("--once", action="store_true", help="한 번만 측정 후 종료")
    parser.add_argument("--interval", type=float, default=0.5, help="측정 간격(초), 기본 0.5")
    args = parser.parse_args()
    run(args.com_port, args.port.upper(), args.once, args.interval)


if __name__ == "__main__":
    main()
