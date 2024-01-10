import asyncio
from libs.E220 import E220
from libs.controllers.network import Frame,INetworkController
import time


class NetworkHandler():
    """
    V1 - Very basic Stop-and-Wait protocol for reliable transmission.
    """

    e220 = E220
    frame = Frame
    netcontroller = INetworkController
    

    def __init__(self,netcontroller) -> None:
        
        netcontroller.register_callback(Frame.FRAME_TYPES['acknowledgement'],self.cb_incoming_ack)
        netcontroller.register_callback(-1,self.transmit_ack)

        self.seq = False
        self.ack = False

        self.rcv_ack = False
        self.rxSegments = bytearray()

    async def cb_measurements(self,message):
        # TO DO
        raise NotImplementedError()
    
    async def cb_incoming_ack(self,message):
        """
        Callback for incoming ACK to extend into receive buffer
        """
        # The right ack
        if message.type == Frame.FRAME_TYPES['acknowledgement']:
            self.rcv_ack = True
        
    async def wait_for_ack(self,message,addr):
        """
        Check buffer to see if ACK has been received.
        """
        lasttime = time.time() + 1
        while time.time() < lasttime:
            # If we have received the ack in the buffer
            if self.rcv_ack:
                self.rcv_ack = False
                return True
            else:
                await asyncio.sleep(0.1)
        
        # No ack received within time because ack/data got lost -> send repeat
        print("Didnt receive ack in time trying again...")
        self.e220.send(message,addr)
        self.wait_for_ack(message,addr)
    
    async def transmit_packet(self,message,type,addr,source_address,destination_address,ttl,rbt):
        """
        Very simple Stop-And-Wait protocol for sending data

        """

        lock = asyncio.Lock()
        message = Frame(type,message,source_address,destination_address,ttl).serialize()
        
        if rbt:
            async with lock:
                self.e220.send(addr,message)
                received = await self.wait_for_ack(message,addr)

            if received == True:
                print(f"[+] ACK received")
            
            elif received == False:
                print(f"[-] Something went wrong")

        else:
            self.e220.send(addr,message)



    async def transmit_ack(self,message):
        ackmsg = Frame(type=0x04, message=b'TESTACK', source_address=message.destination_address,
                       destination_address=message.source_address, ttl=20
                       ).serialize()
        self.e220.send(message.source_address,ackmsg)
      
        
         
