import logging
import socket
import threading


class NodeSocket:

    def __init__(self, socket_kind: socket.SocketKind, port: int = 0):
        sc = socket.socket(socket.AF_INET, socket_kind)
        sc.bind(('127.0.0.1', port))
        self.sc = sc


class TcpSocket(NodeSocket):

    def __init__(self, port: int = 0):
        super(TcpSocket, self).__init__(socket.SOCK_STREAM, port)
        self.sc.listen(1)
        self.tcp_lock = threading.Lock()
        self.connection = None

    def listen(self):
        self.tcp_lock.acquire()
        connection, address = self.sc.accept()
        input_value = connection.recv(1024).decode("UTF-8")
        self.connection = connection

        return input_value, address

    def reply_tcp(self, message: str):
        self.connection.send(message.encode("UTF-8"))
        self.connection.close()
        self.connection = None
        self.tcp_lock.release()

    def send(self, message: str, port: int = 0):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(("127.0.0.1", port))
            s.sendall(message.encode("UTF-8"))
            return s.recv(1024).decode("UTF-8")

class UdpSocket(NodeSocket):

    def __init__(self, port: int = 0):
        super(UdpSocket, self).__init__(socket.SOCK_DGRAM, port)

    def listen(self):
        input_value_byte, address = self.sc.recvfrom(1024)
        return input_value_byte.decode("UTF-8"), address

    @staticmethod
    def send(message: str, port: int = 0):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.sendto(message.encode("UTF-8"), ("127.0.0.1", port))
        client_socket.close()


