import logging
from pprint import pformat
import threading
from node import Node

class RelayNode(Node):
    def __init__(self, my_id: int, my_port: int, ports_of_nodes: list, node_number: int):
        super().__init__(my_id=my_id, my_port=my_port)
        self.node_number = node_number

        self.port_of_nodes_dictionary = {}
        for i in range(0, node_number):
            self.port_of_nodes_dictionary[i] = ports_of_nodes[i]
        logging.debug(f"self.port_of_nodes_dictionary: {pformat(self.port_of_nodes_dictionary)}")

    def start(self):
        pass


def thread_exception_handler(args):
    logging.error(f"Uncaught exception", exc_info=(args.exc_type, args.exc_value, args.exc_traceback))

def main(node_id: int, ports_of_nodes: list, my_port: int = 0, node_number: int = 0):
    threading.excepthook = thread_exception_handler
    try:
        obj = RelayNode(my_id=node_id, my_port=my_port, ports_of_nodes=ports_of_nodes, node_number=node_number)
        obj.start()
    except Exception:
        logging.exception("Caught Error")
        raise