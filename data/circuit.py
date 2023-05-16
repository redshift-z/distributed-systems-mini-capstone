from Crypto.Cipher import AES

class Circuit:
    def __init__(self, circuit_id: int, sk: str):
        self.circuit_id = circuit_id
        self.sk = sk

    @property
    def downstream_port(self):
        return self._downstream_port

    @downstream_port.setter
    def downstream_port(self, value):
        self._downstream_port = value

    # @property
    # def downstream_id(self):
    #     return self._downstream_id

    # @downstream_id.setter
    # def downstream_id(self, value):
    #     self._downstream_id = value

    @property
    def upstream_port(self):
        return self._upstream_port

    @upstream_port.setter
    def upstream_port(self, value):
        self._upstream_port = value

    # @property
    # def upstream_id(self):
    #     return self._upstream_id

    # @upstream_id.setter
    # def upstream_id(self, value):
    #     self._upstream_id = value

    def __str__(self):
        return f"id: {self.circuit_id}, sk: {self.sk}"