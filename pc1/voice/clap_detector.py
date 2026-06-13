"""
Double-clap detector — Rust jarvis 메커니즘 포팅.

핵심 동작:
  - RMS 또는 Peak 가 임계값을 초과하면 "상승 에지" 감지 (한 박수당 1회만)
  - release 구간 아래로 내려가야 다음 박수 카운트 가능
  - 두 박수가 CLAP_MAX_GAP 초 이내이면 더블 클랩으로 판정
"""

import time
import pyaudio
import numpy as np

from config import (
    CLAP_RMS_THRESHOLD, CLAP_PEAK_THRESHOLD,
    CLAP_RMS_RELEASE,   CLAP_PEAK_RELEASE,
    CLAP_MIN_GAP,       CLAP_MAX_GAP,
)

_CHUNK = 512
_RATE  = 44100


class ClapDetector:
    def __init__(self):
        self._pa = pyaudio.PyAudio()

    def wait_for_double_clap(self, timeout: float = 60.0) -> bool:
        """박수 짝짝 감지까지 블록. timeout 초 내에 없으면 False."""
        stream = self._pa.open(
            format=pyaudio.paInt16, channels=1,
            rate=_RATE, input=True,
            frames_per_buffer=_CHUNK,
        )
        try:
            is_above  = False   # 현재 소리가 임계값 위에 있는지 (상승 에지 중복 방지)
            first_t   = None    # 첫 번째 박수 시각
            last_clap = 0.0     # 마지막 카운트된 박수 시각 (debounce)
            deadline  = time.time() + timeout

            while time.time() < deadline:
                data    = stream.read(_CHUNK, exception_on_overflow=False)
                samples = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
                rms     = float(np.sqrt(np.mean(samples ** 2)))
                peak    = float(np.max(np.abs(samples)))
                now     = time.time()

                # release: 소리가 충분히 작아지면 에지 플래그 리셋
                if rms <= CLAP_RMS_RELEASE and peak <= CLAP_PEAK_RELEASE:
                    is_above = False
                    continue

                # 임계값 미달이거나 이미 에지 위에 있으면 무시
                triggered = rms >= CLAP_RMS_THRESHOLD or peak >= CLAP_PEAK_THRESHOLD
                if not triggered or is_above:
                    continue

                # 상승 에지 감지
                is_above = True

                # debounce
                if now - last_clap < CLAP_MIN_GAP:
                    continue

                last_clap = now

                if first_t is None:
                    first_t = now
                elif now - first_t <= CLAP_MAX_GAP:
                    return True          # 짝짝!
                else:
                    first_t = now        # 간격 초과 → 이 박수가 첫 번째로

            return False
        finally:
            stream.stop_stream()
            stream.close()

    def close(self):
        self._pa.terminate()
