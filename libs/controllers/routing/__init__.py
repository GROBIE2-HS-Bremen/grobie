import asyncio
from libs.controllers.config.NodeConfigData import NodeConfigData
from libs.controllers.neighbours import NeighboursController
from libs.controllers.network import Frame, INetworkController




class RoutingController:
    def __init__(self, node_config: NodeConfigData, neighboursController: NeighboursController, networkController: INetworkController) -> None:
        self.node_config = node_config
        self.neighbours = neighboursController
        self.network = networkController
        self.routes: dict[int, tuple[int, int]] = {}    # destination: (next_hop, hops)
        self.handled_requests: dict[int, Frame] = {}
        self.timers = {}

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
            request_id = self.node_config.addr + address    #TODO generate a random request id
            hop_count = 0
            self.send_route_request(request_id, hop_count, self.node_config.addr, address, self.node_config.addr, 10, True)
            self.routes[address] = (-1, -1)
            return -1
        
    def add_route(self, destination: int, next_hop: int, hops: int):
        """
        Adds a route to the routing table.

        Args:
            destination (int): The address of the destination node.
            next_hop (int): The address of the next hop node.
            hops (int): The number of hops to the destination node.

        Returns:
            None
        """
        if destination not in self.routes or self.routes[destination][0] == -1:
            self.routes[destination] = (next_hop, hops)
        else:
            if self.routes[destination][1] > hops:
                self.routes[destination] = (next_hop, hops)
        
    def send_route_request(self, request_id: int, hop_count: int, source: int, destination: int, last_hop: int, ttl: int, broadcast: bool):
        hop_count += 1
        ttl -= 1
        data = request_id.to_bytes(2, 'big') + hop_count.to_bytes(1, 'big')
        

        if broadcast:
            next_hop = 255
            self.network.send_message(
                Frame.FRAME_TYPES['route_request'], data, source, destination, next_hop, self.node_config.addr, ttl
                )
        else:
            next_hop = self.getRoute(destination)
            self.network.send_message(
                Frame.FRAME_TYPES['route_request'], data, source, destination, next_hop, self.node_config.addr, ttl
                )
            


    def send_route_reply(self, request_id: int, hop_count: int, source: int, destination: int, last_hop: int, ttl: int):
        ttl -= 1
        data = request_id.to_bytes(2, 'big') + hop_count.to_bytes(1, 'big')
        new_frame = Frame(Frame.FRAME_TYPES["route_reply"], data, source, destination, last_hop, ttl) #TODO check if this works with last_hop
        next_hop = self.getRoute(destination)
        self.network.send_message(
            Frame.FRAME_TYPES['route_response'], data, source, destination, next_hop, last_hop, ttl
        )

    def extract_data(data: bytes) -> tuple:
        request_id = int.from_bytes(data[:2], 'big')
        hop_count = int.from_bytes(data[2:3], 'big')
        return request_id, hop_count

    async def start_timer(self, request_id, delay):
        await asyncio.sleep(delay)
        if request_id in self.timers:
            hop_count = self.extract_data(self.handled_requests[request_id].data)[1]
            source = self.node_config.addr
            destination = self.handled_requests[request_id].source_address
            last_hop = self.node_config.addr
            ttl = self.handled_requests[request_id].ttl

            self.send_route_reply(request_id,  hop_count, source, destination, last_hop, ttl )
            del self.timers[request_id]

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
        last_address = deserialized_frame.last_hop
        request_id, hop_count = self.extract_data(deserialized_frame.data) #TODO check if data needs to come from deserialized frame or not

        if source == self.node_config.addr:
            print("routing request returned to source")
            return     
        
        if address != destination and request_id in self.handled_requests:
            print("routing request already handled")
            return
        else:
            self.handled_requests[request_id] = deserialized_frame
        
        self.add_route(destination, last_address, hop_count)

        if address == destination:
            if request_id in self.timers:
                return
            else:
                self.timers[request_id] = asyncio.create_task(self.start_timer(request_id, 10))
            self.send_route_reply(request_id, hop_count, address, source, address, deserialized_frame.ttl)
        elif destination in self.neighbours.connections:
            print("destination is a neighbour")
            self.send_route_request(request_id, hop_count, source, destination, self.node_config.addr, deserialized_frame.ttl, False)   #TODO check if neighbours.connections are also in routes, then this check can be removed
        elif destination in self.routes:
            self.send_route_request(request_id, hop_count, source, destination, self.node_config.addr, deserialized_frame.ttl, False)
        else:
            self.send_route_request(request_id, hop_count, source, destination, self.node_config.addr, deserialized_frame.ttl, True)
            

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
        last_address = deserialized_frame.last_hop
        request_id, hop_count = self.extract_data(deserialized_frame.data)

        if source not in self.routes:
            self.routes[source] = (last_address, hop_count)

        if address != destination:
            self.send_route_reply(request_id, hop_count, source, destination, self.node_config.addr, deserialized_frame.ttl)
        

