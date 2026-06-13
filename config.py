"""
Central configuration — 모든 보정값은 여기서 관리합니다.
"""

# ── BLE Hub Names ──────────────────────────────────────────────────────────
HUB_CUP_NAME    = "Cup Hub"      # 컵 레일 허브 (hub2)
HUB_BOTTLE_NAME = "Bottle Hub"   # 병 디스펜서 허브 (hub1)

# ── Drinks ─────────────────────────────────────────────────────────────────
DRINKS = {1: "탄산음료", 2: "맥주", 3: "소주"}  # key = bottle 번호 (hub2 station "1","2","3" 과 일치)
BASE_VOLUME_ML = 200

# ── Hub1 (Bottle Hub) Calibration ──────────────────────────────────────────
# 물리 배선: bottle1=Port.F, bottle2=Port.D, bottle3=Port.B
#            숟가락 상하=Port.A, 숟가락 회전=Port.E
HUB1_MOTOR_SPEED      = 500    # deg/s  — 밸브 모터 속도
HUB1_OPEN_ANGLE       =  90    # deg    — 밸브 열림 각도  CALIBRATION_NEEDED
HUB1_CLOSE_ANGLE      = -90    # deg    — 밸브 닫힘 각도  CALIBRATION_NEEDED
HUB1_SPOON_DOWN_ANGLE =  540   # deg    — 숟가락 내리기   CALIBRATION_NEEDED
HUB1_SPOON_UP_ANGLE   = -540   # deg    — 숟가락 올리기   CALIBRATION_NEEDED
HUB1_SPOON_SPIN_SPEED = 500    # deg/s  — 숟가락 회전 속도 CALIBRATION_NEEDED
HUB1_MIX_TIME_MS      = 3000   # ms     — 믹싱 지속 시간   CALIBRATION_NEEDED

# ── Hub1 Dispenser Calibration ─────────────────────────────────────────────
# FLOW_RATE : 음료별 유속 (ml/sec) — CALIBRATION_NEEDED
FLOW_RATE = {
    1: 15.0,   # 탄산음료 — CALIBRATION_NEEDED
    2: 15.0,   # 맥주     — CALIBRATION_NEEDED
    3: 15.0,   # 소주     — CALIBRATION_NEEDED
}

# ── Hub2 (Cup Hub) Calibration ─────────────────────────────────────────────
# 엔코더 기반 위치 제어 — 홈(엔드스탑) 에서 각 스테이션까지의 거리 (mm)
HUB2_SPEED = 50   # mm/s — 주행 속도

HUB2_STATION_DISTANCES = {   # mm from home endstop — CALIBRATION_NEEDED
    "1":    298,
    "2":    238,
    "3":    160,
    "mix":    71,
}

# ── Speech Recognition ─────────────────────────────────────────────────────
SPEECH_LANG     = "ko-KR"
LISTEN_TIMEOUT  = 5   # seconds
COMMAND_TIMEOUT = 6   # seconds after wake word

# ── Clap Detection ──────────────────────────────────────────────────────────
# 샘플은 -1.0 ~ 1.0 정규화 기준
CLAP_RMS_THRESHOLD  = 0.08   # 이 이상이면 트리거 (RMS)
CLAP_PEAK_THRESHOLD = 0.30   # 이 이상이면 트리거 (Peak) — 짧은 박수에 유리
CLAP_RMS_RELEASE    = 0.04   # 이 아래로 내려가야 다음 박수 카운트 가능
CLAP_PEAK_RELEASE   = 0.18
CLAP_MIN_GAP        = 0.18   # seconds — 한 박수 debounce
CLAP_MAX_GAP        = 1.8    # seconds — 두 박수 사이 최대 간격
