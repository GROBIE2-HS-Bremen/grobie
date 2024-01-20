from libs.controllers.config import NodeConfigData
#from libs.controllers.neighbours import NeighboursController
from libs.controllers.network import Frame, INetworkController


class RoutingController:
    def __init__(self, node_config: NodeConfigData,  networkController: INetworkController) -> None:
        self.node_config = node_config
        #self.neighbours = neighboursController
        self.network = networkController
        self.routes: dict[int, tuple[int, int]] = {}    # destination: (next_hop, hops)
        self.handled_requests: dict[int, Frame] = {}
        self.timers = {}

    async def get_route(self, address: int):
        print("getting route")
        # if address in self.routes:
        #     return self.routes[address]
        # else:
        #     self.network.send_message(Frame.FRAME_TYPES['route_request'], b'', address)

        #     for i in range(10):
        #         await asyncio.sleep(0.1)
        #         if address in self.routes:
        #             return self.routes[address]
        
        #     return None

    
    def handle_route_request(self, frame: Frame):
        print("handling route request")
        pass

    def handle_route_response(self, frame: Frame):
        print("handling route response")
        pass