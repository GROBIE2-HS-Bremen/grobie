from libs.controllers.config import NodeConfigData
from libs.controllers.storage.StorageControllerFactory import StorageControllerFactory
from libs.controllers.network.E220NetworkController import E220NetworkController
from libs.sensors.SensorFactory import I2CSensorFactory
from libs.E220 import E220
from libs.Node import Node
from libs.controllers.network import Frame

from machine import I2C, Pin, UART

from libs.external.ChannelLogger import logger

import asyncio


##### CONNECT SENSORS #####
i2c = I2C(1, scl=Pin(3), sda=Pin(2), freq=400000)
# dynamicaly construct storage controller and sensors.
# by doibng it this way not all nodes need to have the same sensors or storage
sc = StorageControllerFactory.get_controller(
    mosi=Pin(7), miso=Pin(0), sck=Pin(6), cs=Pin(1, Pin.OUT))
sensors = I2CSensorFactory.create_sensors(i2c)

##### INITIALIZE NETWORK #####
uart = UART(1, baudrate=9600, rx=Pin(5), tx=Pin(4), timeout=15)
# we will create the same network controller for all nodes as they need to connect to the same network
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
logger.set_channel('measurement', True)
logger.set_channel('routing', True)


##### START NODE #####
# start event loop and run forever
loop = asyncio.get_event_loop()
node = Node(
    sensors=sensors,
    storage_controller=sc,
    network_controller=nc,  # use e220 as network controller
    node_config=node_config,
)

async def msgs_ack():
    """
    Test the splitting of messages. And ACK'S.
    This message will get split in 5 packets so we need to wait on 5 ACK's. 
    """
    data = b'1TEST'+200*b'TEST'+b'TEST2'
    
    # We need to get 5 ACKS because sending 5 messages
    while True:
        node.network_controller.send_message(1,data,3)
        asyncio.sleep(5)
    


async def msgs_ack():
    """
    Test the splitting of messages. And ACK'S.
    This message will get split in 5 packets so we need to wait on 5 ACK's. 
    """
    data = b'1TEST'+200*b'TEST'+b'TEST2'
    
    # We need to get 5 ACKS because sending 5 messages
    while True:
        node.network_controller.send_message(1,data,3)
        asyncio.sleep(5)
    


async def assemble_msgs():
    """
    This function mimics the receiving of 3 frames with separate data. And sends ACK's for each message. 
    The goal is to keep track of the session and assemble the data correctly.
    """

    amount_frames = 3
    
    
    frames = [b'1-TEST-',b'2-TEST-',b'3-TEST']
    for i in frames:
        frame = Frame(type=Frame.FRAME_TYPES['measurment'], message=i, source_address=3,
                        destination_address=4, ttl=20,frame_num=amount_frames,ses_num=6553
                        ).serialize()+b'\x00'
        amount_frames -= 1
        node.network_controller.on_message(frame)


    frame = Frame(type=Frame.FRAME_TYPES['measurment'], message=i, source_address=3,
                        destination_address=4, ttl=20,frame_num=0,ses_num=6553,rssi=3
                        ).serialize()+b'\x00'
    
    node.network_controller.on_message(frame)
    
        
        




loop.create_task(msgs_ack())
