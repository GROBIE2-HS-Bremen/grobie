import asyncio
import _thread
import time
import config as cfg


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
        'route_request': 0x0a,
        'route_response': 0x0b
    }

    def __init__(self, type: int, message: bytes, source_address: int, destination_address: int, last_hop: int, ttl=20, rssi=-1):
        self.type = type
        self.source_address = source_address
        self.destination_address = destination_address
        self.last_hop = last_hop
        self.ttl = ttl
        self.rssi = rssi

        self.data = message

    def serialize(self) -> bytes:
        return b''.join([
            self.type.to_bytes(1, 'big'),
            self.source_address.to_bytes(2, 'big'),
            self.destination_address.to_bytes(2, 'big'),
            self.last_hop.to_bytes(2, 'big'),
            self.data
        ])

    @staticmethod
    def deserialize(frame: bytes):
        type = frame[0]
        source_address = int.from_bytes(frame[1:3], 'big')
        destination_address = int.from_bytes(frame[3:5], 'big')
        last_hop = int.from_bytes(frame[5:7], 'big')
        message = frame[7:]
        rssi = -1

        if cfg.rssi_enabled:  # type: ignore
            rssi = message[-1]
            message = message[:-1]

        return Frame(type, message, source_address, destination_address, last_hop, rssi=rssi)


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
                type, message, source, destination, addr = self.q.pop()
               
                self._send_message(type, message, source, destination, addr)
                #self.q.pop()
            else:
                time.sleep(0.001)

    def _send_message(self, type: int, message: bytes, source: int, destination: int, addr=255):
        """ send a message to the specified address """
        raise NotImplementedError()

    async def _start(self):
        """ the main loop of the network controller """
        raise NotImplementedError()

    def stop(self):
        """ stop the network controller """
        self.task.cancel()

    def send_message(self, type: int, message: bytes, source: int, destination=255, addr=255):
        """ send a message to the specified address """
        print("this message function is also called")
 
        self.q.append((type, message, source, destination, addr))
        # print("this is the queue in INetworkController")
        # print(self.q)

    def register_callback(self, addr: int, callback):
        """ register a callback for the specified address """
        if addr not in self.callbacks:
            self.callbacks[addr] = []

        self.callbacks[addr].append(callback)

    def on_message(self, message: bytes):
        """ called when a message is recieved """
        frame = Frame.deserialize(message)  
        print("this is the frame that is received")
        print(frame.__dict__)
        print("this is the destination address")
        print(frame.destination_address)

        # print("on_message")
       

        
            
        # print("frame type is", frame.type)
        # print("should be", Frame.FRAME_TYPES['route_request'])
        if frame.type == Frame.FRAME_TYPES['route_request']:
                print("this frame is a route request")
                pass
        elif frame.type == Frame.FRAME_TYPES['route_response']:
                print("this frame is a route response")
                pass
        elif frame.destination_address != self.address and frame.destination_address != 255:
                print("this frame is not for me, sending message")
                self.send_message(frame.type, frame.data, frame.source_address, frame.destination_address, frame.destination_address)
                return

        #TODO check if frame is for this node, if not, forward it before the callbacks are called -> this is the routing part,call send_message, there the route is checked.
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
