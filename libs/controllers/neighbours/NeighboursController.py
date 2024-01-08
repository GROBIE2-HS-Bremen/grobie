from libs.Node import Frame
from libs.controllers.config.NodeConfigData import NodeConfigData
from libs.controllers.network import Frame, INetworkController
from utime import time


class NeighboursController():
    def __init__(self, node_config: NodeConfigData, network: INetworkController) -> None:
        self.node_config = node_config
        self.network = network
        self.connections: dict[int, NodeConfigData] = {}
        self.last_update: dict[int, int] = {}

    def broadcast_join(self):
        """
        Broadcasts a message with its config for when the node starts up.
        """
        self.network.send_message(
            Frame.FRAME_TYPES['node_joining'], self.node_config.serialize())

    def handle_join(self, frame: Frame):
        """
        Handles when a node joins the network, assumes that the data of frame
        contains the config of the joining node. Sends back their own config.
        """

        if frame.type != Frame.FRAME_TYPES['node_joining']:
            return

        node = NodeConfigData.deserialize(frame.data)
        self.connections[node.addr] = node
        self.last_update[node.addr] = time()
        self.network.send_message(
            Frame.FRAME_TYPES['node_alive'], self.node_config.serialize(), node.addr)

    def handle_leave(self, frame: Frame):
        """
        Handles when a node leaves the network, no method exists to trigger
        this event right now. Frame data should contain the address of the
        leaving node.
        """
        if frame.type != Frame.FRAME_TYPES['node_leaving']:
            return

        id = frame.data
        self.connections.pop(int.from_bytes(id, 'big'))

    def handle_alive(self, frame: Frame):
        """
        Handles a node being alive, updates the config.
        """
        if frame.type != Frame.FRAME_TYPES['node_alive']:
            return

        node = NodeConfigData.deserialize(frame.data)
        self.last_update[node.addr] = time()
        self.connections[node.addr] = node
