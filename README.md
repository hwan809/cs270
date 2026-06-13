# 소맥메이커 — LEGO SPIKE 바텐더 로봇

> 표정과 음성을 읽어 당신의 기분에 맞는 한 잔을 만들어 드립니다.

---

## 목차

1. [프로젝트 개요](#프로젝트-개요)
2. [시스템 구성도](#시스템-구성도)
3. [하드웨어 사양](#하드웨어-사양)
4. [소프트웨어 아키텍처](#소프트웨어-아키텍처)
5. [기능 명세](#기능-명세)
   - [Module 1 — 얼굴 감정 인식](#module-1--얼굴-감정-인식)
   - [Module 2 — 슬라이딩 플랫폼 제어](#module-2--슬라이딩-플랫폼-제어)
   - [Module 3 — 병뚜껑 디스펜서 제어](#module-3--병뚜껑-디스펜서-제어)
   - [Module 4 — 음료 레시피 로직](#module-4--음료-레시피-로직)
   - [Module 5 — 허브 간 통신](#module-5--허브-간-통신)
   - [Module 6 — 음성 인식 및 TTS](#module-6--음성-인식-및-tts)
6. [전체 시스템 흐름](#전체-시스템-흐름)
7. [기술 스택](#기술-스택)
8. [개발 환경 설정](#개발-환경-설정)
9. [디렉터리 구조](#디렉터리-구조)
10. [팀원 및 역할 분담](#팀원-및-역할-분담)

---

## 프로젝트 개요

**소맥메이커**는 LEGO SPIKE Prime 두 허브와 PC를 연동해 동작하는 자율 바텐더 로봇입니다.  
사용자의 얼굴 표정 혹은 음성 명령을 입력받아 페트병 3개에 담긴 음료를 적절한 비율로 혼합하여 제공합니다.

| 입력 | 처리 | 출력 |
|------|------|------|
| 웹캠 표정 / 마이크 음성 | 감정 강도 분석 → 레시피 결정 | 슬라이딩 컵 + 3단계 자동 디스펜싱 |

---

## 시스템 구성도

```
┌─────────────────────────────────────────────────┐
│                      PC                         │
│  ┌──────────┐  ┌──────────┐  ┌───────────────┐  │
│  │  Webcam  │  │   Mic /  │  │  Simple UI    │  │
│  │  (얼굴)  │  │ Speaker  │  │  (상태 표시)  │  │
│  └────┬─────┘  └────┬─────┘  └───────────────┘  │
│       │              │                           │
│  ┌────▼──────────────▼───────────────────────┐  │
│  │          중앙 제어 로직 (Python)           │  │
│  │  emotion → recipe → hub command dispatch  │  │
│  └──────────────┬─────────────────┬──────────┘  │
└─────────────────┼─────────────────┼─────────────┘
                  │ USB / BT        │ USB / BT
         ┌────────▼───────┐  ┌──────▼──────────┐
         │  SPIKE Hub 1   │  │  SPIKE Hub 2    │
         │  (디스펜서 ×3) │  │  (슬라이딩 컵) │
         └────────────────┘  └─────────────────┘
```

---

## 하드웨어 사양

### SPIKE Hub 1 — 디스펜서

| 항목 | 내용 |
|------|------|
| 연결 모터 | 3개 (각 페트병 뚜껑 1개씩) |
| 디스펜싱 원리 | 뚜껑을 회전시켜 병 하단 구멍을 개폐 → 대기압 차이로 음료 배출 |
| 음료량 제어 | 모터 개방 시간(ms) 기반 — 사전 보정(calibration) 필요 |
| 포트 할당 | Port A: 음료 1 / Port B: 음료 2 / Port C: 음료 3 |

> **디스펜서 동작 원리**  
> 페트병을 거꾸로 세워 병뚜껑 측면에 구멍을 뚫고, 모터가 뚜껑을 일정 각도 회전시키면 구멍이 정렬되어 음료가 흘러나옵니다. 모터가 원위치로 돌아오면 구멍이 막혀 대기압에 의해 배출이 멈춥니다.

### SPIKE Hub 2 — 컵 레일

| 항목 | 내용 |
|------|------|
| 구조 | 1축 선형 슬라이딩 플랫폼 |
| 동작 | 컵을 올린 캐리지가 레일을 따라 디스펜서 1→2→3 순서로 이동 |
| 위치 결정 | 모터 회전 각도(엔코더) 기반 절대 위치 제어 |
| 기준점(원점) | 컬러/터치 센서로 홈 포지션 감지 |

### PC

| 항목 | 내용 |
|------|------|
| 웹캠 | 얼굴 감정 인식 |
| 마이크 | 음성 명령 입력 |
| 스피커 | 음성 피드백(TTS) |
| UI | 현재 감정 상태, 레시피, 진행 상태 표시 |

---

## 소프트웨어 아키텍처

```
pc/
├── main.py                  # 진입점, 이벤트 루프
├── emotion/
│   ├── face_detector.py     # Module 1: 얼굴 감정 인식
│   └── emotion_mapper.py    # Module 4: 감정 강도 → 레시피 변환
├── voice/
│   ├── listener.py          # Module 6: 음성 인식(STT)
│   └── speaker.py           # Module 6: TTS 피드백
├── hub/
│   ├── hub_client.py        # Module 5: PC ↔ Hub 통신 추상화
│   ├── dispenser.py         # Module 3: Hub1 디스펜서 명령
│   └── rail.py              # Module 2: Hub2 슬라이딩 제어
└── ui/
    └── display.py           # 상태 표시 UI

spike_hub1/
└── main.py                  # Hub1 MicroPython: 디스펜서 3개 제어

spike_hub2/
└── main.py                  # Hub2 MicroPython: 슬라이딩 플랫폼 제어
```

---

## 기능 명세

### Module 1 — 얼굴 감정 인식

**목적**: 웹캠 영상에서 사용자의 감정 상태와 강도를 실시간으로 추출합니다.

**입력 / 출력**

| 항목 | 내용 |
|------|------|
| 입력 | 웹캠 영상 프레임 |
| 출력 | `{ emotion: str, intensity: float(0.0~1.0) }` |

**감정 카테고리**

| 감정 | 설명 |
|------|------|
| `happy` | 행복, 즐거움 |
| `sad` | 슬픔, 우울 |
| `angry` | 화남, 짜증 |
| `surprised` | 놀람 |
| `neutral` | 무표정 |
| `stressed` | 긴장, 피로 (복합 추론) |

**알고리즘 흐름**

```
프레임 캡처
  → 얼굴 영역 검출 (MediaPipe Face Detection)
  → 표정 분류 (DeepFace / FER 모델)
  → softmax 확률 중 최댓값 → emotion + intensity
  → 3~5프레임 이동 평균 → 안정화
```

**구현 참고**
- 라이브러리: `deepface`, `mediapipe`, `opencv-python`
- 모델: FER-2013 기반 CNN (또는 DeepFace `Emotion` 백엔드)
- 프레임레이트 목표: ≥ 10 FPS

---

### Module 2 — 슬라이딩 플랫폼 제어

**목적**: 컵을 실은 캐리지를 디스펜서 위치에 정확히 위치시킵니다.

**입력 / 출력**

| 항목 | 내용 |
|------|------|
| 입력 | 목표 디스펜서 번호 (1, 2, 3) |
| 출력 | 모터 회전 명령 (Hub2) |

**위치 정의**

| 디스펜서 | 레일 상 위치 (엔코더 °) |
|----------|------------------------|
| 1 (음료 A) | 0° (홈) |
| 2 (음료 B) | TBD |
| 3 (음료 C) | TBD |

> 실제 값은 기계 조립 후 보정 단계에서 측정하여 상수로 정의합니다.

**알고리즘 흐름**

```
홈 복귀 (원점 센서 감지까지 저속 이동)
  → 목표 위치 엔코더 각도 계산
  → PID 또는 직접 속도 제어로 이동
  → 위치 도달 확인 → PC에 완료 신호 전송
```

**오류 처리**
- 타임아웃(5초) 내 위치 미달 → 재시도 1회 → 오류 보고
- 센서 미감지 시 소프트 스톱 후 오류 보고

---

### Module 3 — 병뚜껑 디스펜서 제어

**목적**: 지정된 음료를 지정된 양만큼 정확히 배출합니다.

**입력 / 출력**

| 항목 | 내용 |
|------|------|
| 입력 | `{ bottle: int(1~3), volume_ml: float }` |
| 출력 | 모터 개방/폐쇄 명령 (Hub1) |

**동작 시퀀스**

```
1. 해당 포트 모터 → 개방 각도(θ_open)로 회전
2. open_time_ms 동안 대기  ← 음료 배출
3. 모터 → 폐쇄 각도(θ_close)로 복귀
4. 완료 신호 전송
```

**배출량 보정 (Calibration)**

배출량은 음료 점도, 병 내 잔량(수두압)에 따라 달라지므로 보정 테이블을 사용합니다.

```
volume_ml → open_time_ms  (선형 근사, 음료별 별도 테이블)
```

| 파라미터 | 설명 |
|----------|------|
| `θ_open` | 구멍이 완전히 열리는 뚜껑 회전 각도 |
| `θ_close` | 구멍이 완전히 막히는 원위치 각도 |
| `K_flow` | ml/ms 유속 상수 (보정값) |

> **보정 절차**: 빈 컵에 50ml 단위로 측정하며 `open_time_ms`를 기록, 선형 회귀로 `K_flow` 산출.

---

### Module 4 — 음료 레시피 로직

**목적**: 감정 또는 음성 입력을 음료 레시피(음료 종류 + 각 용량)로 변환합니다.

**감정 강도 기반 매핑 (기본 모드)**

감정 강도 `intensity ∈ [0.0, 1.0]`를 각 음료의 비율에 선형 매핑합니다.

```python
# 예시 — 구체적 수치는 팀 논의 후 확정
def map_emotion_to_recipe(emotion: str, intensity: float) -> dict:
    base_volume = 200  # ml (총 음료량)
    
    ratios = EMOTION_RATIO_TABLE[emotion]  # [r1, r2, r3], sum = 1.0
    # intensity가 높을수록 강한 음료 비율 증가
    adjusted = apply_intensity(ratios, intensity)
    
    return {
        "bottle_1": round(base_volume * adjusted[0]),
        "bottle_2": round(base_volume * adjusted[1]),
        "bottle_3": round(base_volume * adjusted[2]),
    }
```

**감정별 기본 비율 테이블 (초안)**

| 감정 | 음료 A (약함) | 음료 B (중간) | 음료 C (강함) | 비고 |
|------|--------------|--------------|--------------|------|
| `happy` | 0.6 | 0.3 | 0.1 | 달콤하고 가벼운 조합 |
| `sad` | 0.2 | 0.5 | 0.3 | 위로가 되는 묵직한 조합 |
| `angry` | 0.5 | 0.3 | 0.2 | 진정 효과 고려 |
| `stressed` | 0.3 | 0.4 | 0.3 | 긴장 이완 중심 |
| `surprised` | 0.4 | 0.4 | 0.2 | 밸런스 |
| `neutral` | 0.33 | 0.34 | 0.33 | 균등 배분 |

> 비율 수치는 팀 내 테스트 및 취향 조정 후 최종 확정.

**음성 명령 오버라이드 모드**

사용자가 음성으로 직접 요청 시 감정 분석보다 우선합니다.

| 음성 키워드 예시 | 동작 |
|----------------|------|
| "약하게", "light" | intensity 강제 0.2 적용 |
| "강하게", "strong" | intensity 강제 0.9 적용 |
| "[음료명]" | 해당 음료 단독 배출 |
| "추천해줘", "recommend" | 현재 감정 기반 레시피 사용 |

---

### Module 5 — 허브 간 통신

**목적**: PC가 Hub1 / Hub2에 명령을 전송하고 완료 신호를 수신합니다.

**통신 토폴로지**

```
PC ←→ Hub1 (USB 또는 Bluetooth)
PC ←→ Hub2 (USB 또는 Bluetooth)
```

> Hub1 ↔ Hub2 직접 통신 없음. PC가 모든 명령을 중재합니다.

**프로토콜 (PC → Hub)**

JSON 문자열을 시리얼(UART) 또는 BT RFCOMM으로 전송합니다.

```json
// 디스펜서 명령 (Hub1)
{ "cmd": "dispense", "bottle": 2, "time_ms": 1500 }

// 이동 명령 (Hub2)
{ "cmd": "move", "position": 1 }

// 홈 복귀 (Hub2)
{ "cmd": "home" }
```

**Hub → PC 응답**

```json
{ "status": "ok" }
{ "status": "error", "msg": "timeout" }
```

**연결 우선순위**: USB 유선 연결 우선, 불가 시 Bluetooth 페어링.

---

### Module 6 — 음성 인식 및 TTS

**목적**: 한국어/영어 혼용 음성 명령을 인식하고, 음성으로 피드백을 제공합니다.

**STT (Speech-to-Text)**

| 항목 | 내용 |
|------|------|
| 엔진 | Google Speech Recognition API (또는 Whisper 로컬 모델) |
| 언어 | `ko-KR` + `en-US` 병렬 인식 |
| 트리거 | 웨이크워드 `"소맥"` / `"Hey Maker"` 또는 버튼 |
| 타임아웃 | 무음 2초 → 인식 종료 |

**인식 키워드 목록**

| 카테고리 | 키워드 (예시) |
|----------|--------------|
| 강도 | 약하게, 보통으로, 강하게, light, medium, strong |
| 추천 | 추천해줘, 알아서 만들어, recommend, surprise me |
| 음료 지정 | [음료A 이름], [음료B 이름], [음료C 이름] |
| 취소 | 그만, 취소, cancel, stop |

**TTS (Text-to-Speech)**

| 상황 | 출력 예시 |
|------|----------|
| 감정 인식 완료 | "슬픔이 느껴지시나요? 위로의 한 잔을 준비할게요." |
| 제조 시작 | "음료를 만들고 있습니다. 잠시만 기다려 주세요." |
| 완료 | "완성됐습니다! 맛있게 드세요." |
| 오류 | "죄송합니다, 다시 시도해 주세요." |

- 라이브러리: `pyttsx3` (오프라인) 또는 Google TTS API

---

## 전체 시스템 흐름

```
[시작]
   │
   ├─ 음성 트리거? ──────────────────────────────┐
   │        No                                   │ Yes
   │                                             ▼
   ▼                                      STT 음성 인식
웹캠 표정 분석                                   │
   │                                             │
   ▼                                             │
감정 + 강도 추출                                  │
   │                                             │
   └──────────────────┬──────────────────────────┘
                      ▼
               레시피 결정 (Module 4)
               { bottle_1: Xml, bottle_2: Yml, bottle_3: Zml }
                      │
                      ▼
               UI + TTS 안내 출력
                      │
                      ▼
               [Hub2] 홈 포지션 복귀
                      │
               ┌──────▼──────────────────────────┐
               │   for each bottle (1→2→3):       │
               │   [Hub2] 해당 위치로 이동         │
               │   [Hub1] 해당 디스펜서 개방        │
               │   open_time_ms 대기               │
               │   [Hub1] 디스펜서 닫기             │
               └──────────────────────────────────┘
                      │
               [Hub2] 홈 포지션 복귀
                      │
               TTS "완성됐습니다!"
                      │
                    [끝]
```

---

## 기술 스택

| 레이어 | 기술 |
|--------|------|
| 허브 제어 | LEGO SPIKE Prime MicroPython |
| PC 메인 로직 | Python 3.11+ |
| 얼굴 감정 인식 | OpenCV, MediaPipe, DeepFace (FER) |
| 음성 인식 | SpeechRecognition + Google STT / OpenAI Whisper |
| TTS | pyttsx3 / Google TTS |
| Hub 통신 | pyserial (USB) / pybluez (BT) |
| UI | tkinter 또는 pygame (간단한 상태 표시) |

---

## 개발 환경 설정

### 요구 사항

- Python 3.11+
- LEGO SPIKE App (허브 펌웨어 업데이트용)
- 웹캠, 마이크, 스피커

### 설치

```bash
git clone https://github.com/<your-org>/somaek-maker.git
cd somaek-maker

pip install -r requirements.txt
```

`requirements.txt` (예시):

```
opencv-python
mediapipe
deepface
SpeechRecognition
pyttsx3
pyserial
pyaudio
```

### 실행

```bash
# Hub 포트 설정 (예시)
export HUB1_PORT=/dev/ttyACM0
export HUB2_PORT=/dev/ttyACM1

python pc/main.py
```

### 보정 (Calibration)

```bash
# 디스펜서 유속 보정
python pc/hub/calibrate_dispenser.py --bottle 1

# 슬라이딩 플랫폼 위치 보정
python pc/hub/calibrate_rail.py
```

---

## 디렉터리 구조

```
somaek-maker/
├── README.md
├── requirements.txt
├── pc/
│   ├── main.py
│   ├── emotion/
│   │   ├── face_detector.py
│   │   └── emotion_mapper.py
│   ├── voice/
│   │   ├── listener.py
│   │   └── speaker.py
│   ├── hub/
│   │   ├── hub_client.py
│   │   ├── dispenser.py
│   │   ├── rail.py
│   │   ├── calibrate_dispenser.py
│   │   └── calibrate_rail.py
│   └── ui/
│       └── display.py
├── spike_hub1/
│   └── main.py
├── spike_hub2/
│   └── main.py
└── docs/
    ├── hardware_assembly.md
    └── calibration_guide.md
```

---

## 팀원 및 역할 분담

| 모듈 | 담당 | 상태 |
|------|------|------|
| Module 1 — 얼굴 감정 인식 | TBD | 🔲 미시작 |
| Module 2 — 슬라이딩 플랫폼 | TBD | 🔲 미시작 |
| Module 3 — 디스펜서 제어 | TBD | 🔲 미시작 |
| Module 4 — 레시피 로직 | TBD | 🔲 미시작 |
| Module 5 — 허브 통신 | TBD | 🔲 미시작 |
| Module 6 — 음성 인식/TTS | TBD | 🔲 미시작 |

---

*KAIST CS270 — Spring 2026*
