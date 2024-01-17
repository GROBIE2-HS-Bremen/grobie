import asyncio
import _thread
import time
import config as cfg

from libs.controllers.network.frame import FrameStructure
from libs.controllers.network.error.CRC import CRC


class Frame:
    FRAME_TYPES = {
        'discovery': 0x00,
        'measurment': 0x01,
        'config': 0x02,
        'replication': 0x03,
        'node_joining': 0x06,
        'node_leaving': 0x07,
        'node_alive': 0x08,
        'sync_time': 0x0f,
    }

    def __init__(self, type: int, message: bytes, source_address: int, destination_address: int, ttl=20, rssi=-1):
        self.type = type
        self.source_address = source_address
        self.destination_address = destination_address
        self.ttl = ttl
        self.rssi = rssi

        self.data = message

    def serialize(self) -> bytes:
        frame = b''.join([
            self.type.to_bytes(FrameStructure.type_length, 'big'),
            self.source_address.to_bytes(FrameStructure.source_address_length, 'big'),
            self.destination_address.to_bytes(FrameStructure.destination_address_length, 'big'),
            self.ttl.to_bytes(FrameStructure.ttl_length, 'big'),
            # self.frame_num.to_bytes(FrameStructure.frame_num_length, 'big'),
            # self.ses_num.to_bytes(FrameStructure.ses_num_length, 'big'),
            self.data
        ])

        return CRC().encode(frame)

    @staticmethod
    def deserialize(frame: bytes):
        print('received frame: ', frame)

        decode_frame = CRC().decode(frame)

        if decode_frame is None:
            return None

        type = decode_frame[FrameStructure.type_index]
        source_address = decode_frame[FrameStructure.source_address_start_index:FrameStructure.source_address_end_index]
        destination_address = decode_frame[FrameStructure.destination_address_start_index:FrameStructure.destination_address_end_index]
        ttl = decode_frame[FrameStructure.ttl_start_index:FrameStructure.ttl_end_index]
        frame_num = decode_frame[FrameStructure.frame_num_start_index:FrameStructure.frame_num_end_index]
        ses_num = decode_frame[FrameStructure.ses_num_start_index:FrameStructure.ses_num_end_index]
        message = decode_frame[FrameStructure.data_start_index:]
        rssi = -1

        if cfg.rssi_enabled:  # type: ignore
            rssi = message[-1]
            message = message[:-1]

        return Frame(
            type,
            message,
            int.from_bytes(source_address, 'big'),
            int.from_bytes(destination_address, 'big'),
            int.from_bytes(ttl),
            int.from_bytes(frame_num),
            int.from_bytes(ses_num),
            rssi
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

    def _send_message(self, type: int, message: bytes, addr=255):
        """ send a message to the specified address """
        raise NotImplementedError()

    async def _start(self):
        """ the main loop of the network controller """
        raise NotImplementedError()

    def stop(self):
        """ stop the network controller """
        self.task.cancel()

    def send_message(self, type: int, message: bytes, addr=255):
        """ send a message to the specified address """
        self.q.append((type, message, addr))

    def register_callback(self, addr: int, callback):
        """ register a callback for the specified address """
        if addr not in self.callbacks:
            self.callbacks[addr] = []

        self.callbacks[addr].append(callback)

    def on_message(self, message: bytes):
        """ called when a message is received """
        frame = Frame.deserialize(message)

        # get the callbacks for the wildcard
        for callback in self.callbacks.get(-1, []):
            callback(frame)

        # get the callbacks for the specific type
        for callback in self.callbacks.get(frame.type, []):
            callback(frame)

    @property
    def address(self) -> int:
        """ the address of the node """
        return int.from_bytes(b'\x00\x00', 'big')
