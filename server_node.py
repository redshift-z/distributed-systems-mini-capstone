import json
import logging
import threading
from pprint import pformat
from node import Node

class ServerNode(Node):

    def __init__(self, my_port: int, node_number: int):
        super().__init__(my_id=-1, my_port=my_port)

    def start(self):
        logging.info("Listening for request...")
        inbound_message_json = self.listen_procedure()
        inbound_message = json.loads(inbound_message_json)
        data = inbound_message["data"]
        logging.info(f"Request message: {pformat(data)}")
    
    def send_response(self):
        pass


def thread_exception_handler(args):
    logging.error(f"Uncaught exception", exc_info=(args.exc_type, args.exc_value, args.exc_traceback))

def reload_logging(filename):
    from importlib import reload
    reload(logging)
    logging.basicConfig(format='%(asctime)-4s %(levelname)-6s %(threadName)s:%(lineno)-3d %(message)s',
                        datefmt='%H:%M:%S',
                        filename=f"logs/{filename}",
                        filemode='w',
                        level=logging.DEBUG)

def main(my_port: int = 0, node_number: int = 0):
    threading.excepthook = thread_exception_handler
    reload_logging("Server.txt")
    try:
        obj = ServerNode(my_port=my_port, node_number=node_number)
        obj.start()
    except Exception:
        logging.exception("Caught Error")
        raise
