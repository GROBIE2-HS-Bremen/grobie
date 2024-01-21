from libs.controllers.config import ConfigController, NodeConfigData
from libs.controllers.database.BinaryKV import BinarKVDatabase
from libs.controllers.measurement import MeasurementController
from libs.controllers.measurement.Measurement import Measurement
from libs.controllers.network import INetworkController
from libs.controllers.network.E220NetworkController import Frame
from libs.controllers.replication import ReplicationController
from libs.controllers.timekeeping.RTCTimekeepingController import RTCTimekeepingController
from libs.sensors import ISensor
from libs.controllers.storage import IStorageController
from libs.controllers.neighbours import NeighboursController
from libs.controllers.routing import RoutingController

from libs.external.ChannelLogger import logger

class Node():

    def __init__(self,
                 sensors: list[ISensor],
                 storage_controller: IStorageController,
                 network_controller: INetworkController,
                 node_config: NodeConfigData) -> None:

        self.sensors = sensors
        self.storage_controller = storage_controller
        self.network_controller = network_controller
        self.neighbours_controller = NeighboursController(
            node_config, network_controller)
        self.node_config = node_config
        # self.node_config.routing_table = {4, 5, 6, 7, 8, 9, 10}
        self.routing_controller = RoutingController(self.node_config, network_controller)
        
        self.timekeeping_controller = RTCTimekeepingController()

        self.init_storage()

        self.measurement_controller = MeasurementController(
            sensors=self.sensors,
            timekeeping_controller=self.timekeeping_controller,
            actions=[
                lambda m: logger((type(m), str(m)), channel='measurement'),
                lambda measurement: self.store_measurement(measurement),
                # lambda measurement: network_controller.send_message(
                #      1, measurement.encode(), node_config.addr, 255, 255),
                lambda measurement: network_controller.send_message(
                     1, measurement.encode(), node_config.addr, 65532, 65532),
                lambda measurement: network_controller.send_message(
                     1, measurement.encode(), node_config.addr, 65531, 65531),
                # lambda measurement: network_controller.send_message(
                #      1, measurement.encode(), node_config.addr, 65533, 65533),
                lambda measurement: print(node_config.addr),
                # lambda measurement: network_controller.send_message(
                #      0x0a, measurement.encode(), node_config.addr)



                # add address to  send measurement to.
            ])

        self.config_controller = ConfigController(
            config=node_config,
            send_message=network_controller.send_message
        )

        self.replication_controller = ReplicationController(
            self.config_controller)

        filepath = '/sd/data.db'
        self.database_controller = BinarKVDatabase(
            filepath, self.storage_controller)

        # Register message callbacks
        self.network_controller.register_callback(-1, lambda frame: logger(
            f'received a message of type {frame.type} from node {frame.source_address} for node {frame.destination_address}: {frame.data} (rssi: {frame.rssi})', 
            channel='recieved_message'
            )
        )  # -1 is a wildcard type

        self.network_controller.register_callback(Frame.FRAME_TYPES['measurment'],
                                                  self.store_measurement_frame)  # decide if we want to store the measurement
        self.network_controller.register_callback(Frame.FRAME_TYPES['discovery'],
                                                  self.config_controller.handle_message)  # new nodes will broadcast this type of message
        self.network_controller.register_callback(Frame.FRAME_TYPES['config'],
                                                  self.config_controller.handle_message)  # handle config changes
        self.network_controller.register_callback(Frame.FRAME_TYPES['replication'],
                                                  self.replication_controller.handle_bid)  # handle replication changes
        self.network_controller.register_callback(Frame.FRAME_TYPES['node_joining'],
                                                  self.neighbours_controller.handle_join)
        self.network_controller.register_callback(Frame.FRAME_TYPES['node_leaving'],
                                                  self.neighbours_controller.handle_leave)
        self.network_controller.register_callback(Frame.FRAME_TYPES['route_request'],
                                                  self.routing_controller.handle_route_request)
        self.network_controller.register_callback(Frame.FRAME_TYPES['route_response'],
                                                  self.routing_controller.handle_route_response)
        self.network_controller.register_callback(-1,
                                                  self.neighbours_controller.handle_alive)
        
        self.network_controller.register_callback(Frame.FRAME_TYPES['sync_time'],
                                                    lambda frame: self.timekeeping_controller.sync_time(int.from_bytes(frame.data, 'big')))
        #TODO: call handle route request when we get a route request
        #TODO: call handle route response when we get a route response

        logger('node has been initialized, starting controllers', channel='info')

        # make and send measuremnt every 1 second
        self.measurement_controller.start(
            node_config.measurement_interval * 1000)
        self.neighbours_controller.start()
        self.network_controller.start()
        logger('node has been initialized, controllers started', channel='info')

        self.neighbours_controller.broadcast_join()
        logger('Sended a broadcast of config', channel='info')

    def init_storage(self):
        self.storage_controller.mount('/sd')

    def store_measurement_frame(self, frame: Frame):
        # check if we should store
        if self.replication_controller.should_replicate(frame.source_address):
            measurement = Measurement.decode(frame.data)
            return self.store_measurement(measurement)

        # check if it needs new replications
        if self.replication_controller.are_replicating(frame.source_address):
            # check if we have enough replications
            if len(self.replication_controller.config_controller.ledger[frame.source_address].replications) < \
                    self.replication_controller.config_controller.ledger[frame.source_address].replication_count:
                # send a bid
                self.network_controller.send_message(
                    3, frame.ttl.to_bytes(4, 'big'), frame.source_address)
                return

    def store_measurement(self, measurement: Measurement, address=None):
        d = measurement.data
        d['address'] = address  # type: ignore

        self.database_controller.store(measurement.timestamp, d)
