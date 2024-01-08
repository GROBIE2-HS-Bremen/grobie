import libs.external.umsgpack as umsgpack
from libs.helpers.dict import DiffChange, apply_diff, diff_dict
# from libs.helpers.dict import apply_diff, diff_dict

class NodeConfigData:
    """ 
    This class represents the configuration of a node. 
    this will controll the storage and generation of the data 

    Attributes
    ----------
    addr : int
        the address of the node. value is in range [0, 255]
    measurement_interval : int
        the interval in which the node should measure from the sensors. this 
    replications : dict[int, int]
        a map of the replications of this node. the key is the address of the node
        and the value is the amount of nodes away from this node
    replication_count : int
        the amount of replications this node wants
    ledger : dict
        a map of the configuration of the nodes in the network. the key is the address
        of the node and the value is the configuration of the node
    """

    # network config
    addr: int  # 2 bytes unsigned
    
    # measuserument config 
    measurement_interval: int # 6 bytes unsigned

    # storage config
    replications: dict[int, int] # 2 byte unsigned keys, 2 byte unsigned values
    replication_count: int # 2 bytes unsigned
    

    def __init__(self, addr: int, measurement_interval: int, replication_count, replications=None, bidding_wait = 1) -> None:
        self.addr = addr
        self.measurement_interval = measurement_interval
        self.replication_count = replication_count
        self.bidding_wait = bidding_wait


        if replications is None:
            replications = {}
        self.replications = replications

    def serialize(self):
        """ serialize the node config """
        return umsgpack.dumps({
            'addr': self.addr,
            'measurement_interval': self.measurement_interval,
            'replication_count': self.replication_count,
            'replications': self.replications,
            'bidding_wait': self.bidding_wait
        })
    
    @staticmethod
    def deserialize(bits):
        """ deserialize the node config """
        return NodeConfigData(**umsgpack.loads(bits))

    def clone(self):
        return self.deserialize(self.serialize())

    def apply_diff(self, diff):
        """ apply a diff to the node config. 
            this doesnt use the apply_diff function from libs/helpers/dict.py 
            because it provides a strange error and the diffing is simple enough 
            to do it manually 
        """
        if 'addr' in diff:
            raise ValueError('Address should not be changed during operation')
        if 'measurement_interval' in diff:
            self.measurement_interval = diff['measurement_interval'][1]
        if 'replication_count' in diff:
            self.replication_count = diff['replication_count'][1]
        if 'replications' in diff:
            for key, value in diff['replications']:
                if value[0] == DiffChange.REMOVED:
                    del self.replications[key]
                elif value[0] == DiffChange.ADDED:
                    self.replications[key] = value[1]
                elif value[0] == DiffChange.MODIFIED:
                    self.replications[key] = value[1]

    def diff(self, other):
        """ diff this node config with another node config """
        if not isinstance(other, NodeConfigData):
            raise TypeError('other is not a NodeConfigData')

        return diff_dict(self.__dict__, other.__dict__)

    def __str__(self) -> str:
        return f'NodeConfigData(addr={self.addr}, measurement_interval={self.measurement_interval}, replication_count={self.replication_count}, replications={self.replications})'
    
    def __repr__(self) -> str:
        return self.__str__()
    
    def __eq__(self, o: object) -> bool:
        if not isinstance(o, NodeConfigData):
            return False
        
        return self.__dict__ == o.__dict__
    
    def __setitem__(self, key, value):
        setattr(self, key, value)
    
    def __dict__(self) -> dict:
        return {
            'addr': self.addr,
            'measurement_interval': self.measurement_interval,
            'replication_count': self.replication_count,
            'replications': self.replications
        }
