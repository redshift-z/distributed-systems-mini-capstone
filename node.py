import logging
import pprint
import threading
import time
from pprint import pformat

from node_socket import UdpSocket

class Node:

    def __init__(self, my_id: int, my_port: int,
                 ports: list, node_socket: UdpSocket):
        self.my_id = my_id
        self.node_socket = node_socket
        self.my_port = my_port

        self.port_dictionary = {}
        for i in range(0, 4):
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

    def sending_procedure(self, sender, order):
        pass


class Client(Node):

    def __init__(self, my_id: int, my_port: int, ports: list, node_socket: UdpSocket):
        super().__init__(my_id, my_port, ports, node_socket)

    def sending_procedure(self, sender, order):
        pass

    def start(self):
        pass

class Server(Node):

    def __init__(self, my_id: int, my_port: int, ports: list, node_socket: UdpSocket):
        super().__init__(my_id, my_port, ports, node_socket)

    def sending_procedure(self, sender, order):
        pass

    def start(self):
        pass

def thread_exception_handler(args):
    logging.error(f"Uncaught exception", exc_info=(args.exc_type, args.exc_value, args.exc_traceback))


def main(node_id: int, ports: list, my_port: int = 0):
    threading.excepthook = thread_exception_handler
    try:
        if node_id == 0:
            obj = Client(my_id=node_id, node_socket=UdpSocket(my_port), my_port=my_port, ports=ports)
        elif node_id == 1:
            obj = Server(my_id=node_id, node_socket=UdpSocket(my_port), my_port=my_port, ports=ports)
        else:
            obj = Node(my_id=node_id, node_socket=UdpSocket(my_port), my_port=my_port, ports=ports)
        obj.start()
    except Exception:
        logging.exception("Caught Error")
        raise
