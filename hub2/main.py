from usys import stdin, stdout
from uselect import poll
from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor
from pybricks.parameters import Port, Direction, Color
from pybricks.robotics import DriveBase
from pybricks.tools import wait

hub = PrimeHub()
hub.light.on(Color.BLUE)
hub.speaker.volume(20)
hub.speaker.beep(frequency=440, duration=200)

left_motor  = Motor(Port.E, Direction.COUNTERCLOCKWISE)
right_motor = Motor(Port.F, Direction.CLOCKWISE)
robot       = DriveBase(left_motor, right_motor, wheel_diameter=56, axle_track=114)

# PC 시작 시 CONFIG 명령으로 덮어씌워집니다.
SPEED = 50

# 홈(엔드스탑) 기준 각 스테이션까지 거리 (mm)
STATION_DISTANCES = {
    "home": 0,
    "1":    None,
    "2":    None,
    "3":    None,
    "mix":  None,
}

_current_pos = None
_pos_mm      = 0   # 홈 기준 현재 위치 (mm)


def go_to(pos_key):
    global _current_pos, _pos_mm
    target_mm = STATION_DISTANCES.get(pos_key)
    if target_mm is None:
        stdout.write(f"UNKNOWN_STATION:{pos_key}\n")
        return
    robot.straight(target_mm - _pos_mm)
    _pos_mm      = target_mm
    _current_pos = pos_key
    stdout.write(f"ARRIVED:{pos_key}\n")


def go_home():
    go_to("home")


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
            if k == "SPEED":
                SPEED = int(v)
                robot.settings(straight_speed=SPEED, straight_acceleration=200,
                                turn_rate=90, turn_acceleration=360)
            elif k.startswith("D") and k[1:] in STATION_DISTANCES:
                STATION_DISTANCES[k[1:]] = int(v)
        stdout.write("CONFIG_OK\n")

    elif received.startswith("MOVE:"):
        pos = received.split(":")[1]
        stdout.write(f"MOVING:{pos}\n")
        go_to(pos)

    elif received == "HOME":
        stdout.write("HOMING\n")
        go_home()
        stdout.write("HOME_DONE\n")

    elif received == "SCAN" or received == "GET_DIST":
        stdout.write(f"DIST:{_pos_mm}\n")

    elif received.startswith("NUDGE:"):
        mm = int(received.split(":")[1])
        robot.straight(mm)
        _pos_mm += mm
        stdout.write(f"NUDGE_DONE:{_pos_mm}\n")

    elif received == "GET_POS":
        pos = _current_pos if _current_pos is not None else "unknown"
        stdout.write(f"POS:{pos}\n")

    elif received == "bye":
        stdout.write("CUP_HUB_DONE\n")
        break

    else:
        stdout.write("UNKNOWN_COMMAND\n")

    hub.light.on(Color.BLUE)
