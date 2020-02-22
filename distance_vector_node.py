from simulator.node import Node
import json
import math


class Distance_Vector_Node(Node):
    def __init__(self, id):
        super().__init__(id)
        self.dv = {str(id): [0, []]}  # Personal DV
        self.seq_num = 0  # Personal sequence number
        self.neighbor_info = {}

    class Neighbor():
        def __init__(self, id, seq_num, latency, dv):
            self.id = id
            self.seq_num = seq_num
            self.latency = latency
            self.dv = dv

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
        if latency == -1:  # delete a link
            if neighbor in self.neighbor_info:
                self.remove_link(neighbor)
        elif neighbor in self.neighbor_info:  # update a link
            self.update_link_latency(neighbor, latency)
        else:  # create a link
            self.create_link(neighbor, latency)
        self.send_to_neighbors(self.format_message())
        pass

    def remove_link(self, neighbor_id):
        del self.neighbor_info[neighbor]
        for destination in self.dv:
            if self.dv[destination][1][0] == neighbor_id:
                del self.dv[destination]
                # see if neighbors have path to destination

    # FIX: need to fix the path to the neighbor whose latency was updated
    def update_link_latency(self, neighbor_id, new_latency):
        length_change = new_latency - self.neighbor_info[neighbor_id].latency
        self.neighbor_info[neighbor_id].latency = new_latency
        for destination in self.dv:
            if self.dv[destination][1][0] == neighbor_id:
                self.dv[destination][0] += length_change
        # check all other DVs to see if there exists a shorter path

    def create_link(self, neighbor_id, latency):
        new_neighbor = self.Neighbor(neighbor_id, 0, latency, {})
        self.neighbor_info[neighbor_id] = new_neighbor
        # if there is no path to the new neighbor
        if neighbor_id not in self.dv:
            self.dv[neighbor_id] = [
                self.neighbor_info[neighbor_id].latency, [neighbor_id]]
        # if there was already a path to the neighbor and the one-hop cost is cheaper than the older path
        elif self.neighbor_info[neighbor_id].latency < self.dv[neighbor_id][0]:
            self.dv[neighbor_id] = [
                self.neighbor_info[neighbor_id].latency, [neighbor_id]]

    # Called when a routing message "m" arrives at a node.
    # This STRING message would have been sent by a neighbor
    # In response, you may send further routing messages using self.send_to_neighbors or self.send_to_neighbor.
    # You may also update your tables.

    def process_incoming_routing_message(self, m):
        json_object = json.loads(m)
        message_id = json_object["id"]
        message_seq_num = json_object["seq_num"]
        message_dv = json_object["dv"]
        # update the dv
        if message_seq_num > self.neighbor_info[message_id].seq_num:
            self.neighbor_info[message_id].dv = message_dv
            self.update_dv(message_id)  # TBD
            # update the sequence number the node associates with the neighbor
            # for every destination in the messages DV
            # if the destination is in the node's DV, see if it needs to be updated
            # if min{cost(x, m)+cost(m,y)>cost(x,y)} update DV
            # else, add a new entry in the DV for this destination
            self.send_to_neighbors(self.format_message)
        # else do nothing

        pass

    # Return a neighbor, -1 if no path to destination
    # Check routing table
    def get_next_hop(self, destination):
        if destination in self.dv:
            return self.dv[destination][1][0]
        else:
            return -1

    def format_message(self):
        json_message = {"id": self.id, "seq_num": self.seq_num, "dv": self.dv}
        return json.dumps(json_message)

    self.update_dv():
