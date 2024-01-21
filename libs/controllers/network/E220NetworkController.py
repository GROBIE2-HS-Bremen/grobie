import asyncio
from libs.E220 import E220, MODE_CONFIG, MODE_NORMAL
from libs.controllers.config import NodeConfigData
from libs.controllers.network import Frame, INetworkController
from libs.controllers.routing import RoutingController


from libs.external.ChannelLogger import logger


class E220NetworkController(INetworkController):
    callbacks: dict[int, list] = {}
    

    def __init__(self, e220: E220, node_config: NodeConfigData = None, set_config=False):
        super().__init__()

        self.e220 = e220

        self.e220.set_mode(MODE_CONFIG)
        self.e220.get_settings()
        self.node_config = node_config
        self.routing_controller = RoutingController(node_config, self) if node_config else None
        self.q: list = []

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
        # start seperate thread
        while True:
            d = self.e220.read()
            if d:
                self.on_message(d)
            await asyncio.sleep(0.1)

    def _send_message(self, type: int, message: bytes, source: int, destination: int, addr: int):
        # Check if the message is already in the queue
        # print("checking if message is already in queue")
        # print("queue has length", len(self.q))
        # print("this method IS called")
        is_in_queue = False

        for queued_message in self.q:
            # print("hello")
            # print("queued message", queued_message)
            if queued_message[1] == message:
                # print("queued message[3]", queued_message[3])
                
                is_in_queue = True
                break

        
        # frame = Frame(type, message, self.address, addr)
        last_hop = self.address
        frame = Frame(type, message, source, destination, last_hop)
        print("frame is", frame.__dict__)
        print("addr is", addr)
        if addr == 255:
            logger(f'sending frame {frame.__dict__}', channel='send_message')
            self.q.pop() if is_in_queue else None
            # print("queue is now", self.q)
            self.e220.send((0xff00 + addr).to_bytes(2, 'big'), frame.serialize())
            return


        if self.node_config.routing_table.get(destination) == None:
            print("destination is not in routing table")
            self.routing_controller.get_route(destination)
            return
        else:
            next_hop = self.routing_controller.get_route(destination) if self.routing_controller else -1
            # if next_hop == -1:
            #     self.q.append((type, message, source, destination, addr))
            #     return
            # elif next_hop == None:
            #     return
            # else: 
            logger(f'sending frame {frame.__dict__}', channel='send_message')
                # if self.q.count((type, message, source, addr)) > 0:
                #     self.q.remove((type, message, source, addr))
            self.q.pop() if is_in_queue else None
                # print("queue is now", self.q)
                # print("next hop is", next_hop)
            self.e220.send((0xff00 + next_hop).to_bytes(2, 'big'), frame.serialize())
            return

        
        
        
        # # Get the address of the next hop
        # if addr != 255: #TODO: change this back to != 255 after testing
        #     print("addr is not 255")
        #     # print("looking up address")
        #     # TODO: fix this
        #     next_hop = self.routing_controller.get_route(addr) if self.routing_controller else -1
        #     #print("next hop is", next_hop)
        #     # addr = self.routing_controller.get_route(addr)

        #     # Node out of reach of network
        #     if next_hop == -1: # and is_in_queue == False:
        #         # print("node out of reach")
        #         # print("appending to queue")
        #         self.q.append((type, message, source, destination, addr))
        #         # print("queue is now", self.q)
        #         return
        #     elif next_hop == None:
        #         # print("next hop is none")
        #         return
        # else:
        #     next_hop = addr
        
        
        # logger(f'sending frame {frame.__dict__}', channel='send_message')
        # # if self.q.count((type, message, source, addr)) > 0:
        # #     self.q.remove((type, message, source, addr))
        # self.q.pop() if is_in_queue else None
        # print("queue is now", self.q)
        # self.e220.send((0xff00 + next_hop).to_bytes(2, 'big'), frame.serialize())
        

    @property
    def address(self) -> int:
        return int.from_bytes(self.e220.address, 'big')
