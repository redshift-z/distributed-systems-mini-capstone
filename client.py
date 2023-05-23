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
        self.random_node_id_list = []

    def start(self):
        logging.info(f"Available nodes for relay: {pformat(self.node_and_port_dict)}")
        circuit_len = int(input("Enter number of relay nodes (positive integers only): "))

        logging.info(f"Building a circuit with {circuit_len} nodes...")
        self.build_circuit(circuit_len)
        logging.info("Circuit built successfully")

        # TODO: Web Request
        logging.info("Starting procedure to send request...")
        self.send_request(str(input("Enter message to send: ")))

        logging.info("Listening for response...")
        inbound_message_json = self.listen_procedure()
        inbound_message = json.loads(inbound_message_json)
        data = inbound_message["data"]
        logging.info(f"INBOUND MESSAGE:\nTor header: {inbound_message['tor_header']}\nData: DATA encrypted with RELAY {self.random_node_id_list[0]} SESSION KEY\nSender port: {inbound_message['sender_port']}")
        self.handle_response(data)

    def build_circuit(self, circuit_len: int):
        logging.info(f"Choosing {circuit_len} random node(s)...")
        self.random_node_id_list = random.sample(self.node_and_port_dict.keys(), circuit_len)
        circuit_dict = {key: self.node_and_port_dict[key] for key in self.random_node_id_list}
        route_str = ""
        for relay_id in circuit_dict.keys():
            route_str += f"Relay {relay_id} -- "
        logging.info(f"Route: Client -- {route_str}Server\n")

        random_node_ports = list(circuit_dict.values())
        for i in range(len(random_node_ports)):
            logging.info("Starting circuit building loop...")
            # Create
            logging.info("Creating data...")
            private_key, public_key = generate_rsa_key()
            message = dict()
            message["tor_header"] = TorHeader(i, "CREATE").__dict__
            message["data"] = {"gk": public_key}
            message["target_port"] = random_node_ports[i]
            logging.info(f"DATA:\nTor header: {message['tor_header']}\nData: CLIENT PUBLIC KEY\nTarget port: {message['target_port']}")

            # Extend
            if self.circuit_list: # If list is not empty
                logging.info(f"Applying {len(self.circuit_list)} layer of encryption to message...")
            for each_circuit in self.circuit_list[::-1]:
                logging.info(f"Encrypting data using RELAY {self.random_node_id_list[self.circuit_list.index(each_circuit)]} SESSION KEY...")
                outbound_message = json.dumps(message)
                encrypted_message = encrypt_with_aes(each_circuit.sk, outbound_message)
                message["tor_header"] = TorHeader(each_circuit.circuit_id, "EXTEND").__dict__
                message["data"] = encrypted_message
                message["target_port"] = each_circuit.upstream_port

            # Send
            logging.info("Sending message...")
            message["sender_port"] = self.my_port
            log_data = ""
            if (len(self.circuit_list) == 0):
                log_data += "CLIENT PUBLIC KEY"
            else:
                log_data += f"DATA encrypted with RELAY {self.random_node_id_list[0]} SESSION KEY"
            logging.info(f"OUTBOUND MESSAGE:\nTor header: {message['tor_header']}\nData: {log_data}\nTarget port: {message['target_port']}\nSender port: {message['sender_port']}")
            outbound_message = json.dumps(message)
            self.sending_procedure(outbound_message, random_node_ports[0])

            # Receive
            logging.info("Listening for reply...")
            inbound_message_json = self.listen_procedure()
            inbound_message = json.loads(inbound_message_json)
            data = inbound_message["data"]
            log_data = ""
            if (len(self.circuit_list) == 0):
                log_data += f"RELAY {self.random_node_id_list[0]} SESSION KEY"
            else:
                log_data += f"DATA encrypted with RELAY {self.random_node_id_list[0]} SESSION KEY"
            logging.info(f"INBOUND MESSAGE:\nTor header: {message['tor_header']}\nData: {log_data}\nSender port: {message['sender_port']}")

            layer = 0
            for each_circuit in self.circuit_list:
                logging.info(f"Peeling encryption layer using RELAY {self.random_node_id_list[layer]} SESSION KEY...")
                decrypted_data = decrypt_with_aes(each_circuit.sk, data)
                if layer < len(self.circuit_list) - 1:
                    logging.debug(f"DECRYPTED DATA:\nData: DATA encrypted with RELAY {self.random_node_id_list[layer+1]} SESSION KEY")
                else:
                    logging.debug(f"DECRYPTED DATA:\nData: RELAY {self.random_node_id_list[i]} SESSION KEY")
                data = json.loads(decrypted_data)["data"]
                layer += 1

            logging.info(f"Storing received session key for port {random_node_ports[i]}...")
            sk = decrypt_with_rsa(private_key, data["sk"])
            new_circuit = Circuit(i, sk)
            new_circuit.upstream_port = random_node_ports[i]
            self.circuit_list.append(new_circuit)

            logging.debug(f"CIRCUIT STORED:")
            debugstr = ""
            for circuit in self.circuit_list:
                debugstr += f"{str(circuit)}, upstream_port: {circuit.upstream_port}\n"
            logging.debug(f"\n{debugstr}")
    
    def send_request(self, request_msg: str):

        #Encrypt message
        logging.info("Creating data...")
        message = dict()
        message["tor_header"] = TorHeader(len(self.circuit_list), "RELAY FORWARD").__dict__
        message["data"] = {"message": request_msg}
        message["target_port"] = 9999
        logging.info(f"DATA:\nTor header: {message['tor_header']}\nData: {message['data']}\nTarget port: {message['target_port']}")
        logging.info("Start encrypting message...")
        for circuit in self.circuit_list[::-1]:
            logging.info(f"Encrypting message with session key from RELAY {self.random_node_id_list[self.circuit_list.index(circuit)]} SESSION KEY")
            outbound_message = json.dumps(message)
            encrypted_message = encrypt_with_aes(circuit.sk, outbound_message)
            message["tor_header"] = TorHeader(circuit.circuit_id, "RELAY FORWARD").__dict__
            message["data"] = encrypted_message
            message["target_port"] = circuit.upstream_port
            logging.info(f"ENCRYPTED MESSAGE:\nTor header: {message['tor_header']}\nData: DATA encrypted with RELAY {self.random_node_id_list[self.circuit_list.index(circuit)]} SESSION KEY\nTarget port: {message['target_port']}")

        #Sending message
        logging.info("Sending message...")
        message["sender_port"] = self.my_port
        logging.info(f"OUTBOUND MESSAGE:\nTor header: {message['tor_header']}\nData: DATA encrypted with RELAY {self.random_node_id_list[self.circuit_list.index(circuit)]} SESSION KEY\nTarget port: {message['target_port']}\nSender port: {message['sender_port']}")
        outbound_message = json.dumps(message)
        self.sending_procedure(outbound_message, self.circuit_list[0].upstream_port)
    
    def handle_response(self, response: str):
        logging.info("Start peeling encryption layers...")
        layer = 0
        for each_circuit in self.circuit_list:
            logging.info(f"Decrypting message with RELAY {self.random_node_id_list[layer]} SESSION KEY...")
            decrypted_data = decrypt_with_aes(each_circuit.sk, response)
            log_data = ""
            if layer < len(self.circuit_list) - 1:
                log_data += f"DATA encrypted with {self.random_node_id_list[layer+1]} SESSION KEY"
            else:
                log_data += str(decrypted_data["data"])
            logging.debug(f"DECRYPTED DATA:\nTor header: {decrypted_data['tor_header']}\nData: {log_data}\nTarget port: {decrypted_data['target_port']}")
            response = json.loads(decrypted_data)["data"]
            layer += 1

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
