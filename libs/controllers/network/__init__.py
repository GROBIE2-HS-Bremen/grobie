import asyncio
from libs.E220 import E220
from libs.controllers.network.median.NetworkHandler import NetworkHandler
import _thread
import time
import math



class Frame: 
    FRAME_TYPES = {
        'discovery': 0x00,
        'measurment': 0x01,
        'config': 0x02,
        'replication': 0x03,
        'acknowledgement':0x04,
        'node_joining': 0x06,
        'node_leaving': 0x07,
        'node_alive': 0x08,
    }

    def __init__(self, type: int, message: bytes, source_address: int, destination_address: int, ttl=20,frame_num=1,ses_num=1):
        self.type = type
        self.source_address = source_address
        self.destination_address = destination_address
        self.ttl = ttl
        self.frame_num = frame_num
        self.ses_num = ses_num
        self.data = message
  

    def serialize(self) -> bytes:
        
        return b''.join([
            self.type.to_bytes(1, 'big'), 
            self.source_address.to_bytes(2, 'big'),
            self.destination_address.to_bytes(2, 'big'),
            self.ttl.to_bytes(3, 'big'),
            self.frame_num.to_bytes(1,'big'),
            self.ses_num.to_bytes(2,'big'),
            self.data,
            #self.crc.to_bytes(2, 'big'),
            ])
        
        
    @staticmethod
    def deserialize(frame: bytes):
        type = frame[0]
        source_address = int.from_bytes(frame[1:3], 'big')
        destination_address = int.from_bytes(frame[3:5], 'big')
        message = frame[5:]

        return Frame(type, message, source_address, destination_address)


    
class INetworkController: 
    """ the abstract base class for all network controllers """

    task: asyncio.Task
    callbacks: dict[int, list]
    q: list
    network = NetworkHandler

    def __init__(self,network):
        self.network = network
        self.callbacks = {}
        self.q = []

    def start(self):
        """ start the network controller """
        loop = asyncio.get_event_loop()
        self.task = loop.create_task(self._start())
        # start a thread
        self.thread = _thread.start_new_thread(self._thread, ())

    def _thread(self):
        while True:
            if len(self.q) > 0:
                type, message, addr = self.q.pop()
                self._send_message(type, message, addr)
            else:
                time.sleep(0.001)
                
    def _send_message(self, type: int, message: bytes, addr=255):
        """ send a message to the specified address """
        raise NotImplementedError()

    async def _start(self):
        raise NotImplementedError()

    def stop(self):
        """ stop the network controller """
        self.task.cancel()

    def send_message(self, type: int, message: bytes, addr=255):
        """ send a message to the specified address """
        self.q.append((type, message, addr))


    def register_callback(self, type: int, callback):
        """ register a callback for the specified address """
        if type not in self.callbacks:
            self.callbacks[type] = []

        self.callbacks[type].append(callback)

    

    def on_message(self, message: bytes):
        """ called when a message is recieved """
        
        frame = Frame.deserialize(message)
        result = self.network.handle_packet(frame)

        if result is None:
            self.network.transmit_ack(frame)
            return
        
        frame = result
            
        

        # get all the callback functions
        # get the callbacks for the wildcard
        callbacks = self.callbacks.get(-1, [])
        # get the callbacks for the specific type
        callbacks += self.callbacks.get(frame.type, [])

        
        # call all the callbacks
        for callback in callbacks:
            callback(frame)


    @property
    def address(self) -> int:
        """ the address of the node """
        return int.from_bytes(b'\x00\x00', 'big')
    

