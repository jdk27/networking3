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
            self.id = str(id)
            self.seq_num = seq_num
            self.latency = latency
            self.dv = dv

    # Return a string
    def __str__(self):
        return "\r\n" + "Node ID: " + str(self.id) + "\r\n" + \
            "Distance Vector: " + \
            json.dumps(self.dv) + "Seq Num: " + str(self.seq_num) + "\r\n"

    # Receives a new link cost then updates self.costs and self.dv given the new information
    # Then calls to recalculate optimal DV using bellman-ford
    def link_has_been_updated(self, neighbor, latency):
        neighbor_change = False
        bellman_change = False

        neighbor = str(neighbor)
        # Removing a link to a neighbor
        if latency == -1:
            if neighbor in self.neighbor_info:
                neighbor_change = self.remove_link(neighbor)
        # Updating the latency to a neighbor
        elif neighbor in self.neighbor_info:
            neighbor_change = self.update_link_latency(neighbor, latency)
        # We have a new linnk
        else:
            neighbor_change = self.create_link(neighbor, latency)

        # Now that we have updated various costs, we check if our DV can be optimized with other routes
        bellman_change = self.bellman_ford()

        # If the DV was updated we sent out the new one to all of our neighbors
        if bellman_change or neighbor_change:
            self.seq_num += 1
            self.send_to_neighbors(self.format_message())

    # Remove from our neighbor info and if any destination in our DV us it as a
    # first hope, then delete those from the DV at the moment

    def remove_link(self, neighbor_id):
        change = False
        deleted = []
        del self.neighbor_info[neighbor_id]
        for destination in self.dv:
            if (len(self.dv[destination][1]) != 0) and (self.dv[destination][1][0] == neighbor_id):
                deleted.append(destination)
                change = True
        for dest in deleted:
            if dest in self.neighbor_info:
                self.dv[dest] = [self.neighbor_info[dest].latency, [dest]]
            else:
                del self.dv[dest]
        return change

    # FIX: need to fix the path to the neighbor whose latency was updated. Actually i don't think so
    # If the node is used as the first hop, no matter what update the link.
    # We will then have to check for shorter paths later
    def update_link_latency(self, neighbor_id, new_latency):
        change = False
        length_change = new_latency - self.neighbor_info[neighbor_id].latency
        self.neighbor_info[neighbor_id].latency = new_latency

        # If a destination used the new link as the first hop, update to the new total latency
        # Will check for better option later
        for destination in self.dv:
            if (len(self.dv[destination][1]) != 0) and (self.dv[destination][1][0] == neighbor_id):
                self.dv[destination][0] += length_change
                change = True
        return change

    # We may update costs but not the dv... do we still make a change?

    def create_link(self, neighbor_id, latency):
        change = False
        new_neighbor = self.Neighbor(neighbor_id, 0, latency, {})
        self.neighbor_info[neighbor_id] = new_neighbor

        # If we do not have a path to the neighbor, add it
        if neighbor_id not in self.dv:
            self.dv[neighbor_id] = [latency, [neighbor_id]]
            change = True
        # If there is a path, check if this one hop is cheaper and update the node's DV
        elif self.neighbor_info[neighbor_id].latency < self.dv[neighbor_id][0]:
            self.dv[neighbor_id] = [latency, [neighbor_id]]
            change = True
        return change

    # Given a new neighbor DV, update self.dv
    # Then call to optimize self.dv with bellman-ford

    def process_incoming_routing_message(self, m):
        # Load the message
        json_object = json.loads(m)
        message_id = str(json_object["id"])
        message_seq_num = json_object["seq_num"]
        message_dv = json_object["dv"]

        # If this message is from a node that's still our neighbor and it's a new message from that neighbor
        if (str(message_id) in list(self.neighbor_info.keys())) and (message_seq_num > self.neighbor_info[message_id].seq_num):
            change = False
            bellman_change = False

            # Update the DV we have saved for this neighbor
            self.neighbor_info[message_id].dv = message_dv
            self.neighbor_info[message_id].seq_num = message_seq_num

            # Update our costs based on the new neighbor DV
            change = self.update_personal_dv(message_id)

            # Check all neighbor DVs to see if there are better options
            bellman_change = self.bellman_ford()

            # If our DV has changed, send it to our neighbors
            if change or bellman_change:
                self.seq_num += 1
                self.send_to_neighbors(self.format_message())
        # else do nothing the information is old
        else:
            pass

    def get_next_hop(self, destination):
        destination = str(destination)
        self.bellman_ford()
        if destination in self.dv or destination in self.dv:
            return int(self.dv[destination][1][0])
        else:
            return -1

    def format_message(self):
        json_message = {"id": self.id, "seq_num": self.seq_num, "dv": self.dv}
        return json.dumps(json_message)

    # When receiving a new message, update any latencies or paths for destinations that use
    # that neighbor as the first hop
    # We will then check all other DVs to check for optimizations
    def update_personal_dv(self, neighbor_id):
        latency = self.neighbor_info[neighbor_id].latency
        change = False
        deleted = []

        for destination in self.dv:
            # if the neighbor is the first hop in a path
            if (len(self.dv[destination][1]) != 0) and (self.dv[destination][1][0] == neighbor_id):
                # if the destination is still reachable going through the neighbor
                if destination in self.neighbor_info[neighbor_id].dv:
                    # if the neighbor's path to the destination matches what we have
                    if(self.dv[destination][1][1:] != self.neighbor_info[neighbor_id].dv[destination][1]):
                        new_path = [neighbor_id] + \
                            self.neighbor_info[neighbor_id].dv[destination][1]
                        self.dv[destination] = [
                            latency + self.neighbor_info[neighbor_id].dv[destination][0], new_path]
                        change = True
                else:
                    deleted.append(destination)
        for destination in deleted:
            del self.dv[destination]

        return change

    def bellman_ford(self):
        change = False

        # For all destinations in our neighbor DVs, see if there are any better paths

        for neighbor_id in self.neighbor_info:
            for destination in self.neighbor_info[neighbor_id].dv:
                neighbor = self.neighbor_info[neighbor_id]

                new_latency = self.dv[neighbor_id][0] + \
                    neighbor.dv[destination][0]
                new_path = self.dv[neighbor_id][1] + \
                    neighbor.dv[destination][1]

                # If self node is present in path, this is a loop and skip
                if self.id in new_path:
                    continue
                else:
                    # new_path = [neighbor_id] + new_path

                    # If we don't have the destination, add it to our DV
                    if destination not in self.dv:
                        self.dv[destination] = [new_latency, new_path]
                        change = True
                    else:
                        old_latency = self.dv[destination][0]
                        if new_latency < old_latency:
                            self.dv[destination] = [new_latency, new_path]
                            change = True

        # Checking if any single hops are better paths than what was found in DV
        # for neighbor_id in self.neighbor_info:
        #     neighbor = self.neighbor_info[neighbor_id]
        #     new_latency = neighbor.latency
        #     if neighbor_id not in self.dv:
        #         self.dv[neighbor_id] = [new_latency, [neighbor_id]]
        #         change = True
        #     else:
        #         old_latency = self.dv[neighbor_id][0]
        #         if new_latency < old_latency:
        #             self.dv[neighbor_id] = [new_latency, [neighbor_id]]
        #             change = True

        return change
