from libs.controllers.storage.StorageControllerFactory import StorageControllerFactory
from libs.controllers.network.E220NetworkController import E220NetworkController
from libs.controllers.network.E220NetworkController.E220 import E220
from libs.sensors.SensorFactory import I2CSensorFactory
from libs.controllers.config import NodeConfigData
from libs.external.ChannelLogger import logger
from libs.Node import Node

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
node_config = NodeConfigData(
    addr=nc.address,
    measurement_interval=5,
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

