import asyncio
from libs.E220 import E220
from libs.controllers.network import Frame,INetworkController,E220NetworkController

import time



class NetworkHandler():
    """
    V1 - Very basic Stop-and-Wait protocol for reliable transmission.
    """

    e220: E220
    

    def __init__(self,e220,max_tries=3) -> None:
        self.e220 = e220
        self.nc = INetworkController
        self.max_tries = max_tries

        self.rcv_ack = False
        self.rxSegments = bytearray()



    
    def cb_incoming_ack(self,message):
        """
        Callback for incoming ACK to extend into receive buffer
        """
        # The right ack
        if message.type == Frame.FRAME_TYPES['acknowledgement']:
            self.rcv_ack = True
        
    def handle_packet(self,frame,sessions={}):
        # More frames incoming and session ID is also set.

        # First session, add first packet as dict to sessions.
        if frame.frame_num and frame.ses_num > 1:
            # Make session if it does not exists
            if not sessions.get(frame.ses_num):
                sessions[frame.ses_num] = frame.__dict__
            else:
                sessions[frame.ses_num]['data'] += frame.data

        # If session exists and last packet we assemble everything and return it.
        elif frame.ses_num in sessions and frame.frame_num == 0:
            packet = sessions[frame.ses_num]
            return Frame(
                type=packet.type,
                message=packet.data,
                source_address=packet.source_address,
                destination_address=packet.destination_address,
                ttl=packet.ttl
            )
        
        else:
            return frame
    
    def wait_for_ack(self,message,addr,ctr=1):
        """
        Check buffer to see if ACK has been received.
        """
        if ctr > self.max_tries:
            return False
        
        last_time = time.time() + 1
        while time.time() < last_time:
            # If we have received the ack in the buffer
            if self.rcv_ack:
                self.rcv_ack = False
                return True
            else:
                time.sleep(0.1)
        
        # No ack received within time because ack/data got lost -> send repeat
        print(f"Not received ack in time, trying again {ctr}/{self.max_tries}")
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
            print(f"[+] ACK received.")
        
        elif received == False:
            print(f"[-] ACK not received.")
      

    def transmit_ack(self,message):

        if message.type == Frame.FRAME_TYPES['acknowledgement'] or message.destination_address == 255:
            return
        
        # end-to-end acks. If the message was intended for this node then send ack back.
        elif message.destination_address == self.nc.address:
            print(f"Sending ACK to {message.source_address}")
            ackmsg = Frame(type=Frame.FRAME_TYPES['acknowledgement'], message=b'', source_address=self.nc.address,
                        destination_address=message.source_address, ttl=20
                        ).serialize()
            self.e220.send(message.source_address.to_bytes(2,'big'),ackmsg)
        
        
         
