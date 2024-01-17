import asyncio
import random
from libs.E220 import E220, MODE_CONFIG, MODE_NORMAL
from libs.controllers.network import Frame, INetworkController
from libs.controllers.network.median.NetworkHandler import NetworkHandler


class E220NetworkController(INetworkController):
    callbacks: dict[int, list] = {}
    network_handler: NetworkHandler

    def __init__(self, e220: E220,set_config=False):
        super().__init__()
        
        self.e220 = e220
        self.sessions = {}
        self.frame_order = {}
        
        self.network_handler = NetworkHandler(e220, self)
        self.register_callback(Frame.FRAME_TYPES['acknowledgement'],self.network_handler.cb_incoming_ack)
        self.register_callback(-1,self.network_handler.transmit_ack)

        self.e220.set_mode(MODE_CONFIG)
        self.e220.get_settings()

        if set_config: 
            import config as cfg

            for cnf_key in [
                dir_val for dir_val in dir(cfg) 
                    if not callable(getattr(cfg, dir_val)) 
                    and not dir_val.startswith("__")
                ]:

                print(f'setting {cnf_key} to {getattr(cfg, cnf_key)}')
                setattr(self.e220, cnf_key, getattr(cfg, cnf_key))

        self.e220.save()
        self.e220.set_mode(MODE_NORMAL)

    async def _start(self):
        # start seperate thread
        while True:
            d = self.e220.read()
            if d:
                self.on_message(d)
            await asyncio.sleep(0.1)
    

    def handle_packet(self,frame: Frame):
        # More frames incoming and session ID is also set.
        sessions = self.sessions
        frame_order = self.frame_order
        
        # Not closing packet or single packet..
        if frame.frame_num != 0:

            # Make session if it does not exists
            if not sessions.get(frame.ses_num):
                print('[+] Adding session')

                sessions[frame.ses_num] = {
                    'destination_address':frame.destination_address,
                    'ttl':frame.ttl,
                    'source_address':frame.source_address,
                    'ses_num':frame.ses_num,
                    'frame_num':frame.frame_num,
                    'type':frame.type,
                    'data':b''
                }
                frame_order[frame.ses_num].insert(frame.frame_num,frame.data)

         

        # If session exists and CLOSING packet we assemble everything and return it.
        elif frame.ses_num in sessions and frame.frame_num == 0:
            
            
            self.frame_order[frame.ses_num].insert(frame.data)
            data = b''.join(frame_order[frame.ses_num])
            sessions[frame.ses_num]['data'] = data

            self.network_handler.transmit_ack(frame)

            packet = sessions[frame.ses_num]
            print('[+] Complete packet is:')
            print(packet)
            return Frame(
                type=packet['type'],
                source_address=packet['source_address'],
                destination_address=packet['destination_address'],
                ttl=packet['ttl'],
                message=packet['data'],
            )
            # TODO Delete session here
        else:
            print('[+] Single packet received')
            return frame
        
    def send_message(self, type: int, message: bytes, addr=255,ttl=20,datasize=188):
        """ send a message to the specified address splits into multiple messages if needed.
        Ebyte module sends data in one continous message if data is 199 bytes or lower.
        """
        
        frame_num = 0
        length_msg = len(message)
        data_splits = []
        
        
        if length_msg > datasize:
            # Random sessionnumber
            # 2 bytes
            ses_num = random.randint(1,60000)
            
            # Amount of frames to send
            frame_num = length_msg // datasize + 1
            
            start = 0
            end = datasize
            

            while True:
                if end > length_msg:
                    end = length_msg

                data_splits.append(message[start:end])
                start += datasize
                end += datasize
                
                if start > length_msg:
                    break
        else:
            frame = Frame(type,message,self.address,addr,ttl,ses_num=0,frame_num=0)
            self.network_handler.transmit_packet(frame)
            return

            
        for msg in data_splits:
            print(f"Sending package - {msg} with session number {ses_num} and frame number {frame_num}")
            frame = Frame(type,msg,self.address,addr,ttl,ses_num,frame_num)
            self.network_handler.transmit_packet(frame)
            frame_num -= 1
        
        # Send closing frame.
        frame_num = 0
        print(f"Sending CLOSING packet with session number 0 and frame number 0!")
        frame = Frame(type,b'CLOSING',self.address,addr,ttl,ses_num,frame_num)
        self.network_handler.transmit_packet(frame)
        
        

    @property
    def address(self) -> int:
        return int.from_bytes(self.e220.address, 'big')
