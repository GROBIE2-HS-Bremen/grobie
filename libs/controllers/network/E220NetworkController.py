import asyncio
from libs.E220 import E220, MODE_CONFIG, MODE_NORMAL
from libs.controllers.network import Frame, INetworkController
from libs.controllers.routing import RoutingController


class E220NetworkController(INetworkController):
    callbacks: dict[int, list] = {}
    routing: RoutingController

    def __init__(self, e220: E220, set_config=False):
        super().__init__()

        self.e220 = e220

        self.e220.set_mode(MODE_CONFIG)
        self.e220.get_settings()

        if set_config: 
            import config as cfg

            for cnf_key in [
                dir_val for dir_val in dir(cfg) 
                    if not callable(getattr(cfg, dir_val)) 
                    and not dir_val.startswith("__")
                ]:

                print(f'setting {cnf_key} to {getattr(cfg, cnf_key)}')
                setattr(self.e220, cnf_key, getattr(cfg, cnf_key))

        self.e220.save()
        self.e220.set_mode(MODE_NORMAL)

    async def _start(self):
        # start seperate thread
        while True:
            d = self.e220.read()
            if d:
                self.on_message(d)
            await asyncio.sleep(0.1)

    def _send_message(self, type: int, message: bytes, addr=255):
        # Get the address of the next hop
        if addr != 255:
            addr = self.routing.getRoute(addr)

        # Node out of reach of network
        if addr == -1:
            return

        frame = Frame(type, message, self.address, addr)
        print(f'sending frame {frame.__dict__}')
        self.e220.send((0xff00 + addr).to_bytes(2, 'big'), frame.serialize())

    @property
    def address(self) -> int:
        return int.from_bytes(self.e220.address, 'big')
