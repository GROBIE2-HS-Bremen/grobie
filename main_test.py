from libs.controllers.config import NodeConfigData
from libs.controllers.network import Frame
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
uart = UART(1, baudrate=9600, rx=Pin(5), tx=Pin(4), timeout=15)
# we will create the same network controller for all nodes as they need to connect to the same network
m0 = Pin(26, Pin.OUT)
m1 = Pin(15, Pin.OUT)
nc = E220NetworkController(E220(uart=uart, m0=m0, m1=m1), set_config=False)

# Config
node_config = NodeConfigData(
    addr=nc.address,
    measurement_interval=100,
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

# async def a():
#     import libs.external.umsgpack as umsgpack

#     await asyncio.sleep(5)

#     addr = 22
#     print('\n'*4)


#     # request the config of the node 
#     await asyncio.sleep(2)
#     print('requesting config' + '*'*12)
#     f = Frame(Frame.FRAME_TYPES['request_config'], b'', addr, 0x0004, addr)
#     node.network_controller.on_message(
#         f.serialize()
#     )
#     print('\n\n')

#     measurement = Frame(
#         Frame.FRAME_TYPES['measurement'],
#         umsgpack.dumps({
#             'timestamp': 123123123,
#             'sensor': 0.1324123,
#             'value': 1
#         }),
#         addr, 0xffff, addr
#     )
#     print('\n\n')

#     print('sending measurement (not in ledger)' + '*'*12)
#     # when receiving a measurement we should send a request_config(id: 0) frame 
#     node.network_controller.on_message(
#         measurement.serialize()
#     )

#     # if we recieve a config we should update it in the ledger
#     await asyncio.sleep(2)
#     cnf = NodeConfigData(
#         addr=addr,
#         measurement_interval=100,
#         replication_count=4,
#         replications={
#             2: 0,
#             3: 20
#         }
#     )

#     f = Frame(Frame.FRAME_TYPES['node_joining'], cnf.serialize(), addr, 0xffff, addr)
#     print('sending config' + '*'*12)
#     node.network_controller.on_message(
#         f.serialize()
#     )
#     await asyncio.sleep(1)
#     print(node.config_controller.ledger.ledger)
#     print('\n\n')

#     # # if we send a measurement we should send a replication bid 
#     await asyncio.sleep(2)
#     print('sending measurement (in ledger) not replicating' + '*'*12)
#     node.network_controller.on_message(
#         measurement.serialize()
#     )

#     print('\n\n')

#     await asyncio.sleep(2)
#     cnf.replications[4]= 2
#     f = Frame(Frame.FRAME_TYPES['node_joining'], cnf.serialize(), addr, 0xffff, addr)
#     print('sending config' + '*'*12)
#     node.network_controller.on_message(
#         f.serialize()
#     )

#     print('\n\n')

#     # if we send a measurement it should be saved
#     await asyncio.sleep(2)
#     print('sending measurement (in ledger)' + '*'*12)
#     node.network_controller.on_message(
#         measurement.serialize()
#     )

# loop.create_task(a())

loop.run_forever()
