import threading
import server  # This is our own server


class GameServer(server.Server):

    players_list = []

    def __init__(self, address, port, number_of_players):
        super().__init__(address, port)
        self.number_of_players = number_of_players
        self.session_lock = threading.Lock()  # This ensures that we'll send the answer to the correct player

    def handle_player_message(self, message):
        return message

    def handle_player_request(self, data, player_address):
        """ Handle Player request """

        player_message = data.decode('ASCII')
        self.show_message(f' Request: {player_message} from player: {player_address}')
        response = self.handle_player_message(player_message)
        self.show_message(f' Response: {response} to player: {player_address}')
        with self.session_lock:
            self.server_socket.sendto(response.encode('ASCII'), player_address)

    def wait_for_players(self):
        """Wait for players to join the game"""

        try:
            while True:
                try:

                    data, player_address = self.server_socket.recvfrom(self.BUFFER_SIZE)
                    player_thread = threading.Thread(target=self.handle_player_request, args=(data, player_address))
                    player_thread.daemon = True
                    player_thread.start()

                except OSError as error:
                    self.show_message(error)

        except KeyboardInterrupt:
            self.shutdown_server()

def main():
    """ Create game server """
    game_server = GameServer('localhost', 4051, 2)
    game_server.configure_server()
    game_server.wait_for_players()

if __name__ == '__main__':
    main()