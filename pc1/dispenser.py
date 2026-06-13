from config import (
    FLOW_RATE,
    HUB1_MOTOR_SPEED, HUB1_OPEN_ANGLE, HUB1_CLOSE_ANGLE,
    HUB1_SPOON_DOWN_ANGLE, HUB1_SPOON_UP_ANGLE,
    HUB1_SPOON_SPIN_SPEED, HUB1_MIX_TIME_MS,
)
from pc1.hub_client import HubClient


class Dispenser:
    def __init__(self, hub: HubClient):
        self._hub = hub

    async def configure(self):
        cfg = (
            f"CONFIG:MOTOR_SPEED={HUB1_MOTOR_SPEED},"
            f"OPEN_ANGLE={HUB1_OPEN_ANGLE},"
            f"CLOSE_ANGLE={HUB1_CLOSE_ANGLE},"
            f"SPOON_DOWN_ANGLE={HUB1_SPOON_DOWN_ANGLE},"
            f"SPOON_UP_ANGLE={HUB1_SPOON_UP_ANGLE},"
            f"SPOON_SPIN_SPEED={HUB1_SPOON_SPIN_SPEED}"
        )
        await self._hub.send_and_wait(cfg, "CONFIG_OK")

    async def dispense(self, bottle: int, volume_ml: int):
        if volume_ml <= 0:
            return
        time_ms = int((volume_ml / FLOW_RATE[bottle]) * 1000)
        await self._hub.send_and_wait(f"DISPENSE:{bottle}:{time_ms}", "DISPENSE_DONE")

    async def mix(self, time_ms: int = HUB1_MIX_TIME_MS):
        await self._hub.send_and_wait(f"MIX:{time_ms}", "MIX_DONE")
