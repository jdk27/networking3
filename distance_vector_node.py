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

    # Called to inform you that an outgoing link to a neighbor has changed.
    # It tells you that you can reach a certain neighbor (identified by an integer) with a certain latency.
    # In response, you may want to update your tables and send further messages to your neighbors.
    def link_has_been_updated(self, neighbor, latency):
        # if latency == -1 delete a link
            # remove entries from the DV where the next hop is this link
        # else: link has gotten longer or shorter
            # find the difference between the original and new latency
            # add this difference to the cost of all paths where this neighbor is the first hop
        # updates one's own sequence number
        # send out DV with new sequence number
        pass

    # Called when a routing message "m" arrives at a node.
    # This STRING message would have been sent by a neighbor
    # In response, you may send further routing messages using self.send_to_neighbors or self.send_to_neighbor.
    # You may also update your tables.
    def process_incoming_routing_message(self, m):
        # get neighbor number and sequenuce number from message
        # compare the sequenuce number with that the node currently associates with its neighbor
        # if the message's sequence number is greater, update the DV
            # update the sequence number the node associates with the neighbor
            # for every destination in the messages DV
                # if the destination is in the node's DV, see if it needs to be updated
                    # if min{cost(x, m)+cost(m,y)>cost(x,y)} update DV
                # else, add a new entry in the DV for this destination
        # else do nothing
        pass

    # Return a neighbor, -1 if no path to destination
    # Check routing table
    def get_next_hop(self, destination):
        # see if the destination is a valid key in the DV
        # if it is, get the first node in the path to the destinstion
        # else return -1
        return -1
