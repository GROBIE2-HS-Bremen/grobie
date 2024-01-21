import random
from libs.controllers.config import NodeConfigData
#from libs.controllers.neighbours import NeighboursController
from libs.controllers.network import Frame, INetworkController


class RoutingController:
    def __init__(self, node_config: NodeConfigData,  networkController: INetworkController) -> None:
        self.node_config = node_config
        #self.neighbours = neighboursController
        self.network = networkController
        # self.routes: dict[int, tuple[int, int]] = {}    # destination: (next_hop, hops)
        # self.handled_requests: dict[int, Frame] = {}
        self.timers = {}
        self.routing_table = self.node_config.routing_table
        self.send_requests: dict[str, int] = {}
        self.handled_requests = {}

    def get_route(self, address: int):
        # print("getting route")
        # print(self.routing_table)
        if address in self.routing_table:
            print("address in routing table")
            print(self.routing_table)
            print("next hop is", self.routing_table[address][0])
            return self.routing_table[address][0]
        else:
            # else send route request
            request_id = str(self.node_config.addr) + str(address)
            if request_id in self.send_requests:
                #print("request id is in send requests")
                self.send_requests[request_id] -= 1
                if self.send_requests[request_id] == 0:
                    # self.routing_table[address] = (2, 3) #decomment this to test a route has been found
                    del self.send_requests[request_id]
                print(self.send_requests)
                return None
            else:
                self.send_requests[request_id] = 5
                print("sending route request")
                if address not in self.routing_table:
                    self.send_route_request(int(request_id), 0, self.node_config.addr, address, 255 , 20, True)


            return -1
        

    def add_route(self, destination: int, next_hop: int, hops: int):
        if destination not in self.routing_table:
            self.routing_table[destination] = (next_hop, hops)

        print("routing table is now", self.routing_table)
        #self.neighbours.add_neighbour(address, node_config)

    def send_route_request(self, request_id: int, hop_count: int, source: int, destination: int, address:int, ttl: int, broadcast: bool):

        hop_count += 1
        ttl -= 1
        data = request_id.to_bytes(2, 'big') + hop_count.to_bytes(1, 'big')
        
        if broadcast:
            self.network.send_message(Frame.FRAME_TYPES['route_request'], data, source, destination, 255)
        
        else:
            self.network.send_message(Frame.FRAME_TYPES['route_request'], data, source, destination, address)

    def send_route_response(self, request_id: int, hop_count: int, source: int, destination: int, last_hop: int, ttl: int):
        # hop_count += 1
        # ttl -= 1
        print("sending route response")
        data = request_id.to_bytes(2, 'big') + hop_count.to_bytes(1, 'big')
        self.network.send_message(Frame.FRAME_TYPES['route_request'], data, source, destination, last_hop)

    
    def handle_route_request(self, frame: Frame):
        print("handling route request")
        address = self.node_config.addr
        request_id = int.from_bytes(frame.data[:2], 'big')
        hop_count = int.from_bytes(frame.data[2:3], 'big')
        source = frame.source_address
        destination = frame.destination_address
        last_hop = frame.last_hop
        if self.handled_requests.get(request_id) == None:
            self.handled_requests[request_id] = frame
        else:
            print("request id already handled")
            return    

        if source == self.node_config.addr:
            print("source is self")
            return
        if request_id in self.send_requests:
            print("request id is in send requests, so already send")
            return
        
        self.add_route(source, last_hop, hop_count )
        

        if address == destination:
            print("address is destination")
            self.send_route_response(request_id, hop_count, destination, source, last_hop, 20)
            return
        elif destination in self.routing_table:
            print("destination in routing table")
            self.send_route_request(request_id, hop_count, source, destination, self.routing_table[destination][0], 20, False)
            return
        else:
            print("sending route request")
            self.send_route_request(request_id, hop_count, source, destination, 255, 20, True)
        
        
        return

    def handle_route_response(self, frame: Frame):
        print("handling route response")
        address = self.node_config.addr
        request_id = int.from_bytes(frame.data[:2], 'big')
        hop_count = int.from_bytes(frame.data[2:3], 'big')
        source = frame.source_address
        destination = frame.destination_address
        last_hop = frame.last_hop

        if destination == self.node_config.addr:
            print("received a response back")
            del self.send_requests[str(request_id)]
            self.add_route(source, last_hop, hop_count)
        else:
            print("forwarding route response")
            self.send_route_response(request_id, hop_count, source, destination, last_hop, 20)
