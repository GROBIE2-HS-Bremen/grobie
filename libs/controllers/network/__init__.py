import asyncio
from libs.E220 import E220
import _thread
import time
import math

import config as cfg


class Frame: 
    FRAME_TYPES = {
        'discovery':    0x00,
        'measurment':   0x01,
        'config':       0x02,
        'replication':  0x03,
        'acknowledgement':0x04,
        'node_joining': 0x06,
        'node_leaving': 0x07,
        'node_alive':   0x08,
        'sync_time':    0x0f,
    }

    def __init__(self, type: int, message: bytes, source_address: int,destination_address: int, ttl=20,frame_num=0,ses_num=0,rssi=1):
        self.type = type
        self.source_address = source_address
        self.destination_address = destination_address
        self.ttl = ttl
        self.frame_num = frame_num
        self.ses_num = ses_num        
        self.rssi = rssi
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
        ttl = int.from_bytes(frame[5:8],'big')
        frame_num = int.from_bytes(frame[8:9],'big')
        ses_num = int.from_bytes(frame[9:11],'big')
        data = frame[11:]
        rssi = -1

        if cfg.rssi_enabled:  # type: ignore
            rssi = - (256 - data[-1])
            data = data[:-1]
        

        return Frame(
            type=type,
            message=data,
            source_address=source_address,
            destination_address=destination_address,
            ttl=ttl,
            frame_num=frame_num,
            ses_num=ses_num,
            rssi=rssi
            )


    
class INetworkController: 
    """ the abstract base class for all network controllers """

    task: asyncio.Task
    callbacks: dict[int, list]
    q: list

    def __init__(self):
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

    def _send_message(self, type: int, message: bytes, addr):
        """ send a message to the specified address """
        raise NotImplementedError()

    async def _start(self):
        raise NotImplementedError()

    def stop(self):
        """ stop the network controller """
        self.task.cancel()

    def send_message(self, type: int, message: bytes, addr=0xffff):
        """ send a message to the specified address """
        self.q.append((type, message, addr))


    def register_callback(self, type: int, callback):
        """ register a callback for the specified address """
        if type not in self.callbacks:
            self.callbacks[type] = []

        self.callbacks[type].append(callback)

    def handle_packet(self,frame):
        raise NotImplementedError()
    
    def on_message(self, message: bytes):
        """ called when a message is recieved """
        
        frame = Frame.deserialize(message)
        frame = self.handle_packet(frame)
        
        #print(frame)
        # No frame to give back to callbacks
        if frame is None: 
            return
     
        
        
        for cb in self.callbacks.get(-1, []):
            #print(cb)
            cb(frame)
        
        for cb in self.callbacks.get(frame.type, []):
            #print(cb)
            cb(frame)
        

        # print(callbacks)        
        # call all the callbacks
        #for callback in self.callbacks:
        #     callback(frame)


    @property
    def address(self) -> int:
        """ the address of the node """
        return int.from_bytes(b'\x00\x00', 'big')
    

