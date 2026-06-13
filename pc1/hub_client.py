"""
Async BLE client for a single Pybricks hub.
"""

import asyncio
from bleak import BleakScanner, BleakClient

PYBRICKS_CHAR_UUID = "c5f50002-8280-46da-89f4-6d8051e4aeef"

class HubClient:
    def __init__(self, name: str):
        self.name = name
        self.client = None
        self.ready_event    = asyncio.Event()
        self.response_event = asyncio.Event()
        self._rx_buffer     = bytearray()
        self.latest_response = ""
        self._target_message = None

    async def connect(self) -> bool:
        print(f"[{self.name}] BLE 스캔 중...")
        device = await BleakScanner.find_device_by_name(self.name)
        if device is None:
            print(f"[{self.name}] 허브를 찾지 못했습니다. BLE 이름을 확인하세요.")
            return False

        self.client = BleakClient(
            device,
            disconnected_callback=lambda _: print(f"\n[{self.name}] 연결 끊김."),
        )
        await self.client.connect()
        await self.client.start_notify(PYBRICKS_CHAR_UUID, self._on_rx)
        print(f"[{self.name}] 연결 완료.")
        return True

    def _on_rx(self, _, data: bytearray):
        if data[0] != 0x01:
            return
        self._rx_buffer.extend(data[1:])
        while b"\n" in self._rx_buffer:
            line, _, self._rx_buffer[:] = self._rx_buffer.partition(b"\n")
            msg = line.decode().strip()
            if not msg:
                continue
            if msg == "READY":
                self.ready_event.set()
            else:
                self.latest_response = msg
                print(f"[{self.name}] {msg}")
                if self._target_message and self._target_message in msg:
                    self._target_message = None
                    self.response_event.set()

    async def send(self, command: str):
        """허브가 READY 신호를 보낼 때까지 기다린 뒤 명령을 전송합니다."""
        await self.ready_event.wait()
        self.ready_event.clear()
        payload = (command + "\n").encode()
        await self.client.write_gatt_char(
            PYBRICKS_CHAR_UUID,
            b"\x06" + payload,
            response=True,
        )

    async def send_and_wait(self, command: str, target: str):
        """응답 대기를 send 전에 등록해 race condition 없이 응답을 기다립니다."""
        self._target_message = target
        self.response_event.clear()
        await self.send(command)
        await self.response_event.wait()

    async def wait_for(self, target: str):
        """허브가 target 문자열을 포함한 메시지를 보낼 때까지 대기합니다."""
        self._target_message = target
        self.response_event.clear()
        await self.response_event.wait()

    async def disconnect(self):
        if self.client and self.client.is_connected:
            await self.client.disconnect()
