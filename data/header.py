import json

class TorHeader:
    def __init__(self, circuit_id: int, cmd: str):
        self.circuit_id = circuit_id
        self.cmd = cmd