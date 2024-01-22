from libs.controllers.network import Frame, INetworkController
from libs.controllers.neighbours import NeighboursController
from libs.external.ChannelLogger import logger


class RoutingController:
    def __init__(self, neighbours: NeighboursController, network: INetworkController) -> None:
        self.neighbours = neighbours
        self.network = network

        # Address -> next hop
        self.routing_table: dict[int, int] = {}

        # Have we already gotten this request.
        # TODO: Clear entry
        self.request_list: list[int] = []

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
        self.request_list.append(address)
        return -1

    def handle_routing_request(self, frame: Frame):
        # TODO: Make this _not_ a one shot gun.

        # We have already had this request before, ignore.
        if frame.destination_address in self.request_list:
            return

        if frame.destination_address == self.network.address:
            # TODO: Make use of the RSSI for best route
            self.request_list.append(frame.destination_address)

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

            return

        # Re-broadcast request
        self.request_list.append(frame.destination_address)
        self.network.send_message(Frame.FRAME_TYPES['routing_request'], b''.join([
            frame.data,
            self.network.address.to_bytes(2, 'big'),
            frame.rssi.to_bytes(1, 'big'),
        ]), frame.destination_address)

    def handle_routing_response(self, frame: Frame):
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
