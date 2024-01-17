import asyncio
import _thread
import time
from libs.controllers.network.error.CRC import *


class Frame:
    # max amount of frames is 0x0F(16)
    FRAME_TYPES = {
        'request_config':   0x00,
        'measurement':      0x01,
        'config':           0x02,
        'replication':      0x03,
        'node_joining':     0x06,
        'node_leaving':     0x07,
        'node_alive':       0x08,
        'sync_time':        0x0f,
    }

    def __init__(self, type: int, message: bytes, source_address: int, destination_address: int, last_hop: int, ttl=20):
        self.type = type
        self.last_hop = last_hop
        self.source_address = source_address
        self.destination_address = destination_address
        self.ttl = ttl

        self.data = message

    def serialize(self) -> bytes:
        return CRC().encode(b''.join([
            self.type.to_bytes(1, 'big'),
            self.last_hop.to_bytes(2, 'big'),
            self.source_address.to_bytes(2, 'big'),
            self.destination_address.to_bytes(2, 'big'),
            self.data
        ]))

    @staticmethod
    def deserialize(frame: bytes):
        decode_frame = CRC().decode(frame)

        if decode_frame is None:
            return None

        type = decode_frame[0]
        last_hop = int.from_bytes(decode_frame[1:3], 'big')
        source_address = int.from_bytes(decode_frame[3:5], 'big')
        destination_address = int.from_bytes(decode_frame[5:7], 'big')
        message = decode_frame[7:]

        return Frame(
            type=type, 
            message=message, 
            last_hop=last_hop,
            source_address=source_address, 
            destination_address=destination_address,
        )


class INetworkController:
    """ the abstract base class for all network controllers """

    task: asyncio.Task
    callbacks: dict[int, list]
    queue: list

    def __init__(self):
        self.callbacks = {}
        self.queue = []

    def start(self):
        """ start the network controller """
        loop = asyncio.get_event_loop()
        self.task = loop.create_task(self._start())
        # start a thread
        self.thread = _thread.start_new_thread(self._thread, ())

    def _thread(self):
        while True:
            if len(self.queue) > 0:
                type, message, addr, last_hop = self.queue.pop()
                self._send_message(type, message, addr, last_hop)
            else:
                time.sleep(0.001)
                
    def _send_message(self, type: int, message: bytes, addr: int, last_hop: int):
        """ send a message to the specified address """
        raise NotImplementedError()

    async def _start(self):
        """ the main loop of the network controller """
        raise NotImplementedError()

    def stop(self):
        """ stop the network controller """
        self.task.cancel()

    def send_message(self, type: int, message: bytes, addr=0xffff, last_hop=0x0000):
        """ send a message to the specified address """
        self.queue.append((type, message, addr, last_hop))

    def register_callback(self, addr: int, callback):
        """ register a callback for the specified address """
        if addr not in self.callbacks:
            self.callbacks[addr] = []

        self.callbacks[addr].append(callback)

    def on_message(self, message: bytes):
        """ called when a message is recieved """
        frame = Frame.deserialize(message)
        if frame is None:
            return

        # call all the callbacks
        for callback in self.callbacks.get(-1, []):
            callback(frame)

        for callback in self.callbacks.get(frame.type, []):
            callback(frame)
        

    @property
    def address(self) -> int:
        """ the address of the node """
        return int.from_bytes(b'\x00\x00', 'big')
