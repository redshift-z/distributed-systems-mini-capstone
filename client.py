import logging
from pprint import pformat
import random
import threading
from node import Node

class ClientNode(Node):

    def __init__(self, my_port: int, node_and_port_dict: dict):
        super().__init__(my_id=-1, my_port=my_port)
        self.node_and_port_dict = node_and_port_dict

    def start(self):
        logging.info(f"Available nodes for relay: {pformat(self.node_and_port_dict)}")
        circuit_len = int(input("Total relay node to build a circuit (int): "))

        logging.info(f"Building a circuit with {circuit_len} nodes")
        random_node_id_list = random.sample(self.node_and_port_dict.keys(), circuit_len)
        circuit_dict = {key: self.node_and_port_dict[key] for key in random_node_id_list}

        route_str = ""
        for relay_id in circuit_dict.keys():
            route_str += f"Relay {relay_id} -- "
        logging.info(f"Route: Client -- {route_str}Server")

def thread_exception_handler(args):
    logging.error(f"Uncaught exception", exc_info=(args.exc_type, args.exc_value, args.exc_traceback))

def main(my_port: int = 0, node_and_port_dict: dict = dict()):
    threading.excepthook = thread_exception_handler
    try:
        obj = ClientNode(my_port=my_port, node_and_port_dict=node_and_port_dict)
        obj.start()
    except Exception:
        logging.exception("Caught Error")
        raise
