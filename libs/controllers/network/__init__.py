import asyncio
from libs.E220 import E220



class Frame: 
    FRAME_TYPES = {
        'discovery': 0x00,
        'measurment': 0x01,
        'config': 0x02,
        'replication': 0x03,
        'acknowledgement':0x04
    }

    def __init__(self, type: int, message: bytes, source_address: int, destination_address: int, ttl=20,seq: int,ack: int):
        self.type = type
        self.source_address = source_address
        self.destination_address = destination_address
        self.ttl = ttl
        self.seq = None
        self.ack = None
        self.data = message

    def serialize(self) -> bytes:
        # We send maximum 199 bytes to send data in one packet.
        return b''.join([
            self.type.to_bytes(1, 'big'), 
            self.destination_address.to_bytes(2, 'big'),
            self.source_address.to_bytes(2, 'big'), 
            #self.seq.to_bytes(2, 'big'),
            self.ttl.to_bytes(3, 'big'),
            #self.reqnum.to_bytes(2, 'big'),
            #self.datalen.to_bytes(2, 'big'),
            self.data,
            #self.crc.to_bytes(2, 'big')
            
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
    network: NetworkHandler
    e220 = E220
   

    def __init__(self):
        self.callbacks = {}
        
    def start(self):
        """ start the network controller """
        loop = asyncio.get_event_loop()
        self.task = loop.create_task(self._start())

    async def _start(self):
        while True:
            d = self.e220.read()
            if d:
                self.on_message(d)
                
            await asyncio.sleep(0.1)

    def stop(self):
        """ stop the network controller """
        self.task.cancel()

    def send_message(self, type: int, source_address,destination_address,ttl, message: bytes, addr=255):
        """ send a message to the specified address TODO split into multiple messages..."""
  
        # boolean True if simple stop-and-wait reliable protocol needs to be used. Else False
        self.network.transmit_packet(message,type,addr,source_address,destination_address,ttl,True)




        
    def register_callback(self, type: int, callback):
        """ register a callback for the specified address """
        if type not in self.callbacks:
            self.callbacks[type] = []

        self.callbacks[type].append(callback)

    def on_message(self, message: bytes):
        """ called when a message is recieved """
        frame = Frame.deserialize(message)

        # get all the callback functions
        callbacks = self.callbacks.get(-1, [])  # get the callbacks for the wildcard
        callbacks += self.callbacks.get(frame.type, [])  # get the callbacks for the specific type

        
        # call all the callbacks
        for callback in callbacks:
            callback(frame)


    @property
    def address(self) -> int:
        """ the address of the node """
        return int.from_bytes(b'\x00\x00', 'big')
    

