

import asyncio
from libs.E220 import E220, MODE_CONFIG, MODE_NORMAL
from libs.controllers.network import Frame, INetworkController



class E220NetworkController(INetworkController): 
    
    callbacks: dict[int, list] = {}

    def __init__(self, e220: E220): 
        super().__init__()

        self.e220 = e220

        self.e220.set_mode(MODE_CONFIG)
        self.e220.get_settings()
        self.e220.set_mode(MODE_NORMAL)

    async def _start(self):
        while True:
            d = self.e220.read()
            if d:
                self.on_message(d)
            await asyncio.sleep(0.1)

    def send_message(self, type: int, message: bytes, addr=255):
        frame = Frame(type, message, self.address, addr)
        print(f'sending frame {frame.__dict__}')
        self.e220.send(addr.to_bytes(2, 'big'), frame.serialize())

    @property
    def address(self) -> int:
        return int.from_bytes(self.e220.address, 'big')