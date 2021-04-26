from socket import socket, AF_INET, SOCK_DGRAM
from datetime import datetime
from player import Player
from exceptions import PlayerCapacityReachedMaximum


class PlayerClient:
    BUFFER_SIZE = 1024
    ALLOWED = 'ALLOWED'

    def __init__(self, address, port):
        self.address = address
        self.port = port
        self.player_socket = None
        self.player = Player()

    def show_message(self, message):

        current_date_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f'[{current_date_time}] {message}')

    def configure_player_client(self):
        """ Configure the player client to use UDP protocol """

        self.show_message('Criando a sessão do jogador...')
        self.player_socket = socket(family=AF_INET, type=SOCK_DGRAM)
        self.show_message('Sessão criada!')

    def end_game(self):
        self.show_message('Fechando o socket...')
        self.player_socket.close()
        self.show_message('Socket fechado')

    def request_join_game(self):
        request = 'JOIN'
        self.show_message('Enviando a solicitação de entrada para o servidor...')
        self.player_socket.sendto(request.encode('ASCII'), (self.address, self.port))

        response, server_address = self.player_socket.recvfrom(self.BUFFER_SIZE)
        game_response = response.decode('ASCII').split('\t')

        if len(game_response) > 0 and game_response[0] == self.ALLOWED:
            self.show_message('Jogador aceito!... ')
            self.player.set_identifier(game_response[1])
            self.handle_name_choice()
        else:
            raise PlayerCapacityReachedMaximum

        print(game_response)

    def play(self):
        """ Send requests to the game server """

        try:
            while True:
                try:
                    if self.player.get_identifier() is None:
                        self.request_join_game()
                    else:
                        self.show_message('Aguardando o início do jogo...\nVocê pode pressionar ctrl + '
                                          'break a qualquer momento para sair do jogo ')

                        response, server_address = self.player_socket.recvfrom(self.BUFFER_SIZE)
                        self.show_message(f'Server said: {response.decode("ASCII")}')

                except OSError as error:
                    break
                    self.show_message('Ops! Mil desculpas, acho que não fui programado direito')

        except KeyboardInterrupt:
            self.show_message('Fim de jogo! Adeus')

        except PlayerCapacityReachedMaximum:
            self.show_message('O jogo atingiu a capacidade máxima! Desculpa')
        finally:
            self.end_game()

    def handle_name_choice(self):
        name = input('Insira seu nome:')
        tries = 1
        while True:
            name_choice = input('Seu nome está correto?\n1 - Sim\n2 - Não\nSua resposta(somente o número): ')
            if name_choice != "1" and tries <= 3:
                name = input("Então vamos escolher um novo nome!\nNome:")
                tries += 1
            else:
                if tries > 3:
                    print('Tá querendo me tirar irmão?')
                    name = 'Bumbum guloso'

                self.player.name = name
                self.show_message(f'Seu nome foi definido como: {self.player.name}')
                break


def main():
    """ Create a session for the player """

    player_client = PlayerClient('localhost', 4051)
    player_client.configure_player_client()
    player_client.play()


if __name__ == '__main__':
    main()
