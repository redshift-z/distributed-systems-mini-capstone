import logging
import threading
from node import Node

class ServerNode(Node):

    def __init__(self, my_port: int, node_number: int):
        super().__init__(my_id=-1, my_port=my_port)

    def start(self):
        pass


def thread_exception_handler(args):
    logging.error(f"Uncaught exception", exc_info=(args.exc_type, args.exc_value, args.exc_traceback))

def main(my_port: int = 0, node_number: int = 0):
    threading.excepthook = thread_exception_handler
    try:
        obj = ServerNode(my_port=my_port, node_number=node_number)
        obj.start()
    except Exception:
        logging.exception("Caught Error")
        raise
