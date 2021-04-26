import threading
import server  # This is our own server
from uuid import uuid4


class GameServer(server.Server):

    players_list = {}
    JOIN_WISH = 'JOIN'

    def __init__(self, address, port, max_num_of_players):
        super().__init__(address, port)
        self.max_num_of_players = max_num_of_players
        self.session_lock = threading.Lock()  # This ensures that we'll send the answer to the correct player

    def add_player_to_list(self,player_identifier, player_address):
        self.players_list[player_identifier] = player_address

    def handle_player_message(self, message, operation, identifier):

        return message

    def handle_player_request(self, data, player_address):
        """ Handle Player request """

        player_message = data.decode('ASCII')
        player_operation = player_message.split('\t')
        player_identifier = ""
        self.show_message(f' Request: {player_message} // from player: {player_address}')

        if len(player_operation) > 0 and player_operation[0] == self.JOIN_WISH:

            if len(self.players_list) >= self.max_num_of_players:

                response = "DENIED\t GAME IS FULL"

            else:

                player_identifier = uuid4()
                response = "ALLOWED\t"+str(player_identifier)
                self.add_player_to_list(player_identifier, player_address[1])

        else:

            response = self.handle_player_message(player_message, player_operation, player_identifier)

        self.show_message(f' Response: {response} // to player: {player_address}')
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