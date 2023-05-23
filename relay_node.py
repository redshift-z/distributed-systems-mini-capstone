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
                logging.info(f"\nINBOUND MESSAGE:\nTor header: {message['tor_header']}\nData: CLIENT PUBLIC KEY\nSender port: {message['sender_port']}")
                self.create(header, message["data"], message["sender_port"])
            elif cmd == "EXTEND":
                logging.info(f"\nINBOUND MESSAGE:\nTor header: {message['tor_header']}\nData: DATA encrypted with RELAY {self.my_id} SESSION KEY\nSender port: {message['sender_port']}")
                self.extend(header, message["data"])
            elif cmd in ["CREATED", "EXTENDED"]:
                if cmd == "CREATED":
                    logging.info(f"\nINBOUND MESSAGE:\nTor header: {message['tor_header']}\nData: RELAY SESSION KEY\nSender port: {message['sender_port']}")
                else:
                    logging.info(f"\nINBOUND MESSAGE:\nTor header: {message['tor_header']}\nData: DATA ENCRYPTED with RELAY SESSION KEY\nSender port: {message['sender_port']}")
                self.cr_or_ext(header, message["data"])
            elif cmd == "RELAY FORWARD":
                logging.info(f"\nINBOUND MESSAGE:\nTor header: {message['tor_header']}\nData: DATA encrypted with RELAY SESSION KEY\nSender port: {message['sender_port']}")
                self.relay_forward(header, message["data"])
            elif cmd == "RELAY BACKWARD":

                # TODO: !!!
                if isinstance(message['data'], dict) or self.is_json(message['data']):
                    logging.info(f"\nINBOUND MESSAGE:\nTor header: {message['tor_header']}\nData: {message['data']}\nSender port: {message['sender_port']}")
                else:
                    logging.info(f"\nINBOUND MESSAGE:\nTor header: {message['tor_header']}\nData: DATA encrypted with RELAY SESSION KEY\nSender port: {message['sender_port']}")

                self.relay_backward(header, message["data"])
            else:
                logging.debug(f"Received unknown command {cmd}")

    def create(self, tor_header: TorHeader, data: dict, sender_port: int):
        logging.info("Initializing new circuit...")
        # Initialize data
        logging.info("Generating season key...")
        sk = generate_session_key()
        gk = data["gk"]

        # Store circuit data
        logging.info("Storing downstream node to memory...")
        new_circuit = Circuit(tor_header.circuit_id, sk)
        new_circuit.downstream_port = sender_port
        self.circuit_dict[tor_header.circuit_id] = new_circuit
        logging.info("Circuit initialized")

        # Create reply message and encrypt it
        logging.info("Creating reply message...")
        message = sk
        logging.info(f"Message: RELAY {self.my_id} SESSION KEY")
        encrypted_message = encrypt_with_rsa(gk, message)
        logging.info("Encrypting reply message with CLIENT PUBLIC KEY...")

        # Reply
        logging.info(f"Sending CREATED message to port {sender_port}...")
        outbound_data = {"sk": encrypted_message}
        logging.info(f"\nOUTBOUND MESSAGE:\nTor header: {TorHeader(tor_header.circuit_id, 'CREATED').__dict__}\nData: SESSION KEY encrypted with CLIENT PUBLIC KEY\nSender port: {self.my_port}")
        self.tor_send(tor_header.circuit_id, "CREATED", outbound_data, sender_port)

    def extend(self, tor_header: TorHeader, data: str):
        logging.info("Received relay extend command")
        logging.info("Decrypting message...")
        circuit = self.circuit_dict[tor_header.circuit_id]
        message = decrypt_with_aes(circuit.sk, data)
        log_data = ""

        # TODO: !!!
        #logging.info(f"message: {message}")
        if isinstance(json.loads(message)['data'], dict) or self.is_json(json.loads(message)['data']):
            log_data = "CLIENT PUBLIC KEY"
        else:
            log_data = "DATA encrypted with NEXT RELAY'S SESSION KEY"

        logging.info("DECRYPTED MESSAGE: " + log_data)

        logging.info("Processing data...")
        message = json.loads(message)
        inbound_tor_header = TorHeader(**message["tor_header"])
        extracted_data = message["data"]
        target_port = message["target_port"]

        logging.info("Storing upstream node to memory...")
        current_circuit = self.circuit_dict[tor_header.circuit_id]
        current_circuit.upstream_port = target_port
        self.circuit_where_upstream_id_equals[inbound_tor_header.circuit_id] = current_circuit
        logging.info(f"Relaying message to next target port {target_port}...")
        logging.info(f"\nOUTBOUND MESSAGE:\nTor header: {TorHeader(inbound_tor_header.circuit_id, inbound_tor_header.cmd).__dict__}\nData: {log_data}\nSender port: {self.my_port}")
        self.tor_send(
            inbound_tor_header.circuit_id,
            inbound_tor_header.cmd,
            extracted_data,
            target_port
        )

    def cr_or_ext(self, tor_header: TorHeader, data: dict):
        logging.info("Received confirmation message of successful circuit build")
        circuit: Circuit = self.circuit_where_upstream_id_equals[tor_header.circuit_id]
        logging.info("Extracting data...")
        log_data = ""

        # TODO: !!!
        if isinstance(data, dict) or self.is_json(data):
            log_data = "SESSION KEY"
        else:
            log_data = "DATA encrypted with RELAY SESSION KEY"

        logging.info("DATA: " + log_data)
        logging.info("Adding encryption layer...")
        message = dict()
        message["data"] = data
        message_json = json.dumps(message)
        encrypted_message = encrypt_with_aes(circuit.sk, message_json)

        logging.info(f"Forwarding message to port {circuit.downstream_port}...")
        logging.info(f"\nOUTBOUND MESSAGE:\nTor header: {TorHeader(circuit.circuit_id, 'EXTENDED').__dict__}\nData: DATA encrypted with RELAY {self.my_id} SESSION KEY\nSender port: {self.my_port}")
        self.tor_send(circuit.circuit_id, "EXTENDED", encrypted_message, circuit.downstream_port)
    
    def relay_forward(self, tor_header: TorHeader, data: str):
        logging.info("Received command to relay forward")
        logging.info("Peeling 1 layer of encryption...")
        circuit = self.circuit_dict[tor_header.circuit_id]
        message = decrypt_with_aes(circuit.sk, data)
        log_data = ""
        
        # TODO: !!!
        if isinstance(json.loads(message)['data'], dict) or self.is_json(json.loads(message)['data']):
            log_data = json.loads(message)['data']
        else:
            log_data = "DATA encrypted with NEXT RELAY'S SESSION KEY"

        logging.info(f"\nDECRYPTED MESSAGE:\nTor header: {json.loads(message)['tor_header']}\nData: {log_data}\nTarget port: {json.loads(message)['target_port']}\nSender port: {self.my_port}")

        message = json.loads(message)
        inbound_tor_header = TorHeader(**message["tor_header"])
        extracted_data = message["data"]
        target_port = message["target_port"]

        logging.info(f"Relaying message to next target port {target_port}...")
        logging.info(f"\nOUTBOUND MESSAGE:\nTor header: {TorHeader(inbound_tor_header.circuit_id, inbound_tor_header.cmd).__dict__}\nData: {log_data}\nSender port: {self.my_port}")
        self.tor_send(
            inbound_tor_header.circuit_id,
            inbound_tor_header.cmd,
            extracted_data,
            target_port
        )
    
    def relay_backward(self, tor_header: TorHeader, data: dict):
        logging.info("Received command to relay backward")
        if tor_header.circuit_id in self.circuit_where_upstream_id_equals:
            circuit: Circuit = self.circuit_where_upstream_id_equals[tor_header.circuit_id]
        else:
            circuit: Circuit = self.circuit_dict[tor_header.circuit_id-1]
        logging.info("Adding 1 encryption layer...")
        message = dict()
        message["data"] = data
        message_json = json.dumps(message)
        encrypted_message = encrypt_with_aes(circuit.sk, message_json)
        logging.info(f"\nENCRYPTED MESSAGE\nTor header: {TorHeader(circuit.circuit_id, 'RELAY BACKWARD').__dict__}\nData: DATA encrypted with RELAY {self.my_id} SESSION KEY\nSender port: {self.my_port}")

        logging.info(f"Relaying message to port {circuit.downstream_port}...")
        logging.info(f"\nOUTBOUND MESSAGE\nTor header: {TorHeader(circuit.circuit_id, 'RELAY BACKWARD').__dict__}\nData: DATA encrypted with RELAY {self.my_id} SESSION KEY\nSender port: {self.my_port}")
        self.tor_send(circuit.circuit_id, "RELAY BACKWARD", encrypted_message, circuit.downstream_port)

    def tor_send(self, circuit_id: int, cmd: str, data, target_port: int):
        message = dict()
        message["tor_header"] = TorHeader(circuit_id, cmd).__dict__
        message["data"] = data
        message["sender_port"] = self.my_port
        outbound_message = json.dumps(message)
        self.sending_procedure(outbound_message, target_port)
    
    def is_json(self, data: str):
        try:
            json.loads(data)
        except ValueError as e:
            return False
        return True


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