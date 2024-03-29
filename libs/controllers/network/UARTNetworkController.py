from libs.controllers.network import INetworkController
from machine import UART

import asyncio


class UARTNetworkController(INetworkController):

    def __init__(self, uart: UART):
        super().__init__()
        self.uart = uart
        self.callbacks = {}

    async def _start(self):
        while True:
            if self.uart.any():
                self.on_message(self.uart.read())
            await asyncio.sleep(0.1)

    def _send_message(self, type: int, message: bytes, addr):
        self.uart.write(message)
