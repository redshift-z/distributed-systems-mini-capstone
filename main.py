import logging
import multiprocessing
import sys
from pprint import pformat
from argparse import ArgumentParser
from os import makedirs
import threading

# RUN IN PYTHON 3.8.8
import server_node
import relay_node
import client

basic_logging = logging.INFO
node_logging = logging.DEBUG
list_nodes = []
client_port = 9998
server_port = 9999
node_starting_port = 10000

logging.basicConfig(format='%(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d:%H:%M:%S',
                    level=basic_logging)
logger = logging.getLogger(__name__)

class NodeProcess(multiprocessing.Process):

    def run(self):
        try:
            super().run()
        except Exception:
            logger.error(f"{self.name} has an error")


def reload_logging_config_node(filename):
    from importlib import reload
    reload(logging)
    logging.basicConfig(format='%(asctime)-4s %(levelname)-6s %(threadName)s:%(lineno)-3d %(message)s',
                        datefmt='%H:%M:%S',
                        filename=f"logs/{filename}",
                        filemode='w',
                        level=node_logging)

def handle_exception(exc_type, exc_value, exc_traceback):
    logger.error(f"Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

def main():
    # parser = ArgumentParser()
    # parser.add_argument("-N", type=str, dest="node_number",
    #                     help=" ")
    # Relay number akan diset di client.py
    # parser.add_argument("-R", type=str, dest="relay_number",
    #                     help=" ")
    # Mungkin server response hardcoded aja
    # parser.add_argument("-S", type=str, dest="server_response",
    #                     help=" ")
    # args = parser.parse_args()

    # logger.info("Processing args...")
    # node_number: int = int(args.node_number)
    # logger.info("Done processing args...")
    node_number = int(input("Node_number: "))
    execution(node_number)


def execution(node_number):
    logger = logging.getLogger(__name__)
    sys.excepthook = handle_exception
    makedirs("logs", exist_ok=True)

    logger.info("The main program is running...")
    logger.info(f"Creating server instance at port {server_port}...")
    logger.info("Start running server nodes...")
    process = NodeProcess(target=server_node.main, args=(
        server_port,
        node_number
    ))
    process.start()
    list_nodes.append(process)
    logger.info("Done running server node")

    logger.info("Creating relay node instance...")
    logger.info("Determining the ports that will be used...")
    port_used_for_node = [port for port in range(node_starting_port, node_starting_port + node_number)]
    logger.debug(f"port_used: {port_used_for_node}")
    logger.info("Done determining the ports that will be used...")

    logger.info("Start running relay nodes...")
    node_and_port_dict = dict()
    for node_id in range(node_number):
        this_node_port = node_starting_port + node_id
        process = NodeProcess(target=relay_node.main, args=(
            node_id,
            port_used_for_node,
            this_node_port,
            node_number
        ))
        process.start()
        list_nodes.append(process)
        node_and_port_dict[node_id] = this_node_port
    logger.info("Done running relay nodes...")
    logger.info(f"Available nodes for relay:\n{pformat(node_and_port_dict)}")

    logger.info("Done running multiple nodes...")
    logger.debug(f"number of running processes: {len(list_nodes)}")

    logger.info("Launching client...")
    logger.info(f"Creating client instance at port {client_port}...")
    reload_logging_config_node(f"Client.txt")
    # Bisa diganti ke NodeProcess jika diperlukan. Untuk sekarang menggunakan threading agar bisa menggunakan input()
    thread = threading.Thread(target=client.main, name="Client", args=(
        client_port,
        node_and_port_dict
    ))
    thread.start()

if __name__ == '__main__':
    main()