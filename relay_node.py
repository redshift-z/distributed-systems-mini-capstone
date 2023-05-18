import json
import logging
from pprint import pformat
import threading
from data.header import TorHeader
from node import Node
from data.cryptography import generate_session_key, encrypt_with_rsa, decrypt_with_aes, encrypt_with_aes
from data.circuit import Circuit

class RelayNode(Node):
    def __init__(self, my_id: int, my_port: int, ports_of_nodes: list, node_number: int):
        super().__init__(my_id=my_id, my_port=my_port)
        self.node_number = node_number
        self.circuit_dict = dict()
        self.circuit_where_upstream_id_equals = dict()

        self.port_of_nodes_dictionary = {}
        for i in range(0, node_number):
            self.port_of_nodes_dictionary[i] = ports_of_nodes[i]
        logging.debug(f"self.port_of_nodes_dictionary: {pformat(self.port_of_nodes_dictionary)}")

    def start(self):
        while True:
            inbound_message = self.listen_procedure()
            message = json.loads(inbound_message)
            header = TorHeader(**message["tor_header"])
            cmd = header.cmd

            if cmd == "CREATE":
                self.create(header, message["data"], message["sender_port"])
            elif cmd == "EXTEND":
                self.extend(header, message["data"])
            elif cmd in ["CREATED", "EXTENDED"]:
                self.cr_or_ext(header, message["data"])
            elif cmd == "RELAY_FORWARD":
                self.relay_forward(header, message["data"])
            elif cmd == "RELAY_BACKWARD":
                self.relay_backward(header, message["data"])
            else:
                logging.debug(f"Received unknown command {cmd}")

    def create(self, tor_header: TorHeader, data: dict, sender_port: int):
        logging.info("Initializing new circuit...")
        # Initialize data
        sk = generate_session_key()
        logging.info(f"Session key: {sk}")
        gk = data["gk"]

        # Store circuit data
        logging.info("Storing downstream node to memory...")
        new_circuit = Circuit(tor_header.circuit_id, sk)
        new_circuit.downstream_port = sender_port
        self.circuit_dict[tor_header.circuit_id] = new_circuit
        logging.info("Circuit initialized")

        # Create reply message and encrypt it
        logging.info("Creating and encrypting reply message...")
        message = sk
        logging.info(f"Message: {message}")
        encrypted_message = encrypt_with_rsa(gk, message)
        logging.info(f"Encrypted_message: {encrypted_message}")

        # Reply
        logging.info(f"Sending relay created message to port {sender_port}...")
        outbound_data = {"sk": encrypted_message}
        self.tor_send(tor_header.circuit_id, "CREATED", outbound_data, sender_port)

    def extend(self, tor_header: TorHeader, data: str):
        logging.info("Received relay extend command")
        logging.info("Decrypting message")
        circuit = self.circuit_dict[tor_header.circuit_id]
        message = decrypt_with_aes(circuit.sk, data)
        logging.info(f"Decrypted message: {message}")

        logging.info("Processing data...")
        message = json.loads(message)
        inbound_tor_header = TorHeader(**message["tor_header"])
        extracted_data = message["data"]
        target_port = message["target_port"]

        logging.info("Storing upstream node to memory...")
        current_circuit = self.circuit_dict[tor_header.circuit_id]
        current_circuit.upstream_port = target_port
        self.circuit_where_upstream_id_equals[inbound_tor_header.circuit_id] = current_circuit
        logging.info(f"Relaying message to next target port {target_port}")
        self.tor_send(
            inbound_tor_header.circuit_id,
            inbound_tor_header.cmd,
            extracted_data,
            target_port
        )

    def cr_or_ext(self, tor_header: TorHeader, data: dict):
        logging.info("Received confirmation message of successful circuit build")
        circuit: Circuit = self.circuit_where_upstream_id_equals[tor_header.circuit_id]
        logging.info("Extracting data and adding encryption layer...")
        message = dict()
        message["data"] = data
        message_json = json.dumps(message)
        logging.debug(f"message json: {message_json}")
        encrypted_message = encrypt_with_aes(circuit.sk, message_json)
        logging.info(f"Encrypted message: {encrypted_message}")

        logging.info(f"Forwarding message to port {circuit.downstream_port}")
        self.tor_send(circuit.circuit_id, "EXTENDED", encrypted_message, circuit.downstream_port)
    
    def relay_forward(self, tor_header: TorHeader, data: str):
        logging.info("Received relay forward command")
        logging.info("Peeling 1 layer of encryption")
        circuit = self.circuit_dict[tor_header.circuit_id]
        message = decrypt_with_aes(circuit.sk, data)
        logging.info(f"Decrypted message: {message}")

        logging.info("Processing data...")
        message = json.loads(message)
        inbound_tor_header = TorHeader(**message["tor_header"])
        extracted_data = message["data"]
        target_port = message["target_port"]

        logging.info(f"Relaying message to next target port {target_port}")
        self.tor_send(
            inbound_tor_header.circuit_id,
            inbound_tor_header.cmd,
            extracted_data,
            target_port
        )
    
    def relay_backward(self, tor_header: TorHeader, data: dict):
        logging.info("Received relay backward command")
        if tor_header.circuit_id in self.circuit_where_upstream_id_equals:
            circuit: Circuit = self.circuit_where_upstream_id_equals[tor_header.circuit_id]
        else:
            circuit: Circuit = self.circuit_dict[tor_header.circuit_id-1]
        logging.info("Extracting data and adding encryption layer...")
        message = dict()
        message["data"] = data
        message_json = json.dumps(message)
        logging.debug(f"message json: {message_json}")
        encrypted_message = encrypt_with_aes(circuit.sk, message_json)
        logging.info(f"Encrypted message: {encrypted_message}")

        logging.info(f"Relaying message to port {circuit.downstream_port}")
        self.tor_send(circuit.circuit_id, "RELAY_BACKWARD", encrypted_message, circuit.downstream_port)

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

def main(node_id: int, ports_of_nodes: list, my_port: int = 0, node_number: int = 0):
    threading.excepthook = thread_exception_handler
    file_name_prefix = f"Relay {node_id}"
    reload_logging(f"{file_name_prefix}.txt")
    try:
        obj = RelayNode(my_id=node_id, my_port=my_port, ports_of_nodes=ports_of_nodes, node_number=node_number)
        obj.start()
    except Exception:
        logging.exception("Caught Error")
        raise