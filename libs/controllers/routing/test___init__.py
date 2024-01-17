import unittest
from unittest.mock import MagicMock
from libs.controllers.config.NodeConfigData import NodeConfigData
from libs.controllers.routing import RoutingController
from libs.controllers.network import Frame

class TestRoutingController(unittest.TestCase):
    def setUp(self):
        self.routing_controller = RoutingController()
        self.frame = Frame(Frame.FRAME_TYPES['route_request'], b'data', 'source', 'destination')
        self.routing_controller.node_config = NodeConfigData('address')

    def test_handle_routing_request_with_non_route_request_frame(self):
        self.frame.type = 'other_type'
        self.routing_controller.handle_routing_request(self.frame)
        # Assert that nothing happens when the frame type is not 'route_request'
        # You can add more assertions here if needed

    def test_handle_routing_request_with_same_source_and_destination(self):
        self.frame.destination_address = 'address'
        self.routing_controller.send_route_reply = MagicMock()
        self.routing_controller.handle_routing_request(self.frame)
        self.routing_controller.send_route_reply.assert_called_once_with()
        # Assert that the 'send_route_reply' method is called when the source and destination addresses are the same

    def test_handle_routing_request_with_destination_as_neighbour(self):
        self.frame.destination_address = 'neighbour_address'
        self.routing_controller.neighbours.connections = ['neighbour_address']
        self.routing_controller.send_route_request = MagicMock()
        self.routing_controller.handle_routing_request(self.frame)
        self.routing_controller.send_route_request.assert_called_once_with(self.frame, 'neighbour_address')
        # Assert that the 'send_route_request' method is called when the destination address is a neighbour

    def test_handle_routing_request_with_destination_in_routes(self):
        self.frame.destination_address = 'route_address'
        self.routing_controller.routes = {'route_address': 'last_address'}
        self.routing_controller.getRoute = MagicMock(return_value='route_address')
        self.routing_controller.send_route_request = MagicMock()
        self.routing_controller.handle_routing_request(self.frame)
        self.routing_controller.send_route_request.assert_called_once_with(self.frame, 'route_address')
        # Assert that the 'send_route_request' method is called when the destination address is in the routes

    def test_handle_routing_request_with_unknown_destination(self):
        self.frame.destination_address = 'unknown_address'
        self.routing_controller._forward_to_all_neighbours = MagicMock()
        self.routing_controller.handle_routing_request(self.frame)
        self.routing_controller._forward_to_all_neighbours.assert_called_once_with(self.frame)
        # Assert that the '_forward_to_all_neighbours' method is called when the destination address is unknown

if __name__ == '__main__':
    unittest.main()