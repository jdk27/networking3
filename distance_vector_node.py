from simulator.node import Node


class Distance_Vector_Node(Node):
    def __init__(self, id):
        super().__init__(id)
        self.neighbor_dv = {}
        self.costs = {}
        self.dv = {}
        self.seq_num = {}

   
    # Need a function to update link costs which will also update DV

    # Need a function to update personal DV

    # Need a function to check for shorter times from other DVS after cost or personal DV is changed


    # Return a string
    def __str__(self):
        return "Rewrite this function to define your node dump printout"

    # Fill in this function
    # Called to inform you that an outgoing link connected to your node has just changed its properties.  
    # It tells you that you can reach a certain neighbor (identified by an integer) with a certain latency.  
    # In response, you may want to update your tables and send further messages to your neighbors.  

    # Going to want to update link costs here and send the new DV to all neighbors
    def link_has_been_updated(self, neighbor, latency):
        # latency = -1 if delete a link
        pass

    # Fill in this function
    # Called when a routing message "m" arrives at a node.  
    # This message would have been sent by a neighbor (more about how to do that later).  
    # The message is a string.  
    # In response, you may send further routing messages using self.send_to_neighbors or self.send_to_neighbor. 
    # You may also update your tables.
    
    # Going to want to update DV here
    def process_incoming_routing_message(self, m):
        pass

    # Return a neighbor, -1 if no path to destination
    # Check routing table
    def get_next_hop(self, destination):
        return -1
