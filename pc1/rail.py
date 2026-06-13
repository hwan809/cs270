from config import HUB2_SPEED, HUB2_STATION_DISTANCES
from pc1.hub_client import HubClient


class Rail:
    def __init__(self, hub: HubClient):
        self._hub = hub

    async def configure(self):
        dist_pairs = ",".join(f"D{k}={v}" for k, v in HUB2_STATION_DISTANCES.items())
        await self._hub.send_and_wait(
            f"CONFIG:SPEED={HUB2_SPEED},{dist_pairs}", "CONFIG_OK"
        )

    async def home(self):
        await self._hub.send_and_wait("MOVE:home", "ARRIVED:home")

    async def move_to(self, position):
        """position: "1"~"3" (bottle), "mix", 또는 정수 bottle 번호"""
        await self._hub.send_and_wait(f"MOVE:{position}", f"ARRIVED:{position}")

    async def mix(self):
        await self.move_to("mix")
