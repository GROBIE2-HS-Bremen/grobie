from libs.controllers.network import Frame, INetworkController
from libs.controllers.neighbours import NeighboursController
from libs.external.ChannelLogger import logger
from time import time
import asyncio


class RoutingController:
    def __init__(self, neighbours: NeighboursController, network: INetworkController) -> None:
        self.neighbours = neighbours
        self.network = network

        # Time a request lives in seconds
        self.timeout = 30

        # Address -> next hop
        self.routing_table: dict[int, int] = {}

        # Address -> time we got it
        self.request_list: dict[int, int] = {}

    def start(self):
        """ Start up the clean up cycle, will delete all routes older than
            `self.timeout`.
        """
        loop = asyncio.get_event_loop()
        self.task = loop.create_task(self._start())

    async def _start(self):
        """ Clean up cycle
        """
        while True:
            # The current list is empty, might aswell wait for it clear up
            if len(self.request_list) <= 0:
                await asyncio.sleep(self.timeout)
                continue

            for i in self.request_list:
                if self.request_list[i] + self.timeout < time():
                    del self.request_list[i]
                    del self.routing_table[i]

            await asyncio.sleep(self.timeout // 4)

    def get_route(self, address: int) -> int:
        """ Find the route from this node to address, makes use of a modified
            and simplified version of the AODV protocol.

            Returns either -1 if the route is still unkown, or the address of
            next hop when it is.
        """
        # Address found in the routing table
        if address in self.routing_table:
            return self.routing_table[address]

        # Address direct neighbour
        if address in self.neighbours.connections:
            return address

        logger(f'Sending route request for {address}', channel='routing')
        self.network.send_message(Frame.FRAME_TYPES['routing_request'], b''.join([
            self.network.address.to_bytes(2, 'big'),
            (0x00).to_bytes(1, 'big'),
        ]), address)
        self.routing_table[address] = -1
        self.request_list[address] = time()
        return -1

    def handle_routing_request(self, frame: Frame):
        """ Handles a route request.

            When it receives a route request for a node that has been through
            this node it will ignore it.
            Otherwise when the destination of the frame is the same as the
            adress of this node, it will respond with a route reply.
            When it is neither of those cases it will re-broadcast the routing
            request.
        """
        # We have already had this request before recently, ignore.
        if frame.destination_address in self.request_list:
            return

        self.request_list[frame.destination_address] = time()
        if frame.destination_address != self.network.address:
            # Re-broadcast request
            self.network.send_message(Frame.FRAME_TYPES['routing_request'], b''.join([
                frame.data,
                self.network.address.to_bytes(2, 'big'),
                frame.rssi.to_bytes(1, 'big'),
            ]), frame.destination_address)
            return

        # TODO: Make use of the RSSI for best route
        # origin -> between nodes -> end node
        route: list[bytes] = [frame.data[i:i+2]
                              for i in range(0, len(frame.data), 3)]
        route.append(self.network.address.to_bytes(2, 'big'))
        # Rssi can be found on every third value, ignoring for now.
        # rssi = int.from_bytes(frame.data[i+2:i+3], 'big', signed=True)

        logger(f"Found a route: {route}", channel='routing')
        self.network.send_message(
            Frame.FRAME_TYPES['routing_response'],
            b''.join(route),
            int.from_bytes(route[-2], 'big'),
        )

    def handle_routing_response(self, frame: Frame):
        """ Handles a routing response.
            Will pass along to the previous node according to the body of the
            frame and save where request for origin needs to go.
        """
        route = [frame.data[i:i+2] for i in range(0, len(frame.data), 2)]
        self.routing_table[int.from_bytes(
            route[-1], 'big')] = frame.source_address

        if int.from_bytes(route[0], 'big') == self.network.address:
            logger(f"Response route: {route}", channel='routing')
            return

        hop = int.from_bytes(
            route[route.index(self.network.address.to_bytes(2, 'big')) - 1], 'big')
        self.network.send_message(
            Frame.FRAME_TYPES['routing_response'], frame.data, hop)
