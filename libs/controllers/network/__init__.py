import _thread
import asyncio
import time

from libs.external.ChannelLogger import logger
from libs.controllers.network.error.CRC import CRC

import hashlib
import libs.external.umsgpack as umsgpack

class Frame:
    FRAME_TYPES = {
        'discovery':        0x00,
        'measurement':      0x01,
        'config':           0x02,
        'replication':      0x03,
        'acknowledgement':  0x04,
        'node_joining':     0x06,
        'node_leaving':     0x07,
        'node_alive':       0x08,
        'routing_request':  0x0d,
        'routing_response': 0x0e,
        'sync_time':        0x0f,
    }

    def __init__(self, type: int, message: bytes, source_address: int, destination_address: int, ttl=20, rssi=1):
        self.type = type
        self.source_address = source_address
        self.destination_address = destination_address
        self.ttl = ttl
        self.rssi = rssi

        self.data = message

    def serialize(self) -> bytes:
        return b''.join([
            self.type.to_bytes(1, 'big'),
            self.source_address.to_bytes(2, 'big'),
            self.destination_address.to_bytes(2, 'big'),
            self.data
        ])

    @staticmethod
    def deserialize(frame: bytes, rssi: int = 1):
        type = frame[0]
        source_address = int.from_bytes(frame[1:3], 'big')
        destination_address = int.from_bytes(frame[3:5], 'big')
        message = frame[5:]

        return Frame(type, message, source_address, destination_address, rssi=rssi)


class INetworkController:
    """ the abstract base class for all network controllers """

    task: asyncio.Task
    callbacks: dict[int, list]
    queue: list = []
    crc: CRC

    def __init__(self):
        self.callbacks = {}
        self.queue = []
        self.crc = CRC()

    def start(self):
        """ start the network controller """
        loop = asyncio.get_event_loop()
        self.task = loop.create_task(self._start())
        # start a thread
        self.thread = _thread.start_new_thread(self._thread, ())

    killed = False

    def _thread(self):
        while True and not self.killed:
            if len(self.queue) > 0:
                type, message, addr = self.queue.pop(0)
                self._send_message(type, message, addr)
            else:
                time.sleep(0.001)

    def _send_message(self, type: int, message: bytes, addr):
        """ send a message to the specified address """
        raise NotImplementedError()

    def _decode_message(self, message: bytes):
        return Frame.deserialize(message)

    async def _start(self):
        """ the main loop of the network controller """
        raise NotImplementedError()

    def stop(self):
        """ stop the network controller """
        self.task.cancel()
        self.killed = True

    def send_message(self, type: int, message: bytes, addr=0xffff):
        """ send a message to the specified address """
        self.queue.append((type, message, addr))

    def register_callback(self, addr: int, callback):
        """ register a callback for the specified address """
        if addr not in self.callbacks:
            self.callbacks[addr] = []

        self.callbacks[addr].append(callback)

    def register_callbacks(self, callbacks: dict[int, list]):
        """ register multiple callbacks """
        for frame_type in callbacks.keys():
            for callback in callbacks[frame_type]:
                self.register_callback(frame_type, callback)

    acknowledgements = {}
    def on_message(self, message: bytes):
        """ called when a message is received """
        frame = self._decode_message(message)

        if frame is None:
            logger(f"Failed to decode message [{message}]", channel='error')
            return None

        if frame.type not in [Frame.FRAME_TYPES['routing_request'], Frame.FRAME_TYPES['routing_response']] and frame.destination_address != self.address and frame.destination_address != 0xffff:
            logger(
                f'Got data for a different node, ignoring and pushing on queue', channel='routing')
            self.send_message(frame.type, frame.data, frame.destination_address)
            return
        
        if frame.type == Frame.FRAME_TYPES['acknowledgement'] and frame.destination_address == self.address:
            logger(f'aknowledgement received for {frame.data}', channel='aknowledge')
            hash = b"" + frame.data
            if hash in self.acknowledgements:
                self.acknowledgements[hash].cancel()
                del self.acknowledgements[hash]
            return
            
        # check if we shoudl aknowledge the message. not broadcast, not routing, not ack, 
        if frame.destination_address != 0xffff: 
            hash = hashlib.sha1(umsgpack.dumps({
                'source': frame.source_address,
                'type': frame.type,
                'destination': frame.destination_address,
                'data': b"" + frame.data
            })).digest()

            self.send_message(Frame.FRAME_TYPES['acknowledgement'], hash, frame.source_address)

        # Don't allow direct messaging between some nodes.
        # if self.address != 0x00a2 and frame.source_address != 0x00a2:
        #     return

        # call all the callbacks
        for callback in self.callbacks.get(-1, []):
            try:
                callback(frame)
            except Exception as e:
                callback_name = callback.__name__ if hasattr(
                    callback, '__name__') else callback
                logger(
                    f'error in callback {callback_name} with message {frame}: {e}', channel='error')

        for callback in self.callbacks.get(frame.type, []):
            try:
                callback(frame)
            except Exception as e:
                callback_name = callback.__name__ if hasattr(
                    callback, '__name__') else callback
                logger(
                    f'error in callback {callback_name} with message {frame}: {e}', channel='error')


    def wait_for_ack(self):
        self.ack = False
        timeout = time.time() + 1
        while not self.ack and time.time() < timeout:
            time.sleep(0.001)

        return self.ack

    @property
    def address(self) -> int:
        """ the address of the node """
        return int.from_bytes(b'\x00\x00', 'big')

    def __del__(self):
        self.stop()
