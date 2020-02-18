import sys
import logging
import traceback
import time
import networkx as nx
import matplotlib.pyplot as plt

from simulator.config import *
from simulator.event import Event
from simulator.event_queue import Event_Queue


class Topology:

    Nodes = {}
    this = None

    def __init__(self, algorithm, step='NORMAL'):
        self.__g = nx.Graph()
        self.node_cls = ROUTE_ALGORITHM_NODE[algorithm]
        self.step = step
        self.logging = logging.getLogger('Sim')
        self.position = None
        self.message_count = 0
        self.print_count = 0
        Topology.Nodes = {}
        Topology.this = self

    def __str__(self):
        ans = ""
        for node in self.__g.nodes:
            ans += "node " + str(node) + ": "
            ans += str(self.__g[node])
            ans += "\n"
        return ans

    def add_node(self, node):
        if node not in Topology.Nodes.keys():
            self.position = None
            Topology.Nodes[node] = self.node_cls(node)
        self.__g.add_node(node)

    def add_link(self, node1, node2, latency):
        if latency < 0:
            sys.stderr.write("Latency of a link cannot be negative.")
            sys.exit(-1)
        self.add_node(node1)
        self.add_node(node2)
        self.__g.add_edge(node1, node2, latency = latency)
        self.post_send_link(node1, node2, latency)
        self.post_send_link(node2, node1, latency)

    def change_link(self, node1, node2, latency):
        self.add_link(node1, node2, latency)

    def send_link(self, node, neighbor, latency):
        if node not in Topology.Nodes:
            return
        Topology.Nodes[node].link_has_been_updated(neighbor, latency)

    def post_send_link(self, node, neighbor, latency):
        Event_Queue.Post(
            Event(
                Get_Time(),
                EVENT_TYPE.SEND_LINK,
                self,
                node,
                neighbor,
                latency
            )
        )

    def delete_link(self, node1, node2):
        if (node1, node2) in self.__g.edges:
            self.__g.remove_edge(node1, node2)
            self.post_send_link(node1, node2, -1)
            self.post_send_link(node2, node1, -1)
        else:
            self.logging.warning("remove link (%d, %d) does not exit" % (node1, node2))

    def delete_node(self, node):
        if node in self.__g.nodes:
            for neighbor in list(self.__g[node].keys()):
                self.delete_link(node, neighbor)
            self.__g.remove_node(node)
            Topology.Nodes.pop(node)
            self.position = None
            self.logging.debug("node %d deleted at time %d" % (node, Get_Time()))
        else:
            self.logging.warning("remove node %d does not exit" % node)

    def dump_node(self, node):
        if (node in self.__g.nodes) and (node in Topology.Nodes.keys()):
            self.logging.info('DUMP_NODE: ' + str(Topology.Nodes[node]))
        else:
            self.logging.warning("node %d does not exit" % node)

    def send_to_neighbors(self, node, m):
        for neighbor in list(self.__g[node].keys()):
            self.send_to_neighbor(node, neighbor, m)

    def send_to_neighbor(self, node, neighbor, m):
        if (node, neighbor) not in self.__g.edges:
            return
        Event_Queue.Post(
            Event(
                Get_Time() + int(self.__g[node][neighbor]['latency']),
                EVENT_TYPE.ROUTING_MESSAGE_ARRIVAL,
                self,
                neighbor,
                m
            )
        )

    def routing_message_arrival(self, neighbor, m):
        self.message_count += 1
        if neighbor in self.__g.nodes:
            Topology.Nodes[neighbor].process_incoming_routing_message(m)

    def node_labels(self):
        return {node : str(node) for node in self.__g.nodes}

    def edge_labels(self):
        return {(node1, node2) : self.__g[node1][node2]['latency'] for node1, node2 in self.__g.edges}

    def draw_topology(self):
        if self.position == None:
            self.position = nx.spring_layout(self.__g)
        nx.draw_networkx_nodes(self.__g, self.position, node_size=600, node_color='b', alpha=0.7)
        nx.draw_networkx_labels(self.__g, self.position, labels=self.node_labels(), font_size=14, font_color='w')
        nx.draw_networkx_edges(self.__g, self.position, width=2, alpha=0.5)
        nx.draw_networkx_edge_labels(self.__g, self.position, edge_labels=self.edge_labels(), font_size=14)
        plt.axis('off')

        filename = 'Topo_' + time.strftime("%H_%M_%S", time.localtime()) + '_Count_' + str(self.print_count) + '_Time_' + str(Get_Time()) + '.png'
        self.print_count += 1
        plt.savefig(OUTPUT_PATH + filename) # call savefig before show
        plt.show()
        plt.close(OUTPUT_PATH + filename)
        self.wait()

    def get_correct_path(self, source, destination):
        try:
            shortest_path = nx.algorithms.shortest_path(self.__g, source=source, target=destination, weight='latency')
        except:
            self.logging.warning("No path from %d to %d, please correct event/topo file" % (source, destination))
            return None

        correct_path = []
        for i in range(len(shortest_path) - 1):
            correct_path.append((shortest_path[i], shortest_path[i + 1]))
        return correct_path

    def get_tree_correct_path(self, source):
        try:
            shortest_tree = nx.algorithms.shortest_path(self.__g, source=source, weight='latency')
        except:
            self.logging.warning("No Tree from %d, please correct event/topo file" % source)
            return None

        correct_path_set = set()
        for s in shortest_tree.keys():
            if s == source:
                continue
            for i in range(len(shortest_tree[s]) -1):
                correct_path_set.add((shortest_tree[s][i], shortest_tree[s][i + 1]))

        destination_list = list(shortest_tree.keys())
        destination_list.remove(source)

        return list(correct_path_set), destination_list

    def get_user_path(self, source, destination):
        path = [source]

        while destination not in path:
            next = Topology.Nodes[path[-1]].get_next_hop(destination)
            if next == None:
                self.logging.warning("Your algorithm cannot find a path from %d to %d. Output: %s." % (source, destination, str(path)))
                return None
            elif next == -1 or next not in self.__g.nodes or next in path:
                path.append(next)
                self.logging.warning(
                    "Your algorithm cannot find a path from %d to %d. Output: %s." % (source, destination, str(path)))
                return None
            path.append(next)

        user_path = []
        for i in range(len(path) - 1):
            if (path[i], path[i + 1]) not in self.__g.edges:
                self.logging.warning("Link from %d to %d does not exists, you cannot use it" % (path[i], path[i + 1]))
                return None
            user_path.append((path[i], path[i + 1]))
        return  user_path

    def get_tree_user_path(self, source, destination_list):
        user_path_set = set()
        solved_destination_set = set()
        for d in destination_list:
            if d in solved_destination_set:
                continue
            path_for_d = self.get_user_path(source, d)
            if path_for_d == None or path_for_d == []:
                self.logging.warning("Your algorithm cannot find a path from %d to %d." % (source, d))
            else:
                for p in path_for_d:
                    user_path_set.add(p)
                    solved_destination_set.add(p[1])

        return list(user_path_set)

    def draw_path(self, source, destination):
        if (source not in self.__g.nodes) or  (destination not in self.__g.nodes) or (source == destination):
            self.logging.warning("Parameters in DRAW_PATH are illegal.")
            return

        correct_path = self.get_correct_path(source, destination)
        if correct_path == None:
            return

        user_path = self.get_user_path(source, destination)

        red_nodes = [source, destination]
        blue_nodes = list(self.__g.nodes)
        for node in red_nodes:
            blue_nodes.remove(node)

        self.draw_in_networkx(red_nodes, blue_nodes, correct_path, user_path)

    def draw_tree(self, source):
        if source not in self.__g.nodes:
            self.logging.warning("Parameter in DRAW_TREE is illegal.")
            return

        correct_path, destination_list = self.get_tree_correct_path(source)
        if correct_path == None or correct_path == []:
            return

        user_path = self.get_tree_user_path(source, destination_list)
        red_nodes = [source]
        blue_nodes = list(self.__g.nodes)
        blue_nodes.remove(source)

        self.draw_in_networkx(red_nodes, blue_nodes, correct_path, user_path)

    def draw_in_networkx(self, red_nodes, blue_nodes, correct_path, user_path):
        if self.position == None:
            self.position = nx.spring_layout(self.__g)
            
        print("correct_path: " + str(correct_path))
        print("student_path: " + str(user_path))

        nx.draw_networkx_nodes(self.__g, self.position, nodelist=blue_nodes, node_size=600, node_color='b', alpha=0.7)
        nx.draw_networkx_nodes(self.__g, self.position, nodelist=red_nodes, node_size=700, node_color='r', alpha=0.6)
        nx.draw_networkx_labels(self.__g, self.position, labels=self.node_labels(), font_size=14, font_color='w')

        nx.draw_networkx_edges(self.__g, self.position, width=2, alpha=0.5)
        if user_path != None:
            nx.draw_networkx_edges(self.__g, self.position, edgelist=user_path, width=6, edge_color='r', alpha=0.4)
        nx.draw_networkx_edges(self.__g, self.position, edgelist=correct_path, width=3, edge_color='g', alpha=0.8)
        nx.draw_networkx_edge_labels(self.__g, self.position, edge_labels=self.edge_labels(), font_size=14)
        plt.axis('off')

        filename = 'Topo_' + time.strftime("%H_%M_%S", time.localtime()) + '_Count_' + str(self.print_count) + '_Time_' + str(Get_Time()) + '.png'
        self.print_count += 1
        plt.savefig(OUTPUT_PATH + filename)  # call savefig before show
        plt.show()
        plt.close(OUTPUT_PATH + filename)
        self.wait()

    def wait(self):
        if self.step == 'NO_STOP':
            return
        input('Press Enter to Continue...')

    def load_command_file(self, file):
        try:
            f = open(file)
            for line in f.readlines():
                line = line.strip()
                if line == "" or line[0] == '#':
                    continue

                items = line.split(' ')
                time_stamp = int(items[0])
                event_type = items[1]

                num_args = len(items) - 2
                if event_type == EVENT_TYPE.PRINT:
                    Event_Queue.Post(Event(time_stamp, event_type, self, "".join(items[2:])))
                elif num_args < 0 or num_args > 3:
                    sys.stderr.write(line)
                    raise BufferError
                elif num_args == 0:
                    Event_Queue.Post(Event(time_stamp, event_type, self))
                elif num_args == 1:
                    Event_Queue.Post(Event(time_stamp, event_type, self, int(items[2])))
                elif num_args == 2:
                    Event_Queue.Post(Event(time_stamp, event_type, self, int(items[2]), int(items[3])))
                elif num_args == 3:
                    Event_Queue.Post(Event(time_stamp, event_type, self, int(items[2]), int(items[3]), int(items[4])))
            f.close()

        except IOError as e:
            print("Can not open file " + file)
            print(e)
            sys.exit(-1)

        except BufferError:
            print("File with wrong format " + file)
            sys.exit(-1)

        except Exception as e:
            print("File with wrong format " + file)
            print(e)
            traceback.print_exc()
            sys.exit(-1)


def Send_To_Neighbors(node, m):
    Topology.this.send_to_neighbors(node.id, m)

def Send_To_Neighbor(node, neighbor, m):
    Topology.this.send_to_neighbor(node.id, neighbor, m)

def Get_Time():
    return Event_Queue.Current_Time
