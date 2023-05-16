import json
import logging
from pprint import pformat
import random
import threading
from data.header import TorHeader
from node import Node
from data.cryptography import generate_rsa_key, decrypt_with_rsa, encrypt_with_aes, decrypt_with_aes
from data.circuit import Circuit

class ClientNode(Node):

    def __init__(self, my_port: int, node_and_port_dict: dict):
        super().__init__(my_id=-1, my_port=my_port)
        self.node_and_port_dict = node_and_port_dict
        self.circuit_list = []

    def start(self):
        logging.info(f"Available nodes for relay: {pformat(self.node_and_port_dict)}")
        circuit_len = int(input("Total relay node to build a circuit (int): "))

        logging.info(f"Building a circuit with {circuit_len} nodes")
        self.build_circuit(circuit_len)

        # TODO: Web Request

    def build_circuit(self, circuit_len: int):
        logging.info(f"Choosing {circuit_len} random node(s)...")
        random_node_id_list = random.sample(self.node_and_port_dict.keys(), circuit_len)
        circuit_dict = {key: self.node_and_port_dict[key] for key in random_node_id_list}
        route_str = ""
        for relay_id in circuit_dict.keys():
            route_str += f"Relay {relay_id} -- "
        logging.info(f"Route: Client -- {route_str}Server\n")

        random_node_ports = list(circuit_dict.values())
        for i in range(len(random_node_ports)):
            logging.info("Starting circuit building loop...")
            # Create
            logging.info("Initializing create data")
            private_key, public_key = generate_rsa_key()
            message = dict()
            message["tor_header"] = TorHeader(i, "CREATE").__dict__
            message["data"] = {"gk": public_key}
            message["target_port"] = random_node_ports[i]
            logging.info(f"Create data:\n{message}")

            # Extend
            if self.circuit_list: # If list is not empty
                logging.info(f"Applying {len(self.circuit_list)} layer of encryption to message...")
            for each_circuit in self.circuit_list[::-1]:
                outbound_message = json.dumps(message)
                encrypted_message = encrypt_with_aes(each_circuit.sk, outbound_message)
                message["tor_header"] = TorHeader(each_circuit.circuit_id, "EXTEND").__dict__
                message["data"] = encrypted_message
                message["target_port"] = each_circuit.upstream_port

            # Send
            logging.info("Sending message...")
            message["sender_port"] = self.my_port
            outbound_message = json.dumps(message)
            self.sending_procedure(outbound_message, random_node_ports[0])

            # Receive
            logging.info("Listening for reply...")
            inbound_message_json = self.listen_procedure()
            inbound_message = json.loads(inbound_message_json)
            data = inbound_message["data"]

            logging.info("Peeling encryption layer...")
            for each_circuit in self.circuit_list:
                logging.debug(f"data: {data}")
                decrypted_data = decrypt_with_aes(each_circuit.sk, data)
                logging.debug(f"decrypted data: {decrypted_data}")
                data = json.loads(decrypted_data)["data"]

            logging.info(f"Storing received session key for port {random_node_ports[i]}...")
            # inbound_header = TorHeader(**inbound_message["tor_header"])
            sk = decrypt_with_rsa(private_key, data["sk"])
            new_circuit = Circuit(i, sk)
            new_circuit.upstream_port = random_node_ports[i]
            self.circuit_list.append(new_circuit)

            debugstr = ""
            for circuit in self.circuit_list:
                debugstr += f"{str(circuit)}, upstream_port: {circuit.upstream_port}\n"
            logging.debug(f"\n{debugstr}")


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
