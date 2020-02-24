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
    # Use bellman ford here! maybe?

    # Need to keep track of when we changed DV to increase seq num and resend to everyone
    
    # Return a string
    def __str__(self):
        return "\r\n" + "Node ID: " + str(self.id) + "\r\n" + \
            "Distance Vector: " + json.dumps(self.dv) + "\r\n"

        # Make way to print out neighbor DV TOO!

    # Receives a new link cost then updates self.costs and self.dv given the new information
    # Then calls to recalculate optimal DV using bellman-ford
    def link_has_been_updated(self, neighbor, latency):
        # print ('ahhhh', str(self))
        print('wwwwww', str(self.dv))
        neighbor_change = False
        bellman_change = False

        if latency == -1:  # delete a link
            # Probably not but maybe we send?
            if neighbor in self.neighbor_info:
                neighbor_change = self.remove_link(neighbor)
        elif neighbor in self.neighbor_info:  # update a link 
            neighbor_change = self.update_link_latency(neighbor, latency)
        else:  # create a link
            # Probably not, but idk
            neighbor_change = self.create_link(neighbor, latency)
        # Check for short paths
        bellman_change = self.bellman_ford()
        # if bellman_change or neighbor_change: update sequence number and self.send_to_neighbors(self.format_message())
        if bellman_change or neighbor_change:
            self.seq_num += 1
            # print('link link link')
            self.send_to_neighbors(self.format_message())

    def remove_link(self, neighbor_id):
        change = False
        del self.neighbor_info[neighbor_id]
        for destination in self.dv:
            if self.dv[destination][1][0] == neighbor_id:
                del self.dv[destination]
                change = True
        return change

    # FIX: need to fix the path to the neighbor whose latency was updated
    def update_link_latency(self, neighbor_id, new_latency):
        change = False
        length_change = new_latency - self.neighbor_info[neighbor_id].latency
        self.neighbor_info[neighbor_id].latency = new_latency
        for destination in self.dv:
            if (destination == neighbor_id) and (new_latency <= self.dv[destination][0]):
                self.dv[str(destination)] = [new_latency,[neighbor_id]]
                change = True
            elif (len(self.dv[destination][1]) != 0) and (self.dv[destination][1][0] == neighbor_id):
                self.dv[destination][0] += length_change
                change = True
        return change

    def create_link(self, neighbor_id, latency):
        change = False
        new_neighbor = self.Neighbor(neighbor_id, 0, latency, {})
        self.neighbor_info[neighbor_id] = new_neighbor
        # if there is no path to the new neighbor
        if neighbor_id not in self.dv:
            self.dv[str(neighbor_id)] = [latency, [neighbor_id]]
            change = True
        # if there was already a path to the neighbor and the one-hop cost is cheaper than the older path
        elif self.neighbor_info[neighbor_id].latency < self.dv[neighbor_id][0]:
            self.dv[str(neighbor_id)] = [latency, [neighbor_id]]
            change = True
        return change

    # Given a new neighbor DV, update self.dv
    # Then call to optimize self.dv with bellman-ford
    def process_incoming_routing_message(self, m):
        # print('here we areeee', type(m))
        # print('check this too: ', m)
        try: 
            json_object = json.loads(m)
        except: 
            return
        message_id = json_object["id"]
        message_seq_num = json_object["seq_num"]
        message_dv = json_object["dv"]
        # update the dv
        if message_seq_num > self.neighbor_info[message_id].seq_num:
            change = False
            bellman_change = False

            self.neighbor_info[message_id].dv = message_dv
            self.neighbor_info[message_id].seq_num = message_seq_num
            
            # Need to first update self.dv costs
            change = self.update_personal_dv(message_id)
            # Then check for optimal
            
            bellman_change = self.bellman_ford()  # TBD updates using bellman-ford

            # update the sequence number the node associates with the neighbor
            # for every destination in the messages DV
            # if the destination is in the node's DV, see if it needs to be updated
            # if min{cost(x, m)+cost(m,y)>cost(x,y)} update DV
            # else, add a new entry in the DV for this destination
            if change or bellman_change:
                self.seq_num += 1
                # print('got a message sending something out!!')
                self.send_to_neighbors(self.format_message)
        # else do nothing the information is old
        pass

    # Return a neighbor, -1 if no path to destination
    # Check routing table
    def get_next_hop(self, destination):
        self.bellman_ford
        print ('ahhhh', str(self))
        if destination in self.dv:
            return self.dv[destination][1][0]
        else:
            return -1

    def format_message(self):
        json_message = {"id": self.id, "seq_num": self.seq_num, "dv": self.dv}
        return json.dumps(json_message)

    def update_personal_dv(self, neighbor_id):
        latency = self.neighbor_info[neighbor_id].latency
        change = False
        for destination in self.neighbor_info[neighbor_id].dv:
            new_latency = latency + self.neighbor_info[neighbor_id].dv[destination][0]
            new_path = [neighbor_id] + self.neighbor_info[neighbor_id].dv[destination][1] # Will this just append to the front??????
            if destination in self.dv:
                # print ('ahhhh', str(self))
                if (len(self.dv[destination][1]) != 0) and (self.dv[destination][1][0] == neighbor_id):
                    self.dv[destination] = [new_latency, new_path]
                    change = True
            else:
                self.dv[destination] = [new_latency, new_path]
                change = True
        return change


    # Distributed bellman ford to find any shorter paths
    def bellman_ford(self):
        change = False
        for destination in self.dv:
            old_latency = self.dv[destination][0]
            for neighbor_id in self.neighbor_info:
                neighbor = self.neighbor_info[neighbor_id]
                if destination in neighbor.dv:
                    new_latency = neighbor.latency + neighbor.dv[destination][0]
                    if new_latency < old_latency:
                        self.dv[destination] = [new_latency, [neighbor.id] + neighbor.dv[destination][1]] # Will this just append to the front??????
                        change = True
        return change
