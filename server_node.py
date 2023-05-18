import json
import logging
import threading
from data.header import TorHeader
from pprint import pformat
from node import Node

class ServerNode(Node):

    def __init__(self, my_port: int, node_number: int):
        super().__init__(my_id=-1, my_port=my_port)

    def start(self):
        logging.info("Listening for request...")
        inbound_message_json = self.listen_procedure()
        inbound_message = json.loads(inbound_message_json)
        header = TorHeader(**inbound_message["tor_header"])
        data = inbound_message["data"]
        logging.info(f"Request: {pformat(data)}")
        self.send_response(header, data["message"], inbound_message["sender_port"])
    
    def send_response(self, tor_header: TorHeader, request_message: str, sender_port: int):
        response_message = request_message + " accepted"
        logging.info(f"Sending response message to port {sender_port}...")
        outbound_data = {"message": response_message}
        self.tor_send(tor_header.circuit_id, "RELAY_BACKWARD", outbound_data, sender_port)
    
    def tor_send(self, circuit_id: int, cmd: str, data, target_port: int):
        message = dict()
        message["tor_header"] = TorHeader(circuit_id, cmd).__dict__
        message["data"] = data
        message["sender_port"] = self.my_port
        outbound_message = json.dumps(message)
        self.sending_procedure(outbound_message, target_port)


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
