from libs.controllers.config import ConfigController
from libs.controllers.network import Frame

from random import randint
import math

import asyncio

class ReplicationController: 

    bids: dict[int, int]

    def __init__(self, config_controller: ConfigController):
        self.config_controller = config_controller

        self.bids = {}

    @property
    def replicating_nodes(self):
        """ get al the nodes we are replicating. """
        return [k for k, v in self.config_controller.ledger.items() if self.config_controller.config.addr in v.replications]


    def are_replicating(self, node_addr: int):
        """ 
            check if we currently are replicating the node

            Arguments:
                node_addr {int} -- the address of the node we want to check

            Returns:
                bool -- true if we are replicating the node
        """

        # check if we are replicating this node
        return node_addr in self.replicating_nodes
        

    def should_replicate(self, node_addr: int) -> bool: 
        """ 
            check if we should replicate the data from this node 
        
            Arguments:
                node_addr {int} -- the address of the node we want to check
            
            Returns:
                bool -- true if we should replicate the data from this node
        """
        # check if we are replicating this node
        if not self.are_replicating(node_addr):
            return False
        
        # check if he wants new replications
        if self.config_controller.ledger[node_addr].replication_count <= len(self.config_controller.ledger[node_addr].replications):
            return False

        return True
    

    def handle_bid(self, frame: Frame):
        """ 
            Handle a replication bid from another node.
            
            This function will add the bid to the list of bids and if it is the first bid it will start a timer to wait
            for other bids. once the timer has completed it will decide which nodes will store the data.
            if the sending node already has a bid it will be ignored.
        
            Arguments:
                frame {Frame} -- the frame containing the bid
        """
        # check if it is for us 
        if frame.destination_address != self.config_controller.config.addr:
            return

        # check if we already have a bid for this node. if so ignore it.
        if frame.source_address in self.bids:
            return
            
        # store the bid
        self.bids[frame.source_address] = int.from_bytes(frame.data, 'big') # decode the ttl to an int

        # start a timer to wait for other bids. the lenght of this timer is in config
        if not self.waiting_for_bids:
            self.waiting_for_bids = True
            loop = asyncio.get_event_loop()
            loop.create_task(self.decide_winners())




    waiting_for_bids = False
    async def decide_winners(self):
        """ 
            Decide which nodes will store the data.
            
            this function will first wait for the amount of time specified in the config. after that it will decide
            which nodes will store the measurements. it will decide this by trying to distribute the bids over the 
            entire network. 

            after this it will update the configuration and broadcast it on the network. 
        """
        await asyncio.sleep(self.config_controller.config.measurement_interval)
        self.waiting_for_bids = False

        # decide all winners and update config
        winners = self.config_controller.config.replications
        winner_count = self.config_controller.config.replication_count - len(winners)

        if winner_count <= 0:
            return

        # sort the bids
        sorted_bids = sorted(self.bids.items(), key=lambda x: x[1], reverse=True)

        segment_size = len(sorted_bids) // winner_count
        if segment_size == 0:
            # take all bids
            segment_size = 1

        for i in range(min(winner_count, math.ceil(len(sorted_bids) / segment_size))):
            index = randint(i * segment_size, (i + 1) * segment_size - 1)

            node = sorted_bids[index]
            winners[node[0]] = node[1]

        # clear the list of bids and update the replicating nodes
        self.bids = {}
        self.config_controller.update_config('replications', winners)

        
