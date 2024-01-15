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
        
        self.network_handler = NetworkHandler(e220=e220)
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
    

    def handle_packet(self,frame,sessions={}):
        # More frames incoming and session ID is also set.
        # First session, add first packet as dict to sessions.
        if frame.frame_num and frame.ses_num != 0:
            # Make session if it does not exists
            if not sessions.get(frame.ses_num):
                sessions[frame.ses_num] = frame.__dict__
            else:
                sessions[frame.ses_num]['data'] += frame.data
            self.network_handler.transmit_ack(frame)


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
        
    def send_message(self, type: int, message: bytes, addr=255,ttl=20,datasize=188):
        """ send a message to the specified address splits into multiple messages if needed.
        Ebyte module sends data in one continous message if data is 199 bytes or lower.
        """
        
        frame_num = 0
        length_msg = len(message)
        data_splits = []
        
        if length_msg > datasize:
            # Random sessionnumber
            ses_num = random.randint(1,255)
            
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
            ses_num = 0
            data_splits = [message]

        print(f"Sending package(s) - {data_splits}")
        for msg in data_splits:
            frame = Frame(type,msg,self.address,addr,ttl,ses_num,frame_num)
            self.network_handler.transmit_packet(frame)
            frame_num -= 1

    @property
    def address(self) -> int:
        return int.from_bytes(self.e220.address, 'big')
