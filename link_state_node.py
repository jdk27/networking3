from simulator.node import Node
import json


# I don't think this works when paths are deleted!!!!!
# why is it not doing the last one?
class Link_State_Node(Node):
    def __init__(self, id):
        super().__init__(id)
        self.graph_costs = {}

    # Return a string. FIX THIS
    def __str__(self):
        latencies = str(self.graph_costs)
        return "\r\n" + "Node ID: " + str(self.id) + "\r\n" + "Costs: " + latencies + "\r\n"

    # Fill in this function
    # Update the costs in our graph costs and then send the message to everyone
    def link_has_been_updated(self, neighbor, latency):
        # print('new node: ', neighbor)
        # latency = -1 if delete a link
        pair = frozenset([self.id,neighbor])

        # if latency == -1:
        #     print('time to delete a node!! ')
        seq_num = 1
        if pair in self.graph_costs:
            seq_num = self.graph_costs[pair][1] + 1
            self.graph_costs[pair] = [latency, seq_num]
        else:
            self.graph_costs[pair] = [latency, 1]

        self.send_to_neighbors(self.format_message(self.id, neighbor,latency, seq_num))

        # Sending everything over to keep everyone up to date if they are new :)
        for pair in self.graph_costs:
            duo = []
            for element in pair:
                duo.append(element)
            self.send_to_neighbors(self.format_message(int(duo[0]), int(duo[1]), int(self.graph_costs[pair][0]), int(self.graph_costs[pair][1])))


    # Fill in this function
    # If new, update the costs in our graph costs and retransmit
    def process_incoming_routing_message(self, m):
        try: 
            json_object = json.loads(m)
        except: 
            return
        source = json_object["source"]
        destination = json_object["destination"]
        latency = json_object["latency"]
        new_seq = json_object["seq_num"]


        pair = frozenset([source, destination])

        if pair in self.graph_costs:
            old_seq = self.graph_costs[pair][1]
            if new_seq > old_seq:
                self.graph_costs[pair] = [latency, new_seq]
                self.send_to_neighbors(json.dumps(json_object))
        else:
            self.graph_costs[pair] = [latency, new_seq]
            self.send_to_neighbors(json.dumps(json_object))


    # Return a neighbor, -1 if no path to destination
    # Run djikstra
    def get_next_hop(self, destination):
        next_hop = self.dijkstra(destination)

        return next_hop

    def format_message(self, source, neighbor_id, latency, seq_num):
        json_message = {'source': int(source), 'destination' : neighbor_id,  'seq_num': seq_num, 'latency': latency }
        return json.dumps(json_message)

    def min_from_queue(self, q):
        min_val = float('inf')
        min_element = -1
        for element in q:
            alt = q[element]
            if alt < min_val:
                min_val = alt
                min_element = element
        return min_element
    
    def dijkstra(self,destination):
        nodes = []
        neighbors = {}
        dist = {}
        prev = {}
        q = {}
        for pair in self.graph_costs:
            duo = []
            if self.graph_costs[pair][0] != -1:
                for element in pair:
                    duo.append(element)
                    if element not in nodes:
                        nodes.append(element)
                
                if duo[0] in neighbors: 
                    neighbors[duo[0]] = neighbors[duo[0]] + [duo[1]]
                else: 
                    neighbors[duo[0]] = [duo[1]]
                if duo[1] in neighbors: 
                    neighbors[duo[1]] = neighbors[duo[1]] + [duo[0]]
                else:
                    neighbors[duo[1]] = [duo[0]]

        for node in nodes:
            dist[node] = float('inf')
            prev[node] = -1
            q[node] = float('inf')
        q[self.id] = 0
        dist[self.id] = 0

        while len(q) > 0:
            u = self.min_from_queue(q)
            del q[u]

            for v in neighbors[u]:
                couple = frozenset([u, v])
                if self.graph_costs[couple][0] != -1:
                    alt = dist[u] + self.graph_costs[couple][0]
                    if alt < dist[v]:
                        dist[v] = alt
                        prev[v] = u
                        q[v] = alt
        
        before = prev[destination]
        path = [destination]
        while before != -1:
            path = [before] + path
            before = prev[before]
        return path[1]

