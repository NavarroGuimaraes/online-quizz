import threading
from socket import socket, AF_INET, SOCK_DGRAM
from datetime import datetime
from player import Player
from exceptions import PlayerCapacityReachedMaximum, GameOver, TimesUp
from timeout import timeout


class PlayerClient:
    BUFFER_SIZE = 1024
    ALLOWED = 'ALLOWED'
    INFO = 'INFO'
    WARNING = 'WARN'
    END_GAME = 'OVER'
    QUESTION = 'QST'
    ANSWER = 'ANS'
    ENCODING = 'UTF-8'
    ANSWER_IS_CORRECT = "RGT"
    ANSWER_IS_WRONG = "WRG"
    TIMEOUT_FOR_ANSWER = 10

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
        self.player_socket.sendto(request.encode(self.ENCODING), (self.address, self.port))

        response, server_address = self.player_socket.recvfrom(self.BUFFER_SIZE)
        game_response = response.decode(self.ENCODING).split('\t')
        if len(game_response) > 0 and game_response[0] == self.ALLOWED:
            self.show_message('Jogador aceito!... ')
            self.player.set_identifier(game_response[1])
            self.handle_name_choice()
            self.show_message('Aguardando o início do jogo...\nVocê pode pressionar ctrl + '
                              'break a qualquer momento para sair do jogo ')
        else:
            raise PlayerCapacityReachedMaximum

    def send_message_to_server(self, message):
        self.player_socket.sendto(message.encode(self.ENCODING), (self.address, self.port))

    def show_score(self):
        self.show_message(f'Sua pontuação atual é de: {self.player.score}')

    def play(self):
        """ Send requests to the game server """

        if self.player.get_identifier() is None:
            self.request_join_game()
        try:
            while True:
                try:
                    response, server_address = self.player_socket.recvfrom(self.BUFFER_SIZE)
                    self.handle_server_response(response.decode(self.ENCODING))

                except OSError as error:
                    self.show_message('Ops! Mil desculpas, acho que não fui programado direito')
                    break

        except KeyboardInterrupt:
            self.show_message('Fim de jogo! Adeus')

        except PlayerCapacityReachedMaximum:
            self.show_message('O jogo atingiu a capacidade máxima! Desculpa')

        except GameOver:
            self.show_message(f'Obrigado por jogar {self.player.name}!!'
                              f'Sua pontuação foi de {self.player.score}')
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

    def handle_server_response(self, response):
        server_messages = response.split('\t')
        goal = server_messages[0]
        if goal == self.INFO:
            for i in range(1, len(server_messages)):
                self.show_message(server_messages[i])

        elif goal == self.QUESTION:
            self.handle_question(server_messages[1])

        elif goal == self.ANSWER_IS_CORRECT:
            self.handle_correct_answer(server_messages[1])

        elif goal == self.ANSWER_IS_WRONG:
            self.handle_wrong_answer(server_messages[1])
        elif goal == self.END_GAME:
            raise GameOver

    def handle_question(self, question):
        self.show_message(question)
        try:
            answer = self.read_answer()
            if isinstance(answer, TimeoutError):
                self.show_message("Você demorou demais...")
            else:
                self.send_message_to_server(self.build_answer(answer))
        except Exception as e:
            self.show_message("Ops, houve um erro!")

    @timeout(10)
    def read_answer(self):
        return input("Sua resposta: ")

    def handle_correct_answer(self, message):
        self.show_message(message)
        self.player.score += 25
        self.show_score()

    def handle_wrong_answer(self, message):
        self.show_message(message)
        self.player.score -= 5
        self.show_score()

    def build_answer(self, answer):
        text = self.ANSWER+"\t"+self.player.identifier+"\t"+answer
        return text

def main():
    """ Create a session for the player """

    player_client = PlayerClient('localhost', 4051)
    player_client.configure_player_client()
    player_client.play()


if __name__ == '__main__':
    main()
