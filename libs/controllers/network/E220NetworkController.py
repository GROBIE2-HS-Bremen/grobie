import asyncio
from libs.E220 import E220, MODE_CONFIG, MODE_NORMAL
from libs.controllers.network import Frame, INetworkController
from libs.controllers.network.median.NetworkHandler import Frame, NetworkHandler


class E220NetworkController(INetworkController):
    callbacks: dict[int, list] = {}
    network_handler: NetworkHandler

    def __init__(self, e220: E220,set_config=False):
        super().__init__()
        
        self.e220 = e220
        
        self.network_handler = NetworkHandler(e220=e220)
        self.register_callback(Frame.FRAME_TYPES['acknowledgement'],self.network_handler.cb_incoming_ack)
        self.register_callback(-1,self.network_handler.transmit_ack)

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

    def send_message(self, type: int, message: bytes, addr=255,ttl=20,datasize=188):
        """ send a message to the specified address splits into multiple messages if needed.
        Ebyte module sends data in one continous message if data is 199 bytes or lower.
        """
        framenr = 0
        length_msg = len(message)

        if length_msg > datasize:
            framenr = length_msg // datasize + 1
            datasplits = [message[i:i+framenr] for i in range(0, len(message), framenr)]
            
        else:
            datasplits = [message]
            
        for msg in datasplits:
            frame = Frame(type,msg,self.address,addr,ttl,framenr)
            self.network_handler.transmit_packet(frame)
            framenr -= 1

    @property
    def address(self) -> int:
        return int.from_bytes(self.e220.address, 'big')
