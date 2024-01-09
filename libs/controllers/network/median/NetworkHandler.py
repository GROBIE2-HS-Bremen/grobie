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
    

    def __init__(self,data) -> None:
        self.netcontroller.register_callback(0x04,self.cb_incoming_ack)
        self.netcontroller.register_callback(0x01,self.transmit_ack)

        self.seq = 0
        self.ack = 0

        self.rxAckBuff = bytearray()

        
        self.rxSegments = bytearray()


    async def cb_measurements(self,message):
        # TO DO
        raise NotImplementedError()

        
    async def cb_incoming_ack(self,message):
        """
        Callback for incoming ACK to extend into receive buffer
        """
        # The right ack
        if message.type == 0x04:
            self.rxAckBuff.extend(message)
        else:
            pass
        

    async def wait_for_ack(self,message,addr):
        """
        Check buffer to see if ACK has been received.
        """
       
        while time.time() < time.time() + 1:
            # If we have received the ack in the buffer
            if self.rxAckBuff:
                self.rxAckBuff.clear()
                return True
            else:
                continue
        
        # No ack received within time because ack/data got lost -> send repeat
        print("Didnt receive ack in time trying again...")
        self.e220.send(message,addr)
        self.wait_for_ack(message,addr)
        
       

    
    async def transmit_packet(self,message,type,addr,source_address,destination_address,ttl,rbt):
        """
        Very simple Stop-And-Wait protocol for sending data

        """

        lock = asyncio.Lock()
        
        # Only add sequence number on measurement packets
        if type == 0x01 and rbt:
            async with lock:
                message = Frame.serialize(type,message,source_address,destination_address,ttl,self.seq)
                self.e220.send(message,addr)
                received = await self.wait_for_ack(message,addr)

            if received == True:
                print(f"[+] ACK received")
            
            elif received == False:
                print(f"[-] Something went wrong")

        else:
            message = Frame.serialize(type,message,source_address,destination_address,ttl)
            self.e220.send(message,addr)



    async def transmit_ack(self,message):
        ackmsg = Frame(type=0x04, message=b'TESTACK', source_address=message.destination_address,
                       destination_address=message.source_address, ttl=20,ack=0
                       )
        ackmsg = ackmsg.serialize()
        self.e220.send(ackmsg,message.source_address)
      
        
         

