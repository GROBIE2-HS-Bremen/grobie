import asyncio
import _thread
import time
import config as cfg

from libs.controllers.network.error.CRC import CRC


class Frame:
    FRAME_TYPES = {
        'discovery':    0x00,
        'measurment':   0x01,
        'config':       0x02,
        'replication':  0x03,
        'node_joining': 0x06,
        'node_leaving': 0x07,
        'node_alive':   0x08,
        'sync_time':    0x0f,
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
            self.type.to_bytes(1, 'big'),
            self.source_address.to_bytes(2, 'big'),
            self.destination_address.to_bytes(2, 'big'),
            self.data
        ])

        return CRC().encode(frame)

    @staticmethod
    def deserialize(frame: bytes):
        if cfg.rssi_enabled:
            rssi = frame[-1]
            frame = frame[:-1]
        else:
            rssi = -1

        decode_frame = CRC().decode(frame)

        if decode_frame in None:
            return None

        type = decode_frame[0]
        source_address = int.from_bytes(decode_frame[1:3], 'big')
        destination_address = int.from_bytes(decode_frame[3:5], 'big')
        message = decode_frame[5:]

        return Frame(type, message, source_address, destination_address, rssi=rssi)


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
        """ called when a message is recieved """
        frame = Frame.deserialize(message)

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
