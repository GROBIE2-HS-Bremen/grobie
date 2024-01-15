from libs.Node import Frame
from libs.controllers.config import ConfigController
from libs.controllers.config.NodeConfigData import NodeConfigData
from libs.controllers.network import Frame, INetworkController
from utime import time
import asyncio


class NeighboursController():
    def __init__(self, config_controller: ConfigController, network: INetworkController, heartbeat: int = 120, max_timeout: int = 140) -> None:
        """
        heartbeat: aprox time in seconds between sending a "i am alive" message.
        max_timeout: max time in seconds waiting before deleting the node from the connection table.
        """
        self.config_controller = config_controller
        self.network = network
        self.connections: dict[int, NodeConfigData] = {}
        self.last_update: dict[int, int] = {}

        self.max_timeout = max_timeout
        self.heartbeat = heartbeat

    def broadcast_join(self):
        """
        Broadcasts a message with its config for when the node starts up.
        """
        self.network.send_message(
            Frame.FRAME_TYPES['node_joining'], self.config_controller.config.serialize())

    def start(self):
        loop = asyncio.get_event_loop()
        loop.create_task(self.broadcast_alive_loop())
        loop.create_task(self.nodes_alive_loop())

    async def broadcast_alive_loop(self):
        while True:
            await asyncio.sleep(self.heartbeat)
            self.network.send_message(
                Frame.FRAME_TYPES['node_alive'], self.config_controller.config.serialize())

    async def nodes_alive_loop(self):
        while True:
            await asyncio.sleep(self.max_timeout)
            for node in self.connections:
                if node not in self.last_update or self.last_update[node] + self.max_timeout > time():
                    self.last_update.pop(node)
                    self.connections.pop(node)

    def handle_join(self, frame: Frame):
        """
        Handles when a node joins the network, assumes that the data of frame
        contains the config of the joining node. Sends back their own config.
        """
        if frame.type != Frame.FRAME_TYPES['node_joining']:
            return
        
        print(frame.data)

        node = NodeConfigData.deserialize(frame.data)
        self.connections[node.addr] = node
        self.last_update[node.addr] = time()
        self.network.send_message(
            Frame.FRAME_TYPES['node_alive'], self.config_controller.config.serialize(), node.addr)
        print("Connection created, current table: ", self.connections)

        # set the config in the ledger
        self.config_controller.ledger.ledger[frame.source_address] = node

    def handle_leave(self, frame: Frame):
        """
        Handles when a node leaves the network, no method exists to trigger
        this event right now. Frame data should contain the address of the
        leaving node.
        """
        if frame.type != Frame.FRAME_TYPES['node_leaving']:
            return

        id = int.from_bytes(frame.data, 'big')
        self.connections.pop(id)
        self.last_update.pop(id)
        print("Node leaving network created, current table: ", self.connections)

    def handle_alive(self, frame: Frame):
        """
        Handles a node being alive, updates the config.
        """
        self.last_update[frame.source_address] = time()

        if frame.type != Frame.FRAME_TYPES['node_alive']:
            return

        print(frame)
        node = NodeConfigData.deserialize(frame.data)
        self.connections[frame.source_address] = node

        # set the config in the ledger
        self.config_controller.ledger.ledger[frame.source_address] = node
        print("A node has send a heartbeat, current table: ", self.connections)
