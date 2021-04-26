from socket import socket, AF_INET, SOCK_DGRAM
from datetime import datetime

class PlayerClient:

    BUFFER_SIZE = 1024

    def __init__(self, address, port):
        self.address = address
        self.port = port
        self.player_socket = None

    def show_message(self, message):

        current_date_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f'[{current_date_time}] {message}')

    def configure_player_client(self):
        """ Configure the player client to use UDP protocol """

        self.show_message('Creating player session...')
        self.player_socket = socket(family=AF_INET, type=SOCK_DGRAM)
        self.show_message('Session created!')

    def interact_with_server(self):
        ''' Send requests to the game server '''
        try:
            self.show_message('Sending request to server...')
            request = 'teste'
            self.player_socket.sendto(request.encode('ASCII'), (self.address, self.port))
            self.show_message('Request succesfully sent ')

            response, server_address = self.player_socket.recvfrom(self.BUFFER_SIZE)
            self.show_message(f'Response received: {response.decode("ASCII")}')

        except OSError as error:
            print(error)

        finally:
            self.show_message('Closing socket...')
            self.player_socket.close()
            self.show_message('Socket closed')


def main():
    """ Create a session for the player """

    player_client = PlayerClient('localhost', 4051)
    player_client.configure_player_client()
    player_client.interact_with_server()


if __name__ == '__main__':
    main()