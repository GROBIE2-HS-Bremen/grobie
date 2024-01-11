from libs.controllers.config import NodeConfigData
from libs.controllers.storage.StorageControllerFactory import StorageControllerFactory
from libs.controllers.network.E220NetworkController import E220NetworkController
from libs.sensors.SensorFactory import I2CSensorFactory
from libs.E220 import E220
from libs.Node import Node

from machine import I2C, Pin, UART

import asyncio

##### CONNECT SENSORS #####
i2c = I2C(1, scl=Pin(3), sda=Pin(2), freq=400000)
# dynamicaly construct storage controller and sensors.
# by doibng it this way not all nodes need to have the same sensors or storage
sc = StorageControllerFactory.get_controller(
    mosi=Pin(7), miso=Pin(0), sck=Pin(6), cs=Pin(1, Pin.OUT))
sensors = I2CSensorFactory.create_sensors(i2c)

##### INITIALIZE NETWORK #####
uart = UART(1, baudrate=9600, rx=Pin(5), tx=Pin(4), timeout=10)
# we will create the same network controller for all nodes as they need to connect to the same network
m0 = Pin(26, Pin.OUT)
m1 = Pin(15, Pin.OUT)
nc = E220NetworkController(E220(uart=uart, m0=m0, m1=m1), set_config=False)

# Config
node_config = NodeConfigData(
    addr=nc.address,
    measurement_interval=5,
    replication_count=4
)

##### START NODE #####
# start event loop and run forever
loop = asyncio.get_event_loop()
node = Node(
    sensors=sensors,
    storage_controller=sc,
    network_controller=nc,  # use e220 as network controller
    node_config=node_config,
)


async def testendpoint():
    await asyncio.sleep(1)
    node.network_controller.send_message(1,b'',3)

loop.create_task(testendpoint())


loop.run_forever()
