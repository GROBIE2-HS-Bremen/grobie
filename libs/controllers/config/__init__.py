from libs.controllers.config.NodeConfigData import NodeConfigData
from libs.helpers.dict import deserialize_dict, serialize_dict
from libs.controllers.config.Ledger import Ledger
from libs.controllers.network import Frame


class ConfigController:

    def __init__(
            self,
            config: NodeConfigData,
            send_message
    ):
        self._config = config
        self.send_message = send_message

        self._ledger = Ledger()

    @property
    def config(self):
        return self._config

    @property
    def ledger(self):
        return self._ledger

    def handle_message(self, frame: Frame):
        # parse the message
        config = deserialize_dict(frame.data)
        # apply the diff to the config
        self._ledger.apply_diff(config, frame.source_address)

    def update_config(self, key, value):
        # clone the config
        # update the config
        self.config[key] = value

        # broadcast the new config
        self.broadcast_config()

    def clone_config(self):
        # clone the config
        n = self._config.clone()

        # clone the replications. dict is pass by reference instead of value
        for addr, distance in self._config.replications.items():
            n.replications[addr] = distance

        return n

    def broadcast_config(self, new_config=None):
        if new_config is None:
            # broadcast the config. 
            # we use the node_alive type as it is used to keep the node in the network. 
            # it takes the config as data 
            self.send_message(Frame.FRAME_TYPES['node_alive'], self._config.serialize())

        else:
            # broadcast only the difference config
            diff = self._config.diff(new_config)
            self.send_message(Frame.FRAME_TYPES['config'], serialize_dict(diff))
