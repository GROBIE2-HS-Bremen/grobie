import asyncio
from libs.E220 import E220, MODE_CONFIG, MODE_NORMAL
from libs.controllers.network import Frame, INetworkController


class E220NetworkController(INetworkController):
    callbacks: dict[int, list] = {}

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

    def _send_message(self, type: int, message: bytes, addr, last_hop):
        print(f'sending message of type {type} to {addr}')
        frame = Frame(type, message, self.address, addr, last_hop)
        self.e220.send(addr.to_bytes(2, 'big'), frame.serialize())

    @property
    def address(self) -> int:
        return int.from_bytes(self.e220.address, 'big')
