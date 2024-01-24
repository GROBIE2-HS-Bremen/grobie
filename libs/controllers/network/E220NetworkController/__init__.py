from libs.controllers.network.E220NetworkController.E220 import E220, MODE_CONFIG, MODE_NORMAL
from libs.controllers.network.routing import RoutingController
from libs.controllers.network import Frame, INetworkController
from libs.external.ChannelLogger import logger

import libs.external.umsgpack as umsgpack
import config as cfg

import hashlib
import asyncio




class E220NetworkController(INetworkController):
    callbacks: dict[int, list] = {}
    routing_controller: RoutingController

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

                logger(f'setting {cnf_key} to {getattr(cfg, cnf_key)}')
                setattr(self.e220, cnf_key, getattr(cfg, cnf_key))

        self.e220.save()
        self.e220.set_mode(MODE_NORMAL)

    async def _start(self):
        # start separate thread
        while True:
            d = self.e220.read()
            if d:
                self.on_message(d)
            await asyncio.sleep(0.1)


    def _send_message(self, type: int, message: bytes, address: int):
        frame = Frame(type, message, self.address, address)
        dest = address

        # If the frame is a routing request, we shuold put the destionation to
        # broadcast
        if type == Frame.FRAME_TYPES['routing_request']:
            dest = 0xffff

        # If the request isnt a broadcast or a routing request, check what the
        # destionation should be
        # elif address != 0xffff and type != Frame.FRAME_TYPES['routing_response']:
        #     dest = self.routing_controller.get_route(address)

        # If destination is unkown, put it back on the queue
        if dest == -1:
            self.send_message(type, message, address)
            return

        logger(f'sending frame {frame.__dict__}', channel='send_message')
        self.e220.send(dest.to_bytes(2, 'big'),
                       self.crc.encode(frame.serialize()))
        
        print('message_send')
        # check if it needs an aknowledgement
        if  address != 0xffff and \
            type != Frame.FRAME_TYPES['routing_response'] and \
            type != Frame.FRAME_TYPES['routing_request'] and \
            type != Frame.FRAME_TYPES['acknowledgement']:

            async def readd_msg():
                await asyncio.sleep(1)
                print('not aknowledged. resending')
                self.send_message(type, message, address)     

            # create a hash for the message based on the address and the type 
            # of the message
            
            hash = hashlib.sha1(umsgpack.dumps({
                'source': frame.source_address,
                'type': frame.type,
                'destination': frame.destination_address,
                'data': frame.data
            })).digest()

            handle = asyncio.get_event_loop().create_task(readd_msg())
            self.acknowledgements[hash] = handle

    def _decode_message(self, message: bytes):
        rssi = 1

        if cfg.rssi_enabled:  # type: ignore
            rssi = - (256 - message[-1])
            message = message[:-1]

        decode = self.crc.decode(message)

        if decode is None:
            return None

        return Frame.deserialize(decode, rssi)

    @property
    def address(self) -> int:
        return int.from_bytes(self.e220.address, 'big')
