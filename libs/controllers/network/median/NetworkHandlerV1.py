import asyncio
import random
from libs.E220 import E220
import time






class Frame: 
    FRAME_TYPES = {
        'discovery': 0x00,
        'measurment': 0x01,
        'config': 0x02,
        'replication': 0x03,
        'acknowledgement':0x04
    }

    def __init__(self, type: int, message: bytes, source_address: int, destination_address: int, ttl=20):
        self.type = type
        self.source_address = source_address
        self.destination_address = destination_address
        self.ttl = ttl
        self.data = message

    def serialize(self) -> bytes:
        return b''.join([
            self.type.to_bytes(1, 'big'), 
            self.source_address.to_bytes(2, 'big'), 
            self.destination_address.to_bytes(2, 'big'),
            self.data
        ])

    @staticmethod
    def deserialize(frame: bytes):
        type = frame[0]
        source_address = int.from_bytes(frame[1:3], 'big')
        destination_address = int.from_bytes(frame[3:5], 'big')
        message = frame[5:]

        return Frame(type, message, source_address, destination_address)




class NetworkHandlerV1():
    """
    Very basic Stop-and-Wait protocol for reliable transmission.
    
    """
    e220 = E220
    

    def __init__(self,data) -> None:
        self.rxBuff = bytearray()

    
    async def cb_incoming_ack(self,message):
        """
        Callback for incoming ACK to extend into receive buffer
        """
        if message.type == 0x04:
            self.rxBuff.extend(message)
        else:
            pass
        

    async def wait_for_ack(self):
        """
        Check buffer to see if ACK has been received.
        """
       
        while time.time() < time.time() + 1:
            # If we have received the ack in the buffer
            if self.rxBuff:
                self.rxBuff.clear()
                return True
            else:
                continue

        return False

    
    async def transmit_packet(self,message,type,addr,rbt):
        """
        Very simple Stop-And-Wait protocol for sending data

        """
        lock = asyncio.Lock()
        # Only add sequence number on measurement packets
        if type == 0x01 and rbt:
            async with lock:
                self.e220.send(message,addr)
                received = await self.wait_for_ack()
           

            if received == True:
                print("[+] ACK received")
            
            elif received == False:
                print(f"[-] Something went wrong")

        else:
            self.e220.send(message,addr)

            
        
         
    
class INetworkController: 
    """ the abstract base class for all network controllers """

    task: asyncio.Task
    callbacks: dict[int, list]
    network: NetworkHandlerV1
   

    def __init__(self):
        self.callbacks = {0x04:self.network.cb_incoming_ack()}
        
    def start(self):
        """ start the network controller """
        loop = asyncio.get_event_loop()
        self.task = loop.create_task(self._start())

    async def _start(self):
        """ the main loop of the network controller """
        raise NotImplementedError()

    def stop(self):
        """ stop the network controller """
        self.task.cancel()

    def send_message(self, type: int, message: bytes, addr=255):
        """ send a message to the specified address """
        message = Frame.serialize(type=type,message=message)
        
        # boolean True if simple stop-and-wait reliable protocol needs to be used. Else False
        self.network.transmit_packet(message,type,addr,True)

        
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
    



