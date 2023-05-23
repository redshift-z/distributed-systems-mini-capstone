import logging

def gui_event_start(name):
    logging.info(f"\nGUI_EVENT_START\n{name}")

# def gui_event_additional_info(info: dict)
#     logging.info(f"\nGUI_EVENT_ADDITIONAL_INFO\n{info}")

def gui_event_stop(next_node):
    logging.info(f"\nGUI_EVENT_STOP\nNext event at: {next_node}")

def gui_event_get_next(string:str):
    return string[15:]

def gui_event_get_node_name_from_port(port:int):
    if port == 9998:
        return "Client"
    if port == 9999:
        return "Server"
    return f"Relay {port - 10000}"