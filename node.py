import logging
import pprint
import threading
import time
import random
from pprint import pformat

from node_socket import UdpSocket

class Node:

    def __init__(self, my_id: int, my_port: int, ports: list, node_socket: UdpSocket, node_number: int):
        self.my_id = my_id
        self.node_socket = node_socket
        self.my_port = my_port
        self.node_number = node_number

        self.port_dictionary = {}
        for i in range(0, node_number):
            self.port_dictionary[i] = ports[i]
        logging.debug(f"self.port_dictionary: {pformat(self.port_dictionary)}")

        self.id_dictionary = {}
        for key, value in self.port_dictionary.items():
            self.id_dictionary[value] = key
        logging.debug(f"self.id_dictionary: {pprint.pformat(self.id_dictionary)}")

    def start(self):
        pass

    def listen_procedure(self):
        input_value, address = self.node_socket.listen()
        logging.debug(f"input_value: {input_value}")
        logging.debug(f"address: {address}")
        incoming_message: list = input_value.split("~")
        return incoming_message

    def sending_procedure(self, sender):
        pass


class Client(Node):

    def __init__(self, my_id: int, my_port: int, ports: list, node_socket: UdpSocket, node_number: int,
                  message: str, relay_number: int):
        super().__init__(my_id, my_port, ports, node_socket, node_number)
        self.message = message
        self.relay_number = relay_number

        self.avail_port_dictionary = {}
        for i in range (0, self.node_number):
            if i != self.my_id and i != 1:
                self.avail_port_dictionary[i] = ports[i]
        
        self.relay_node_dictionary = {}

    def sending_procedure(self, sender):
        pass

    def start(self):
        logging.info(f"Available nodes for relay: {pformat(self.avail_port_dictionary)}")
        logging.info("Randomly choosing relay nodes...")

        avail_nodes = list(self.avail_port_dictionary.keys())
        relay_nodes = random.sample(avail_nodes, self.relay_number)
        route_str = ""

        for node in relay_nodes:
            self.relay_node_dictionary[node] = self.avail_port_dictionary[node]
            route_str += f"Node {node} -- "

        logging.info(f"Route: Node 0 -- {route_str}Node 1")

class Server(Node):

    def __init__(self, my_id: int, my_port: int, ports: list, node_socket: UdpSocket, node_number: int, message: str):
        super().__init__(my_id, my_port, ports, node_socket, node_number)
        self.message = message

    def sending_procedure(self, sender):
        pass

    def start(self):
        pass

def thread_exception_handler(args):
    logging.error(f"Uncaught exception", exc_info=(args.exc_type, args.exc_value, args.exc_traceback))


def main(node_id: int, ports: list, my_port: int = 0, node_number: int = 0, message: str = None, relay_number: int = 0):
    threading.excepthook = thread_exception_handler
    try:
        if node_id == 0:
            obj = Client(my_id=node_id, node_socket=UdpSocket(my_port), my_port=my_port, ports=ports, node_number = node_number,
                         message=message, relay_number=relay_number)
        elif node_id == 1:
            obj = Server(my_id=node_id, node_socket=UdpSocket(my_port), my_port=my_port, ports=ports, node_number = node_number,
                         message=message)
        else:
            obj = Node(my_id=node_id, node_socket=UdpSocket(my_port), my_port=my_port, ports=ports, node_number = node_number)
        obj.start()
    except Exception:
        logging.exception("Caught Error")
        raise
