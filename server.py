from socket import socket, AF_INET, SOCK_DGRAM
from datetime import datetime


class Server:
    # CONSTANTS
    BUFFER_SIZE = 1024

    def __init__(self, address='localhost', port=4051):

        # Server properties
        self.address = address
        self.port = port
        self.server_socket = None

    def show_message(self, msg):

        """ Prints the given message with the current time """
        current_date_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f'[{current_date_time}] {msg}')

    def configure_server(self):

        """ Configure the server """
        self.show_message('Creating socket and configuring server...')
        self.server_socket = socket(family=AF_INET, type=SOCK_DGRAM)
        self.server_socket.bind((self.address, self.port))
        self.server_socket.settimeout(10.0)
        self.show_message(f'Server binded to {self.address}:{self.port}')

    def shutdown_server(self):

        """ Shutdown the server """
        self.show_message("Shutting down the server...")
        self.server_socket.close()
        self.show_message("Goodbye...")
