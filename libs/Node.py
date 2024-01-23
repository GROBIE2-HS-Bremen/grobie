from libs.controllers.timekeeping.RTCTimekeepingController import RTCTimekeepingController
from libs.controllers.neighbours import NeighboursController
from libs.controllers.config import ConfigController, NodeConfigData
from libs.controllers.network import Frame
from libs.controllers.measurement.Measurement import Measurement
from libs.controllers.database.BinaryKV import BinarKVDatabase
from libs.controllers.measurement import MeasurementController
from libs.controllers.replication import ReplicationController
from libs.controllers.database.CsvDatabase import CsvDatabase
from libs.controllers.network.routing import RoutingController
from libs.controllers.network import INetworkController
from libs.controllers.storage import IStorageController
from libs.external.ChannelLogger import logger
from libs.sensors import ISensor

import time


class Node():

    def __init__(self,
                 sensors: list[ISensor],
                 storage_controller: IStorageController,
                 network_controller: INetworkController,
                 node_config: NodeConfigData) -> None:

        self.sensors = sensors

        ## SETUP CONTROLLERS ##
        # setup and mount storage
        self.storage_controller = storage_controller
        self.storage_controller.mount('/sd')

        # setup config controller
        self.config_controller = ConfigController(
            config=node_config,
            send_message=network_controller.send_message
        )

        # setup network and routing related controllers
        self.network_controller = network_controller
        self.neighbours_controller = NeighboursController(
            config_controller=self.config_controller,
            network=network_controller
        )
        self.routing_controller = RoutingController(
            self.neighbours_controller, network_controller)

        # TODO: Fix this with a different method
        self.network_controller.routing_controller = self.routing_controller  # type: ignore

        # setup measurement related controllers
        self.timekeeping_controller = RTCTimekeepingController()
        self.measurement_controller = MeasurementController(
            sensors=self.sensors,
            timekeeping_controller=self.timekeeping_controller,
            actions=[
                lambda m: logger((type(m), str(m)), channel='measurement'),  # log the measurement
                lambda measurement: self.store_measurement(measurement),     # store the measurement
                lambda measurement: network_controller.send_message(        # broadcast the measurement
                    Frame.FRAME_TYPES['measurement'],
                    measurement.encode()
                )
            ])

        self.replication_controller = ReplicationController(self.config_controller)

        filepath = '/sd/data.db'
        self.database_controller = CsvDatabase(
            filepath, self.storage_controller)

        # register routing callbacks
        self.network_controller.register_callbacks({
            -1: [self.neighbours_controller.handle_alive],
            Frame.FRAME_TYPES['node_joining']: [self.neighbours_controller.handle_join],
            Frame.FRAME_TYPES['node_leaving']: [self.neighbours_controller.handle_leave],
        })

        # register measurement callbacks
        self.network_controller.register_callbacks({
            Frame.FRAME_TYPES['config']: [self.config_controller.handle_message],
            Frame.FRAME_TYPES['measurement']: [self.store_measurement_frame],
            Frame.FRAME_TYPES['replication']: [self.replication_controller.handle_bid],
            Frame.FRAME_TYPES['discovery']: [lambda _: self.config_controller.broadcast_config()],
        })

        # routing callbacks
        self.network_controller.register_callbacks({
            Frame.FRAME_TYPES['routing_request']: [self.routing_controller.handle_routing_request],
            Frame.FRAME_TYPES['routing_response']: [self.routing_controller.handle_routing_response],
        })

        # extra callbacks
        self.network_controller.register_callbacks({
            -1: [self.print_message_received],
            Frame.FRAME_TYPES['sync_time']: [
                lambda frame: self.timekeeping_controller.sync_time(
                    int.from_bytes(frame.data, 'big')
                )
            ],
        })

        logger('Node has been initialized. starting', channel='info')

        self.measurement_controller.start(node_config.measurement_interval)
        self.neighbours_controller.start()
        self.network_controller.start()
        self.routing_controller.start()

        logger('Node has been started. Broadcasting config', channel='info')

        self.neighbours_controller.broadcast_join()

        time.sleep(1)

        ## LOG THE NODES INFO ##
        all_callbacks = []
        for i in self.network_controller.callbacks.values():
            all_callbacks.extend(i)

        info = {
            'address': self.network_controller.address,
            'requested_replications': self.config_controller.config.replication_count,
            'callbacks': {
                key: len(val) for key, val in self.network_controller.callbacks.items()
            }
        }

        logger('Node has been started and joined network.', channel='info')
        for key, val in info.items():
            logger(f'\t {key}: {val}', channel='info')

    def print_message_received(self, frame: Frame):
        logger(
            f'received a message of type {frame.type} from node {frame.source_address} for node {frame.destination_address}: {frame.data} (rssi: {frame.rssi})',
            channel='recieved_message'
        )

    def store_measurement_frame(self, frame: Frame):
        # check if in ledger
        if frame.source_address not in self.replication_controller.config_controller.ledger:
            # send a discovery message
            self.network_controller.send_message(
                Frame.FRAME_TYPES['discovery'],
                b'',
                frame.source_address
            )
            return

        # check if we should store
        if self.replication_controller.are_replicating(frame.source_address):
            print('store measurement', frame.source_address)
            measurement = Measurement.decode(frame.data)
            return self.store_measurement(measurement, frame.source_address)

        # check if it needs new replications
        if self.replication_controller.should_replicate(frame.source_address):
            self.network_controller.send_message(
                3, frame.ttl.to_bytes(4, 'big'), frame.source_address)
            return

    def store_measurement(self, measurement: Measurement, address=None):
        # if no address is passed we will use our own
        if address is None:
            address = self.network_controller.address

        measurement.data['address'] = address
        self.database_controller.store(measurement.timestamp, measurement.data)

    def __del__(self):
        # stop all async tasks and threads
        self.network_controller.stop()
        self.measurement_controller.stop()

        # close the database controller
        del self.database_controller
