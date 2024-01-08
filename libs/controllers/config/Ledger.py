from libs.controllers.config import NodeConfigData


class Ledger: 

    ledger: dict[int, NodeConfigData]

    def __init__(self, ledger = None) -> None:
        if ledger is None:
            ledger = {}
        self.ledger = ledger


    def get_node_config(self, addr):
        return self.ledger[addr]
    
    def __getitem__(self, addr):
        return self.ledger[addr]

    def __setitem__(self, addr, config):
        self.ledger[addr] = config

    def apply_diff(self, diff, addr):
        if addr not in self.ledger:
            self.ledger[addr] = NodeConfigData(addr, 0, 0)

        self.ledger[addr].apply_diff(diff)

    # make it iterable

    def __iter__(self):
        return iter(self.ledger)
    
    def __len__(self):
        return len(self.ledger)
    
    def __contains__(self, addr):
        return addr in self.ledger
    
    def items(self):
        return self.ledger.items()
