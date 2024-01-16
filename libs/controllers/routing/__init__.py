from libs.controllers.config.NodeConfigData import NodeConfigData
from libs.controllers.neighbours import NeighboursController
from libs.controllers.network import Frame, INetworkController


#TODO ensure that the source and destination addresses are forwarded correctly. they should
# be the same as the original frame, not the current node's address. Also, last_address should probably be handled differently.
#TODO add a hop_count to the frame, and increment it each time the frame is forwarded. This will allow the node to know how many hops it is from the destination.

class RoutingController:
    def __init__(self, node_config: NodeConfigData, neighboursController: NeighboursController, networkController: INetworkController) -> None:
        self.node_config = node_config
        self.neighbours = neighboursController
        self.network = networkController
        self.routes: dict[int, tuple[int, int]] = {}    # destination: (next_hop, hops)

    async def getRoute(self, address: int):
            """
            Get the route to a node, returns the address of the next connected node.

            Args:
                address (int): The address of the node to find the route to.

            Returns:
                int: The address of the next connected node in the route.

            Notes:
                If the node is out of reach of the network, this function will send out a route_request to all neighbours and return -1.
            """

            if address in self.routes:
                print("address found in routes")
                return self.routes[address][0]
            else:
                print("address not found in routing table")
                frame = Frame(Frame.FRAME_TYPES['route_request'], self.node_config.serialize(), self.node_config.addr, address)
                self._forward_to_all_neighbours(frame)
                return -1
        
    def send_route_request(self, frame: Frame, address: int):
        self.network.send_message(
            Frame.FRAME_TYPES['route_request'], self.node_config.serialize(), address
        )

    def send_route_reply(self, frame: Frame, address: int):
        self.network.send_message(
            Frame.FRAME_TYPES['route_response'], self.node_config.serialize(), address
        )


    def handle_routing_request(self, frame: Frame):
        """
        Handles a routing request frame.

        Args:
            frame (Frame): The routing request frame to handle.

        Returns:
            None
        """
        if frame.type != Frame.FRAME_TYPES['route_request']:
            return
        
        deserialized_frame = Frame.deserialize(frame)
        address = self.node_config.addr
        source = deserialized_frame.source_address
        destination = deserialized_frame.destination_address
        last_address = NodeConfigData.deserialize(frame.data).addr

        if source not in self.routes:
            self.routes[source] = last_address

        if address == destination:
            print("sending routing response")
            frame = Frame(Frame.FRAME_TYPES['route_response'], self.node_config.serialize, destination, source)
            self.send_route_reply()
        elif destination in self.neighbours.connections:
            print("destination is a neighbour")
            self.send_route_request(frame, destination) 
        elif destination in self.routes:
            self.send_route_request(frame, self.getRoute(destination))
        else:
            self._forward_to_all_neighbours(frame)
            

    def handle_route_reply(self, frame: Frame):
        """
        Handles the route reply frame received by the node.

        Args:
            frame (Frame): The route reply frame to be handled.

        Returns:
            None
        """
        if frame.type != Frame.FRAME_TYPES['route_reply']:
            return

        deserialized_frame = Frame.deserialize(frame)
        address = self.node_config.addr
        source = deserialized_frame.source_address
        destination = deserialized_frame.destination_address
        last_address = NodeConfigData.deserialize(frame.data).addr

        if source not in self.routes:
            self.routes[source] = last_address

        if address != destination:
            self.send_route_reply(frame, self.getRoute(destination))
        
    def _forward_to_all_neighbours(self, frame: Frame):
        """
        Forwards the given frame to all neighbours in the network.

        Args:
            frame (Frame): The frame to be forwarded.

        Returns:
            None
        """
        for neighbour in self.neighbours.connections:
            self.network.send_message(frame.type, frame.data, neighbour)