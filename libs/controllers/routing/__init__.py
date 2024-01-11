from libs.controllers.neighbours import NeighboursController
from libs.controllers.network import INetworkController


class RoutingController:
    def __init__(self, neighboursController: NeighboursController, networkController: INetworkController) -> None:
        self.neighbours = neighboursController
        self.network = networkController

    async def getRoute(self, address: int):
        """
            Get the route to a node, returns the address of the next connected node.

            When a node is out of reach of the network, this function will return -1.
        """
        return address

    def handle_routing_request(self):
        pass

    def handle_routing_response(self):
        pass
