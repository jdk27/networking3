from simulator.node import Node
import json
import math


class Link_State_Node(Node):
    def __init__(self, id):
        super().__init__(id)
        self.graph_costs = {}

    # Return a string
    def __str__(self):
        return "Rewrite this function to define your node dump printout"

    # Fill in this function
    # Update the costs in our graph costs and then send the message to everyone
    def link_has_been_updated(self, neighbor, latency):
        # print('new node: ', neighbor)
        # latency = -1 if delete a link
        pair = frozenset([self.id,neighbor])

        seq_num = 1
        if pair in self.graph_costs:
            seq_num = self.graph_costs[pair][1] + 1
            self.graph_costs[pair] = [latency, seq_num]
        else:
            self.graph_costs[pair] = [latency, 1]


        # print('sending a new cost: ', latency)
        self.send_to_neighbors(self.format_message(self.id, neighbor,latency, seq_num))

        for pair in self.graph_costs:
            duo = []
            for element in pair:
                duo.append(element)
            # msg = self.format_message(int(duo[0]), int(duo[1]), int(self.graph_costs[pair][1]), int(self.graph_costs[pair][0]))
            self.send_to_neighbors(self.format_message(int(duo[0]), int(duo[1]), int(self.graph_costs[pair][1]), int(self.graph_costs[pair][0])))
            # print('New message: ', msg)
            # self.send_to_neighbors(json.dumps(msg))

    # Fill in this function
    # If new, update the costs in our graph costs and retransmit
    def process_incoming_routing_message(self, m):
        # print('my name is: ', self.id)
        try: 
            json_object = json.loads(m)
        except: 
            return
        # print('destination ahhh: ', type(json_object))
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
            # print('new pair baby: ', pair)
            self.graph_costs[pair] = [latency, new_seq]
            self.send_to_neighbors(json.dumps(json_object))


    # Return a neighbor, -1 if no path to destination
    # Run djikstra
    def get_next_hop(self, destination):
        return self.dijkstra(destination)

    def format_message(self, source, neighbor_id, latency, seq_num):
        json_message = {'source': int(source), 'destination' : neighbor_id,  'seq_num': seq_num, 'latency': latency }
        return json.dumps(json_message)

    def min_from_queue(self, q):
        min_val = math.inf
        min_element = 0
        for element in q:
            alt = q[element]
            if alt < min_val:
                min_val = alt
                min_element = element
        return min_element
    
    def dijkstra(self,destination):
        # for pair in self.graph_costs:
        #     print('pair: ', pair)
        #     print(self.graph_costs[pair])

        nodes = []
        neighbors = {}
        dist = {}
        prev = {}
        q = {}
        for pair in self.graph_costs:
            duo = []
            for element in pair:
                duo.append(element)
                if element not in nodes:
                    nodes.append(element)
            
            # print('here duo: ', duo)
            # print('here is neighbors so far: ', neighbors[duo[0]] )
            
            if duo[0] in neighbors: 
                neighbors[duo[0]] = neighbors[duo[0]] + [duo[1]]
            else: 
                neighbors[duo[0]] = [duo[1]]
            if duo[1] in neighbors: 
                neighbors[duo[1]] = neighbors[duo[1]] + [duo[0]]
            else:
                neighbors[duo[1]] = [duo[0]]
            # print('new neighbors: ', neighbors)


        print('All nodes: ', nodes)
        for node in nodes:
            dist[node] = math.inf
            prev[node] = -1
            q[node] = math.inf
        q[self.id] = 0
        dist[self.id] = 0

        while len(q) > 0:
            u = self.min_from_queue(q)
            # print('here is the Q: ', q)
            # print('Trying to delete: ', u)
            del q[u]

            print('here are all my neighbors: ', neighbors[u])
            for v in neighbors[u]:
                couple = frozenset([u, v])
                alt = dist[u] + self.graph_costs[couple][0]
                if alt < dist[v]:
                    dist[v] = alt
                    prev[v] = u
                    q[v] = alt
        print('Distances: ', dist)
        print('Previouses: ', prev)

        # returncle
        
        before = prev[destination]
        path = [destination]
        while before != -1:
            path = [before] + path
            before = prev[before]
        print('here is the path: ', path)
        return path[1]

