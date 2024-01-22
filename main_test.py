from libs.controllers.storage.StorageControllerFactory import StorageControllerFactory
from libs.controllers.network.E220NetworkController import E220NetworkController
from libs.controllers.network.E220NetworkController.E220 import E220
from libs.sensors.SensorFactory import I2CSensorFactory
from libs.controllers.config import NodeConfigData
from libs.external.ChannelLogger import logger
from libs.Node import Node
from libs.controllers.network import Frame

from machine import I2C, Pin, UART

import asyncio


##### CONNECT SENSORS #####
i2c = I2C(1, scl=Pin(3), sda=Pin(2), freq=400000)
sensors = I2CSensorFactory.create_sensors(i2c)

### CONNECT STORAGE CONTROLLER #####
sc = StorageControllerFactory.get_controller(
    mosi=Pin(7), 
    miso=Pin(0), 
    sck=Pin(6), 
    cs=Pin(1, Pin.OUT)
)


##### INITIALIZE E220 #####
uart = UART(1, baudrate=9600, rx=Pin(5), tx=Pin(4), timeout=15)
m0 = Pin(26, Pin.OUT)
m1 = Pin(15, Pin.OUT)
nc = E220NetworkController(E220(uart=uart, m0=m0, m1=m1), set_config=True)

# Config
print(nc.address)
node_config = NodeConfigData(
    addr=nc.address,
    measurement_interval=100,
    replication_count=4
)

## SETUP LOGGER ##
# register custom log levels
logger.set_channel('recieved_message', True)
logger.set_channel('send_message', True)
logger.set_channel('measurement', False)
logger.set_channel('routing', False)


##### START NODE #####
# start event loop and run forever
loop = asyncio.get_event_loop()

try: 
    # create node and loop in try except block to catch keyboard interrupt\
    # this way we can stop everything
    node = Node(
        sensors=sensors,
        storage_controller=sc,
        network_controller=nc,  # use e220 as network controller
        node_config=node_config,
    )

    loop.run_forever()
except KeyboardInterrupt:
    del node

except Exception as e:
    logger((e,), channel='error')
    raise e


async def send_frames():
    """
    Test the splitting of messages. And receiving ACK'S.
    This message will get split in 5 packets so we need to wait on 5 ACK's. 
    """
    data = b'1TEST'+200*b'TEST'+b'TEST2'

    
    # We need to get 5 ACKS because sending 5 messages
    while True:
        node.network_controller.send_message(1,data,4)
        await asyncio.sleep(5)
        

async def receive_frames():
    """
    This function mimics the receiving of 5 frames with splitted data. And sends ACK's for each message (if destination is this node)
    The goal is to keep track of the session and assemble the data correctly and ack messages.
    """

    frames = [b'1test',b'2test']
    amount_frames = 0


    frame = Frame(type=Frame.FRAME_TYPES['measurment'], message=frames[0], source_address=5,
                destination_address=0xFFFF, ttl=20, frame_num=2, ses_num=6553
                ).serialize() + b'\x00'
    node.network_controller.on_message(frame)

    
    frame = Frame(type=Frame.FRAME_TYPES['measurment'], message=frames[1], source_address=5,
                destination_address=0xFFFF, ttl=20, frame_num=1, ses_num=6553
                ).serialize() + b'\x00'
    node.network_controller.on_message(frame)

    frame = Frame(type=Frame.FRAME_TYPES['measurment'], message=b'CLOSING', source_address=5,
                        destination_address=0xFFFF, ttl=20,frame_num=0,ses_num=6553
                        ).serialize()+b'\x00'
    
    node.network_controller.on_message(frame)
    


loop.create_task(send_frames())



# async def a():
#     from libs.controllers.network import Frame

#     orig_time = node.timekeeping_controller.get_time()
#     f = Frame(
#         Frame.FRAME_TYPES['sync_time'],
#         (orig_time - 10000000).to_bytes(4, 'big'),
#         nc.address,
#         1
#     )
#     node.network_controller.on_message(f.serialize())

#     new_time = node.timekeeping_controller.get_time()

#     print(orig_time, new_time, orig_time - new_time)



