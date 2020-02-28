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
    
    def print_neighbor_dvs(self):
        print('Get ready for neighbors of : ', self.id)
        for neighbor_id in self.neighbor_info:
            print('Neighbor ID: ', neighbor_id)
            print(json.dumps(self.neighbor_info[str(neighbor_id)].dv))
        print('Done with neighbors')
    
    # Return a string
    def __str__(self):
        return "\r\n" + "Node ID: " + str(self.id) + "\r\n" + \
            "Distance Vector: " + json.dumps(self.dv) + "Seq Num: " + str(self.id) + "\r\n"

    # NEED A CHECK FOR LOOPS I THINK
    # Receives a new link cost then updates self.costs and self.dv given the new information
    # Then calls to recalculate optimal DV using bellman-ford
    def link_has_been_updated(self, neighbor, latency):
        neighbor_change = False
        bellman_change = False

        # Removing a link to a neighbor
        if latency == -1:
            if neighbor in self.neighbor_info:
                neighbor_change = self.remove_link(neighbor)
        # Updating the latency to a neighbor
        elif str(neighbor) in self.neighbor_info: 
            print('Do we already have this neighbor???')
            neighbor_change = self.update_link_latency(neighbor, latency)
        # We have a new linnk
        else:
            neighbor_change = self.create_link(neighbor, latency)

        
        print('The DV before bellman-ford: ', self.dv)
        # Now that we have updated various costs, we check if our DV can be optimized with other routes
        bellman_change = self.bellman_ford()

        # If the DV was updated we sent out the new one to all of our neighbors
        if bellman_change or neighbor_change:
            self.seq_num += 1
            # print('We sent a message!')
            print('The DV we sent: ', self.dv)
            self.send_to_neighbors(self.format_message())


    # Remove from our neighbor info and if any destination in our DV us it as a 
    # first hope, then delete those from the DV at the moment
    def remove_link(self, neighbor_id):
        change = False
        deleted = []
        del self.neighbor_info[str(neighbor_id)]
        for destination in self.dv:
            if (len(self.dv[str(destination)][1]) != 0) and (self.dv[str(destination)][1][0] == neighbor_id):
                deleted.append(destination)
                # del self.dv[destination]
                change = True
        for dest in deleted:
            del self.dv[str(dest)]
        return change

    # FIX: need to fix the path to the neighbor whose latency was updated. Actually i don't think so
    # If the node is used as the first hop, no matter what update the link. 
    # We will then have to check for shorter paths later
    def update_link_latency(self, neighbor_id, new_latency):
        change = False
        length_change = new_latency - self.neighbor_info[str(neighbor_id)].latency
        self.neighbor_info[str(neighbor_id)].latency = new_latency
        print('updating the link latency to: ', new_latency)

        # If a destination used the new link as the first hop, update to the new total latency
        # Will check for better option later
        for destination in self.dv:
            if (len(self.dv[str(destination)][1]) != 0) and (self.dv[str(destination)][1][0] == neighbor_id):
                print('shouldnt we have made a fucking change? ', length_change)
                self.dv[str(destination)][0] += length_change
                print('so what did we do? ', self.dv)
                change = True
        return change



    # We may update costs but not the dv... do we still make a change?
    def create_link(self, neighbor_id, latency):
        change = False
        new_neighbor = self.Neighbor(neighbor_id, 0, latency, {})
        self.neighbor_info[str(neighbor_id)] = new_neighbor
        
        # If we do not have a path to the neighbor, add it
        if neighbor_id not in self.dv:
            self.dv[str(neighbor_id)] = [latency, [neighbor_id]]
            change = True
        # If there is a path, check if this one hop is cheaper and update the node's DV
        elif self.neighbor_info[str(neighbor_id)].latency < self.dv[str(neighbor_id)][0]:
            self.dv[str(neighbor_id)] = [latency, [neighbor_id]]
            change = True
        return change


    # Given a new neighbor DV, update self.dv
    # Then call to optimize self.dv with bellman-ford
    def process_incoming_routing_message(self, m):
        # Load the message
        try: 
            json_object = json.loads(m)
        except: 
            return
        message_id = json_object["id"]
        message_seq_num = json_object["seq_num"]
        message_dv = json_object["dv"]

        # If this is indeed a new message then we will use it
        if message_seq_num > self.neighbor_info[str(message_id)].seq_num:
            change = False
            bellman_change = False

            # Update the DV we have saved for this neighbor
            self.neighbor_info[str(message_id)].dv = message_dv
            self.neighbor_info[str(message_id)].seq_num = message_seq_num
            
            # Update our costs based on the new neighbor DV
            change = self.update_personal_dv(message_id)
            
            # Check all neighbor DVs to see if there are better options
            bellman_change = self.bellman_ford()

            # If our DV has changed, send it to our neighbors
            if change or bellman_change:
                self.seq_num += 1
                # print('got a message sending something out!!')
                self.send_to_neighbors(self.format_message)
        # else do nothing the information is old
        else: 
            pass


    # Return a neighbor, -1 if no path to destination
    # Check routing table
    def get_next_hop(self, destination):
        print('Jeez what is the dv: ', self.dv)
        self.bellman_ford()
        if str(destination) in self.dv or destination in self.dv:
            return int(self.dv[str(destination)][1][0])
        else:
            print('ohhh no')
            return -1

    def format_message(self):
        json_message = {"id": self.id, "seq_num": self.seq_num, "dv": self.dv}
        return json.dumps(json_message)

    # When receiving a new message, update any latencies or paths for destinations that use
    # that neighbor as the first hop
    # We will then check all other DVs to check for optimizations
    def update_personal_dv(self, neighbor_id):
        latency = self.neighbor_info[str(neighbor_id)].latency
        change = False

        for destination in self.dv:
            if (len(self.dv[str(destination)][1]) != 0) and (self.dv[str(destination)][1][0] == neighbor_id):
                # Is the path different?
                # Or if latency is now smaller or greater
                if(self.dv[str(destination)][1][1:] != self.neighbor_info[str(neighbor_id)].dv[str(destination)][1]):
                    self.print_neighbor_dvs()
                    new_path = [neighbor_id] + self.neighbor_info[str(neighbor_id)].dv[str(destination)][1]
                    self.dv[str(destination)] = [latency + self.neighbor_info[str(neighbor_id)].dv[str(destination)][0], new_path]
                    change = True

        return change

        # deleted = []

        # for destination in self.dv:
        #     # If the first hop in our DV is the neighbor associated with the message:
        #     if (len(self.dv[str(destination)][1]) != 0) and (self.dv[str(destination)][1][0] == neighbor_id): 
        #         print('Our path: ', self.dv[str(destination)][1])
        #         print('from : ', self.id)
        #         # Check if that destination was removed from the neighbor DV 
        #         # and should be removed from ours as well
        #         if destination not in self.neighbor_info[str(neighbor_id)].dv:
        #             deleted.append(destination)
        #             change = True
        #             continue
                
        #         # If the path is different, update our corresponding path
        #         print('Their path: ', self.neighbor_info[str(neighbor_id)].dv[str(destination)])
        #         if (self.dv[str(destination)][1][1:] != self.neighbor_info[str(neighbor_id)].dv[str(destination)][1]):
        #             new_path = [neighbor_id] + self.neighbor_info[str(neighbor_id)].dv[str(destination)][1]
        #             self.dv[str(destination)] = [latency + self.neighbor_info[str(neighbor_id)].dv[str(destination)][0], new_path]
        #             change = True
                
        #         # If the paths are the same but new cost, just update costs
        #         elif (self.dv[str(destination)][0]) != (latency + self.neighbor_info[str(neighbor_id)].dv[str(destination)][0]):
        #             self.dv[str(destination)] = [latency + self.neighbor_info[str(neighbor_id)].dv[str(destination)][0], self.dv[str(destination)][1]] # Should be right path?
        #             change = True
        
        # for destination in deleted:
        #     del self.dv[str(destination)]
        # return change


    # Distributed bellman ford to find any shorter paths
    # are we adding new destinations from our neighbor?
    def bellman_ford(self):
        change = False

        # for n in self.neighbor_info:
        #     n = self.neighbor_info[n]
        #     print('Cost of neighbor ' + str(n.id) + 'is ' + str(n.latency))

        # For all destinations in our neighbor DVs, see if there are any better paths
        for neighbor_id in self.neighbor_info:
            for destination in self.neighbor_info[str(neighbor_id)].dv:
                neighbor = self.neighbor_info[str(neighbor_id)]
                
                # print('Here is the DV ', self.dv)
                # print('looking for: ', neighbor_id)
                # print('Here is the DV row of neighbor as dest', self.dv[str(neighbor_id)])
                # print('Here is the neighbor: ', neighbor_id)
                # print('neighbor shit working? ', neighbor.dv[str(destination)][0])
                
                new_latency = self.dv[str(neighbor_id)][0] + neighbor.dv[str(destination)][0]
                new_path = neighbor.dv[str(destination)][1]
                
                # If self node is present in path, this is a loop and skip
                if self.id in new_path:
                    continue
                else:
                    new_path = [neighbor_id] + new_path
                    
                    # If we don't have the destination, add it to our DV
                    if destination not in self.dv:
                        self.dv[str(destination)] = [new_latency, new_path]
                        change = True
                    else:
                        
                        old_latency = self.dv[str(destination)][0]
                        if old_latency == 100: print('ahhhhh')
                        if new_latency < old_latency:
                            self.dv[str(destination)] = [new_latency, new_path]  
                            change = True 

        # Checking if any single hops are better paths than what was found in DV
        for neighbor_id in self.neighbor_info:
            neighbor = self.neighbor_info[str(neighbor_id)]
            new_latency = neighbor.latency
            if neighbor_id not in self.dv:
                self.dv[str(neighbor_id)] = [new_latency, [neighbor_id]]
                change = True
            else:
                old_latency = self.dv[str(neighbor_id)][0]
                if new_latency < old_latency:
                    self.dv[str(neighbor_id)] = [new_latency, [neighbor_id]]  
                    change = True 

        return change



        
