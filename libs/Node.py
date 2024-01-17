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


class Node():

    def __init__(self,
                 sensors: list[ISensor],
                 storage_controller: IStorageController,
                 network_controller: INetworkController,
                 node_config: NodeConfigData) -> None:

        self.sensors = sensors
        self.storage_controller = storage_controller
        self.network_controller = network_controller

        self.timekeeping_controller = RTCTimekeepingController()

        self.init_storage()

        self.measurement_controller = MeasurementController(
            sensors=self.sensors,
            timekeeping_controller=self.timekeeping_controller,
            actions=[
                lambda m: print(type(m), str(m)),
                lambda measurement: self.store_measurement(measurement),
                lambda measurement: network_controller.send_message(
                    Frame.FRAME_TYPES['measurement'], measurement.encode())
            ])

        self.config_controller = ConfigController(
            config=node_config,
            send_message=network_controller.send_message
        )
        self.neighbours_controller = NeighboursController(
            self.config_controller, network_controller)



        self.replication_controller = ReplicationController(
            self.config_controller)

        filepath = '/sd/data.db'
        self.database_controller = BinarKVDatabase(
            filepath, self.storage_controller)

        # Register message callbacks
        self.network_controller.register_callback(-1, lambda frame: print(
            f'received a message of type {frame.type} from node {frame.source_address} for node {frame.destination_address}'))  # -1 is a wildcard type

        self.network_controller.register_callback(Frame.FRAME_TYPES['measurement'],
                                                  self.store_measurement_frame)  # decide if we want to store the measurement
        self.network_controller.register_callback(
            Frame.FRAME_TYPES['request_config'],
            lambda frame: self.network_controller.send_message(
                Frame.FRAME_TYPES['node_joining'], 
                self.config_controller.config.serialize(), 
                frame.source_address,
            )
        )

        self.network_controller.register_callback(Frame.FRAME_TYPES['config'],
                                                  self.config_controller.handle_message)  # handle config changes
        self.network_controller.register_callback(Frame.FRAME_TYPES['replication'],
                                                  self.replication_controller.handle_bid)  # handle replication changes
        self.network_controller.register_callback(Frame.FRAME_TYPES['node_joining'],
                                                  self.neighbours_controller.handle_join)
        self.network_controller.register_callback(Frame.FRAME_TYPES['node_leaving'],
                                                  self.neighbours_controller.handle_leave)
        self.network_controller.register_callback(-1,
                                                  self.neighbours_controller.handle_alive)
        
        self.network_controller.register_callback(Frame.FRAME_TYPES['sync_time'],
                                                    lambda frame: self.timekeeping_controller.sync_time(int.from_bytes(frame.data, 'big')))

        print(self.network_controller.callbacks)

        print('node has been initialized, starting controllers')

        # make and send measuremnt every 1 second
        self.measurement_controller.start(
            node_config.measurement_interval * 1000)
        self.neighbours_controller.start()
        self.network_controller.start()
        print('node has been initialized, controllers started')

        self.neighbours_controller.broadcast_join()
        print('Sended a broadcast of config')

    def init_storage(self):
        self.storage_controller.mount('/sd')

    def store_measurement_frame(self, frame: Frame):
        print(self.config_controller.ledger.ledger)

        # check if in ledger
        if frame.source_address not in self.config_controller.ledger.ledger:
            print('not in ledger')
            # send a confgi request
            self.network_controller.send_message(
                Frame.FRAME_TYPES['request_config'], frame.ttl.to_bytes(4, 'big'), frame.source_address)
            return

        # check if we should store
        if self.replication_controller.are_replicating(frame.source_address):
            print('saving measurement')
            measurement = Measurement.decode(frame.data)
            return self.store_measurement(measurement)

        # check if it needs new replications
        if self.replication_controller.should_replicate(frame.source_address):
            print('making bid')
            # check if we have enough replications
            self.network_controller.send_message(
                3, 
                frame.ttl.to_bytes(4, 'big'), 
                frame.source_address
            )
            return 
        
        print('should not be reachable')

    def store_measurement(self, measurement: Measurement, address=None):
        d = measurement.data
        d['address'] = address  # type: ignore

        self.database_controller.store(measurement.timestamp, d)
