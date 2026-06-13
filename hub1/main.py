from usys import stdin, stdout
from uselect import poll
from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor
from pybricks.parameters import Port, Stop, Color
from pybricks.tools import wait

hub = PrimeHub()
hub.light.on(Color.ORANGE)
hub.speaker.volume(20)
hub.speaker.beep(frequency=440, duration=200)

# 물리 배선: bottle1=Port.F, bottle2=Port.D, bottle3=Port.B
#            숟가락 상하=Port.A, 숟가락 회전=Port.E
_dispensers = {
    "1": Motor(Port.F),
    "2": Motor(Port.D),
    "3": Motor(Port.B),
}
_spoon_lift = Motor(Port.A)
_spoon_spin = Motor(Port.E)

# ── 아래 초기값은 직접 수정하지 마세요 ──────────────────────────────────────
# PC 시작 시 config.py 값이 CONFIG 명령으로 전달되어 덮어씌워집니다.
MOTOR_SPEED      = 500
OPEN_ANGLE       =  90
CLOSE_ANGLE      = -90
SPOON_DOWN_ANGLE =  90
SPOON_UP_ANGLE   = -90
SPOON_SPIN_SPEED = 500

keyboard = poll()
keyboard.register(stdin)

while True:
    stdout.write("READY\n")

    while not keyboard.poll(0):
        wait(10)

    received = stdin.readline().strip()
    hub.light.on(Color.RED)

    if received.startswith("CONFIG:"):
        for pair in received[7:].split(","):
            k, v = pair.split("=", 1)
            if   k == "MOTOR_SPEED":      MOTOR_SPEED      = int(v)
            elif k == "OPEN_ANGLE":       OPEN_ANGLE       = int(v)
            elif k == "CLOSE_ANGLE":      CLOSE_ANGLE      = int(v)
            elif k == "SPOON_DOWN_ANGLE": SPOON_DOWN_ANGLE = int(v)
            elif k == "SPOON_UP_ANGLE":   SPOON_UP_ANGLE   = int(v)
            elif k == "SPOON_SPIN_SPEED": SPOON_SPIN_SPEED = int(v)
        stdout.write("CONFIG_OK\n")

    elif received.startswith("DISPENSE:"):
        parts   = received.split(":")
        bottle  = parts[1]
        time_ms = int(float(parts[2]))
        motor   = _dispensers.get(bottle)
        if motor:
            stdout.write(f"DISPENSING:{bottle}:{time_ms}\n")
            motor.run_angle(MOTOR_SPEED, OPEN_ANGLE,  then=Stop.HOLD, wait=True)
            wait(time_ms)
            motor.run_angle(MOTOR_SPEED, CLOSE_ANGLE, then=Stop.HOLD, wait=True)
            stdout.write("DISPENSE_DONE\n")
        else:
            stdout.write("UNKNOWN_BOTTLE\n")

    elif received.startswith("VALVE_OPEN:"):
        bottle = received.split(":")[1]
        motor  = _dispensers.get(bottle)
        if motor:
            motor.run_angle(MOTOR_SPEED, OPEN_ANGLE, then=Stop.HOLD, wait=True)
            stdout.write(f"VALVE_OPENED:{bottle}\n")
        else:
            stdout.write("UNKNOWN_BOTTLE\n")

    elif received.startswith("VALVE_CLOSE:"):
        bottle = received.split(":")[1]
        motor  = _dispensers.get(bottle)
        if motor:
            motor.run_angle(MOTOR_SPEED, CLOSE_ANGLE, then=Stop.HOLD, wait=True)
            stdout.write(f"VALVE_CLOSED:{bottle}\n")
        else:
            stdout.write("UNKNOWN_BOTTLE\n")

    elif received.startswith("MIX:"):
        time_ms = int(float(received.split(":")[1]))
        stdout.write(f"MIXING:{time_ms}\n")
        _spoon_lift.run_angle(MOTOR_SPEED, SPOON_DOWN_ANGLE, then=Stop.HOLD, wait=True)
        _spoon_spin.run_time(SPOON_SPIN_SPEED, time_ms, then=Stop.COAST, wait=True)
        _spoon_lift.run_angle(MOTOR_SPEED, SPOON_UP_ANGLE,   then=Stop.HOLD, wait=True)
        stdout.write("MIX_DONE\n")

    elif received == "bye":
        stdout.write("BOTTLE_HUB_DONE\n")
        break

    else:
        stdout.write("UNKNOWN_COMMAND\n")

    hub.light.on(Color.ORANGE)
