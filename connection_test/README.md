# connection_test

PC ↔ LEGO SPIKE Hub USB 시리얼 통신 테스트

---

## 환경

- LEGO SPIKE 앱 **2.0.10**
- Python 3.x + `pyserial`

```
pip install pyserial
```

---

## 연결 순서

### 1. 허브에 코드 업로드

SPIKE 앱에서 `hub_distance_spike.py` (또는 `hub_ping_spike.py`)를 열고 허브에 업로드합니다.

### 2. SPIKE 앱 완전히 종료

⚠️ SPIKE 앱이 열려 있으면 COM 포트를 점유해서 PC에서 접근할 수 없습니다.

### 3. 허브 버튼으로 프로그램 시작

SPIKE 앱 없이 허브 중앙 버튼을 눌러 프로그램을 직접 실행합니다.

### 4. COM 포트 확인

Windows 장치 관리자 → 포트(COM & LPT) 에서 LEGO 허브의 COM 번호 확인.  
또는 아래 명령으로 자동 탐색:

```
python -c "import serial.tools.list_ports; [print(p.device, p.description) for p in serial.tools.list_ports.comports()]"
```

---

## 테스트 실행

### 연결 확인 (ping)

```
python usb_ping.py COM12
```

`ok` 응답이 연속으로 오면 통신 정상.

### 거리 센서 읽기

초음파 센서를 허브 포트 A~F 중 하나에 연결한 뒤:

```
# 연속 측정 (0.5초 간격)
python pc_distance.py COM12 --port A

# 한 번만 측정
python pc_distance.py COM12 --port A --once

# 측정 간격 변경 (0.2초)
python pc_distance.py COM12 --port A --interval 0.2
```

---

## 프로토콜

PC → Hub: JSON + `\n`  
Hub → PC: JSON + `\n`

| 명령 | 예시 |
|------|------|
| ping | `{"cmd": "ping"}` |
| 거리 측정 | `{"cmd": "get_distance", "port": "A"}` |

응답 예시:
```json
{"status": "ok", "port": "A", "distance_cm": 23.4}
{"status": "ok", "port": "A", "distance_cm": null}   ← 범위 밖
```

---

## 주의사항

- **SPIKE 앱을 닫지 않으면** `PermissionError`로 포트 열기 실패
- **허브 버튼을 누르지 않으면** 연결은 되지만 응답 없음 (timeout)
- 허브가 보내는 센서 텔레메트리(`{"m":...}`)는 PC 측 코드에서 자동으로 필터링됨
