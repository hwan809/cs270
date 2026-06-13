"""
박수 임계값 측정 도구

사용법:
    python -m pc1.calibrate_clap

조용할 때와 박수칠 때의 RMS 값을 확인해서
config.py 의 CLAP_THRESHOLD 를 설정하세요.
"""

import pyaudio
import numpy as np
import time

CHUNK = 512
RATE  = 44100


def main():
    pa     = pyaudio.PyAudio()
    stream = pa.open(format=pyaudio.paInt16, channels=1,
                     rate=RATE, input=True, frames_per_buffer=CHUNK)

    print("RMS / Peak 실시간 측정 중... (Ctrl+C 로 종료)")
    print("조용히 있을 때와 박수칠 때 값을 확인하세요.\n")
    print(f"{'RMS':>8}  {'Peak':>8}  {'max_rms':>8}  {'max_peak':>8}")

    max_rms = max_peak = 0.0
    try:
        while True:
            data    = stream.read(CHUNK, exception_on_overflow=False)
            samples = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
            rms     = float(np.sqrt(np.mean(samples ** 2)))
            peak    = float(np.max(np.abs(samples)))
            max_rms  = max(max_rms, rms)
            max_peak = max(max_peak, peak)
            bar = "█" * int(peak * 40)
            print(f"\r{rms:8.3f}  {peak:8.3f}  {max_rms:8.3f}  {max_peak:8.3f}  {bar:<40}",
                  end="", flush=True)
            time.sleep(0.02)
    except KeyboardInterrupt:
        print(f"\n\n박수 최대값  →  RMS: {max_rms:.3f}  Peak: {max_peak:.3f}")
        print(f"\n권장 config.py 설정:")
        print(f"  CLAP_RMS_THRESHOLD  = {max_rms * 0.5:.2f}")
        print(f"  CLAP_PEAK_THRESHOLD = {max_peak * 0.6:.2f}")
        print(f"  CLAP_RMS_RELEASE    = {max_rms * 0.25:.2f}")
        print(f"  CLAP_PEAK_RELEASE   = {max_peak * 0.3:.2f}")
    finally:
        stream.stop_stream()
        stream.close()
        pa.terminate()


if __name__ == "__main__":
    main()
