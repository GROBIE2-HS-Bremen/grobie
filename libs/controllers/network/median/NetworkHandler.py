import asyncio
from libs.controllers.network.E220NetworkController import E220
from libs.controllers.network import Frame, INetworkController
from libs.external.ChannelLogger import logger
import random
import time



class NetworkHandler():
    """
    V1 - Very basic Stop-and-Wait protocol for reliable transmission.
    """

    e220: E220
    

    def __init__(self,e220,network_controller: INetworkController, max_tries=3) -> None:
        self.e220 = e220
        self.nc = network_controller
        self.max_tries = max_tries

        self.rcv_ack = False

    
    def cb_incoming_ack(self,message):
        """
        Callback for incoming ACK to extend into receive buffer
        """

        if message.type == Frame.FRAME_TYPES['acknowledgement']:
            self.rcv_ack = True
           
        
    def wait_for_ack(self,message,addr,ctr=1):
        """
        Check buffer to see if ACK has been received.
        """
        if addr == 0xFFFF:
            return
        
        rt = 1
        
        if ctr > self.max_tries:
            return False
        
        elif ctr > 1:
            rt = random.randint(1,ctr)
            last_time = time.time() + rt

        else:
            last_time = time.time() + 1

        
        while time.time() < last_time:
            # If we have received the ack in the buffer
            if self.rcv_ack:
                logger("Received ACK")
                self.rcv_ack = False
                return True
            else:
                time.sleep(0.1)
        
        # No ack received within time because ack/data got lost -> send repeat
        logger(f"Not received ack in time, trying again {ctr}/{self.max_tries} with timeout of {rt} seconds.")
        self.e220.send(addr,message)
        self.wait_for_ack(message,addr,ctr+1)
    
    def transmit_packet(self,frame: Frame):
        """
        Very simple Stop-And-Wait protocol for sending data

        """

        message = frame.serialize()
        addr = (frame.destination_address).to_bytes(2,'big')

        if frame.destination_address == 255:
            return self.e220.send(addr,message)


        self.e220.send(addr,message)
        received = self.wait_for_ack(message,addr)

        if received == True:
            logger(f"[+] ACK received.")
        
        elif received == False:
            logger(f"[-] ACK not received.")
      

    def transmit_ack(self,frame):
        """
        Send ACK when message is arrived.
        """
        
        # If intended for this end-device send ACK.
        if frame.destination_address == self.nc.address:
            ackmsg = Frame(type=Frame.FRAME_TYPES['acknowledgement'], message=b'', source_address=self.nc.address,
                        destination_address=frame.source_address, ttl=20,frame_num=0,ses_num=frame.ses_num
                        ).serialize()
            
            self.e220.send(frame.source_address.to_bytes(2,'big'),ackmsg)
            logger(f"[+] Done sending ACK node {self.nc.address} -> {frame.source_address}")
        
        else:
            return
        
         
