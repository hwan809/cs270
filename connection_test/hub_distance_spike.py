# SPIKE 2.x 펌웨어용 — 초음파 거리 센서 서버
# SPIKE 앱에서 업로드 → 앱 닫기 → 허브 버튼으로 실행

import sys
import ujson
from spike import DistanceSensor

_sensors = {}

def get_sensor(port):
    if port not in _sensors:
        _sensors[port] = DistanceSensor(port)
    return _sensors[port]

sys.stdout.write(ujson.dumps({"status": "ready"}) + "\n")

while True:
    line = sys.stdin.readline()
    if not line or not line.strip():
        continue
    try:
        cmd = ujson.loads(line.strip())
        action = cmd.get("cmd", "")

        if action == "ping":
            sys.stdout.write(ujson.dumps({"status": "ok"}) + "\n")

        elif action == "get_distance":
            port = cmd.get("port", "A").upper()
            dist_cm = get_sensor(port).get_distance_cm()
            sys.stdout.write(ujson.dumps({
                "status": "ok",
                "port": port,
                "distance_cm": round(dist_cm, 1) if dist_cm is not None else None,
            }) + "\n")

        else:
            sys.stdout.write(ujson.dumps({"status": "error", "msg": "unknown cmd"}) + "\n")

    except Exception as e:
        sys.stdout.write(ujson.dumps({"status": "error", "msg": str(e)}) + "\n")
