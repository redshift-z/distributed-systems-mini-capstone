import logging
import multiprocessing
import sys
from pprint import pformat
from os import makedirs
import threading
import tkinter as tk
import sys

# RUN IN PYTHON 3.8.8
import server_node
import relay_node
import client

basic_logging = logging.INFO
client_logging = logging.INFO
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
                        level=client_logging)

def handle_exception(exc_type, exc_value, exc_traceback):
    logger.error(f"Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

def main():

    def validate_numeric_input(value: str):
        if value.isdigit() and value != "0" or value == "":
            return True
        return False

    def check_if_all_entry_filled(*args):
        for each_var in (node_number_var, node_number_in_relay_var, message_to_send_var):
            # If any entry is still empty disable sim start
            if each_var.get() == "":
                sim_start_button.config(state="disabled")
                return
        # Else enable sim start
        sim_start_button.config(state="normal")

    def on_node_number_input_update(*args):
        if node_number_var.get() == "":
            node_number_in_relay_input.config(state="disabled")
        else:
            node_number_in_relay_input.config(state="normal")
            if node_number_in_relay_var.get() != "":
                node_number_in_relay_var.set(min(int(node_number_var.get()), int(node_number_in_relay_var.get())))

    def on_node_relay_input_update(*args):
        if node_number_in_relay_var.get() != "":
            node_number_in_relay_var.set(min(int(node_number_var.get()), int(node_number_in_relay_var.get())))

    def start_button_pressed():
        submitted_node_number = int(node_number_var.get())
        submitted_circuit_length = int(node_number_in_relay_var.get())
        submitted_message = message_to_send_var.get()
        sim_start_button.destroy()
        for each_var in (node_number_input, node_number_in_relay_input, message_to_send_input):
            each_var.config(state="disabled")
        tk.Label(gui_window, text="Simulation executed, please wait...").pack()
        execution(submitted_node_number, submitted_circuit_length, submitted_message, gui_window)

    # Build the gui window
    gui_window = tk.Tk()
    gui_window.title("Onion Routing Simulator")
    gui_width, gui_height = 300, 235
    gui_window.geometry(f"{gui_width}x{gui_height}")
    gui_window.resizable(False, False)
    numeric_validation = gui_window.register(validate_numeric_input)

    # Input widget
    tk.Label(gui_window, text="Enter number of nodes available for relay", height=2).pack(anchor="w", padx="10")
    node_number_var = tk.StringVar()
    node_number_var.trace_add("write", check_if_all_entry_filled)
    node_number_var.trace_add("write", on_node_number_input_update)
    node_number_input = tk.Entry(gui_window, validate="key", validatecommand=(numeric_validation, "%P"), textvariable=node_number_var)
    node_number_input.pack(fill="x", padx="10")
    tk.Label(gui_window, text="Recommended up to 10 node").pack(anchor="w", padx="10")

    tk.Label(gui_window, text="Enter number of relay nodes", height=2).pack(anchor="w", padx="10")
    node_number_in_relay_var = tk.StringVar()
    node_number_in_relay_var.trace_add("write", check_if_all_entry_filled)
    node_number_in_relay_var.trace_add("write", on_node_relay_input_update)
    node_number_in_relay_input = tk.Entry(gui_window, validate="key", validatecommand=(numeric_validation, "%P"), textvariable=node_number_in_relay_var, state="disabled")
    node_number_in_relay_input.pack(fill="x", padx="10")

    tk.Label(gui_window, text="Enter message to send", height=2).pack(anchor="w", padx="10")
    message_to_send_var = tk.StringVar()
    message_to_send_var.trace_add("write", check_if_all_entry_filled)
    message_to_send_input = tk.Entry(gui_window, textvariable=message_to_send_var)
    message_to_send_input.pack(fill="x", padx="10")

    # Start button
    sim_start_button = tk.Button(gui_window, text="Start simulation", command=start_button_pressed, state="disabled")
    sim_start_button.pack(pady=10)

    gui_window.mainloop()


def execution(node_number, circuit_length, message, main_gui):
    logger = logging.getLogger(__name__)
    sys.excepthook = handle_exception
    makedirs("logs", exist_ok=True)

    logger.info("The main program is running...")
    logger.info(f"Creating server instance at port {server_port}...")
    logger.info("Start running server nodes...")
    process = NodeProcess(target=server_node.main, daemon=True, args=(
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
        process = NodeProcess(target=relay_node.main, daemon=True, args=(
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
    thread = threading.Thread(target=client.main, name="Client", daemon=True, args=(
        client_port,
        node_and_port_dict,
        main_gui,
        circuit_length,
        message
    ))
    thread.start()

if __name__ == '__main__':
    main()