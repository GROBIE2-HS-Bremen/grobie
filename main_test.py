# from libs.controllers.config import NodeConfigData
# from libs.controllers.network import Frame
# from libs.controllers.network.UARTNetworkController import UARTNetworkController
# from libs.controllers.storage.StorageControllerFactory import StorageControllerFactory
# from libs.controllers.network.E220NetworkController import E220NetworkController
# from libs.sensors.SensorFactory import I2CSensorFactory
# from libs.E220 import E220
# from libs.Node import Node

# from machine import I2C, Pin, UART

# import asyncio


# ##### CONNECT SENSORS #####
# i2c = I2C(1, scl=Pin(3), sda=Pin(2), freq=400000)
# # dynamicaly construct storage controller and sensors. 
# # by doibng it this way not all nodes need to have the same sensors or storage
# sc = StorageControllerFactory.get_controller(mosi=Pin(7), miso=Pin(0), sck=Pin(6), cs=Pin(1, Pin.OUT))
# sensors = I2CSensorFactory.create_sensors(i2c)


# ##### INITIALIZE NETWORK #####
# uart = UART(1, baudrate=9600, rx=Pin(5), tx=Pin(4))
# # we will create the same network controller for all nodes as they need to connect to the same network 
# m0 = Pin(26, Pin.OUT)
# m1 = Pin(15, Pin.OUT)
# nc = E220NetworkController(E220(uart=uart, m0=m0, m1=m1))


# ##### START NODE #####
# # start event loop and run forever
# loop = asyncio.get_event_loop()
# node = Node(
#     sensors=sensors,
#     storage_controller=sc,
#     network_controller=nc, # use e220 as network controller
#     node_config=NodeConfigData(
#         addr = nc.address,
#         measurement_interval = 1,
#         replication_count = 4
#     )
# )

# import time
# # secondConfig 
# cnf = NodeConfigData(
#     addr = 2,
#     measurement_interval = 1,
#     replication_count = 0
# )

# # send discovery frame
# frame = Frame(Frame.FRAME_TYPES['discovery'], cnf.serialize(), 1, 255)
# node.network_controller.on_message(frame.serialize())

# time.sleep(1)
# print(node.config_controller.ledger.items())
# time.sleep(1)


# # send replication bid
# frame = Frame(Frame.FRAME_TYPES['replication'], b'\x01', 2, 4)
# node.network_controller.on_message(frame.serialize())

# async def a ():
#     await asyncio.sleep(3)
#     print(node.config_controller.config.replications)
#     await asyncio.sleep(3)

#     loop.stop()

# loop.create_task(a())


# # loop 
# loop.run_forever()


import sys
sys_mpy = sys.implementation._mpy
arch = [None, 'x86', 'x64',
    'armv6', 'armv6m', 'armv7m', 'armv7em', 'armv7emsp', 'armv7emdp',
    'xtensa', 'xtensawin'][sys_mpy >> 10]
print('mpy version:', sys_mpy & 0xff)
print('mpy sub-version:', sys_mpy >> 8 & 3)
print('mpy flags:', end='')
if arch:
    print(' -march=' + arch, end='')
print()