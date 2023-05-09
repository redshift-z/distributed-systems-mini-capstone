import logging
import multiprocessing
import pprint
import random
import sys
from argparse import ArgumentParser

# RUN IN PYTHON 3.8.8
import node

list_nodes = []

logging.basicConfig(format='%(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d:%H:%M:%S',
                    level=logging.INFO)
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
                        level=logging.INFO)

def handle_exception(exc_type, exc_value, exc_traceback):
    logger.error(f"Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

def main():
    parser = ArgumentParser()
    parser.add_argument("-N", type=str, dest="node_number",
                        help=" ")
    parser.add_argument("-R", type=str, dest="relay_number",
                        help=" ")
    parser.add_argument("-C", type=str, dest="client_request",
                        help=" ")
    parser.add_argument("-S", type=str, dest="server_response",
                        help=" ")
    args = parser.parse_args()

    logger.info("Processing args...")
    node_number: int = args.node_number
    relay_number: int = args.relay_number
    client_request: str = args.client_request
    server_response: str = args.server_response
    logger.info("Done processing args...")
    execution(node_number, relay_number, client_request, server_response)


def execution(node_number, relay_number, client_request, server_response):
    logger = logging.getLogger(__name__)

    sys.excepthook = handle_exception

    logger.info("The main program is running...")
    logger.info("Determining the ports that will be used...")
    starting_port = random.randint(10000, 11000)
    port_used = [port for port in range(starting_port, starting_port + node_number)]
    logger.debug(f"port_used: {port_used}")
    logger.info("Done determining the ports that will be used...")

    logger.info("Start running multiple nodes...")
    for node_id in range(node_number):
        is_client = True if node_id == 0 else False
        is_server = True if node_id == 1 else False
        file_name_prefix = "client" if is_client else "server" if is_server else f"node_{node_id}"
        reload_logging_config_node(f"{file_name_prefix}.txt")
        if is_client:
            process = NodeProcess(target=node.main, args=(
                node_id,
                port_used,
                starting_port + node_id,
                client_request,
                relay_number
            ))
        elif is_server:
            process = NodeProcess(target=node.main, args=(
                node_id,
                port_used,
                starting_port + node_id,
                server_response
            ))
        else:
            process = NodeProcess(target=node.main, args=(
                node_id,
                port_used,
                starting_port + node_id
            ))
        process.start()
        list_nodes.append(process)
    logger.info("Done running multiple nodes...")
    logger.debug(f"number of running processes: {len(list_nodes)}")


if __name__ == '__main__':
    main()