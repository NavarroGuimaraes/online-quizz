import threading
import server  # This is our own server
from uuid import uuid4
from time import time, sleep
from random import randint
from exceptions import GameOver


class GameServer(server.Server):
    players_list = {}
    JOIN = 'JOIN'
    ANSWER = 'ANS'
    UPDATE_INFO = 'UPDT'
    QUESTIONS = []
    ANSWERS = []
    ENCODING = 'UTF-8'
    QUESTION = 'QST'
    players_score = {}
    players_who_answered = []
    QUEST_TIME = 10
    ANSWER_IS_CORRECT = "RGT"
    ANSWER_IS_WRONG = "WRG"

    def __init__(self, address, port, max_num_of_players):

        super().__init__(address, port)
        self.max_num_of_players = max_num_of_players
        self.session_lock = threading.Lock()  # This ensures that we'll send the answer to the correct player

        self.max_wait_time = 300  # in seconds
        self.timer_started_at = None
        self.timer = None
        self.is_game_started = False
        self.qt_questions_made = 0
        self.current_question = None
        self.current_answer = None
        self.timer_to_wait_answer = None

        with open('questions.txt', 'r', encoding='UTF-8') as file:
            for row in file:
                row = row.strip()
                question, answer = row.split('\t')
                self.QUESTIONS.append(question)
                self.ANSWERS.append(answer)

    def add_player_to_list(self, player_identifier, player_address):
        self.players_list[player_identifier] = player_address
        self.players_score[player_identifier] = 0
        self.players_score[player_identifier] += 5
        print(self.players_score[player_identifier])

    def get_remaining_time_to_begin(self):
        return int(self.max_wait_time - (time() - self.timer_started_at))

    def handle_timer_wait_limit(self):
        self.timer = None
        self.timer_started_at = None
        self.show_message("Tempo encerrado, vamos iniciar o jogo!")
        sleep(5)
        self.start_game()

    def start_server_timer(self):
        self.timer_started_at = time()
        self.timer = threading.Timer(self.max_wait_time, self.handle_timer_wait_limit)
        self.timer.start()
        self.show_message(f'Aguardaremos a entrada dos jogadores ou iniciaremos em {self.max_wait_time} segundos!')
        sleep(2)

    def handle_player_answer(self, answer, identifier):
        if self.current_answer.upper() == answer.upper():
            self.players_score[identifier] += 25
            message = self.ANSWER_IS_CORRECT+"\tSua Resposta está correta!"
            # Eu sei que, o ideal seria o servidor contar a pontuação para o player.
            # Nesse caso, como fiz apenas o MVP, decidi deixar o client do player somar o score
            # Futuramente posso mudar isso

        else:
            self.players_who_answered[identifier] -= 5
            message = f"WRG\tInfelizmente você errou! A resposta correta seria: {self.current_answer}"

        self.players_who_answered.append(identifier)
        self.send_message_to_player(identifier, message)

    def handle_player_request(self, data, player_address):
        """ Handle Player request """

        player_message = data.decode(self.ENCODING)
        player_operation = player_message.split('\t')
        player_wants_to = player_operation[0]
        self.show_message(f' Request: {player_message} // from player: {player_address}')

        if player_wants_to == self.ANSWER:
            player_identifier = player_operation[1]
            player_message = player_operation[2]
            self.handle_player_answer(player_message, player_identifier)
            self.check_if_all_answered()

        elif player_wants_to == self.JOIN:
            self.handle_join_request_player(player_address)

        elif player_wants_to == self.UPDATE_INFO:
            player_identifier = player_operation[1]
            self.send_message_to_player(player_identifier,
                                        self.get_game_details())

    def check_if_all_answered(self):
        if len(self.players_who_answered) >= len(self.players_list):
            self.timer_to_wait_answer.cancel()
            self.do_play()

    def can_game_start(self):
        if len(self.players_list) == self.max_num_of_players:
            self.start_game()

    def send_message_to_all_players(self, message):
        for identifier, address in self.players_list.items():
            self.send_message_to_player(identifier, message)

    def finish_game(self):
        raise GameOver

    def ask_and_wait_or_timeout(self):
        self.send_message_to_all_players(self.QUESTION+"\t"+self.current_question)
        self.timer_to_wait_answer = threading.Timer(self.QUEST_TIME, self.timeout_quest_time)
        self.timer_to_wait_answer.start()

    def timeout_quest_time(self):
        self.send_message_to_all_players("INFO\tTempo esgotado!")
        sleep(3)
        players_who_didnt_answered = [identifier for identifier in self.players_list if identifier
                                      not in self.players_who_answered]
        for player in players_who_didnt_answered:
            self.players_score[player] -= 1
            self.send_message_to_player(player, f"A resposta correta seria: {self.current_answer}")
        self.do_play()


    def do_play(self):
        self.is_game_started = True
        self.send_message_to_all_players(f"INFO\tVamos para a {self.qt_questions_made+1}ª pergunta!")
        sleep(2)
        if self.qt_questions_made < 5:
            index = randint(0, len(self.QUESTIONS)-1)
            self.current_question = self.QUESTIONS.pop(index)
            self.current_answer = self.ANSWERS.pop(index)
            self.ask_and_wait_or_timeout()
            self.qt_questions_made += 1
        else:
            self.finish_game()

    def start_game(self):
        self.send_message_to_all_players(f'INFO\tVocê terá até {self.QUEST_TIME} segundos para responder às '
                                         f'perguntas. Seja rápido!')
        sleep(2)

        self.send_message_to_all_players("INFO\tO jogo inicará em 5 segundos!")  # warn the players
        self.show_message("O jogo vai iniciar em 5 segundos!")  # warn the server
        game_timer = threading.Timer(5, self.do_play)
        game_timer.start()

    def wait_for_players_and_start(self):
        """Wait for players to join the game and start the game"""

        try:
            self.start_server_timer()
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

        except GameOver:
            self.show_message("Jogo finalizado!")
            self.send_message_to_all_players("INFO\tJogo finalizado!")
            self.shutdown_server()

    def send_message_to_player(self, player_identifier, response):
        player_address = self.players_list[player_identifier]
        self.show_message(f"Enviando {response} para {player_address}")
        with self.session_lock:
            self.server_socket.sendto(response.encode(self.ENCODING), player_address)

    def get_game_details(self):
        details = f"INFO\t{len(self.players_list)}/{self.max_num_of_players} Jogadores\nTempo restante de " \
                  f"aguardo: {self.get_remaining_time_to_begin()} segundos"
        return details

    def handle_join_request_player(self, player_address):

        if len(self.players_list) >= self.max_num_of_players:
            response = "DENIED\t GAME IS FULL"

        elif self.is_game_started:
            response = "DENIED\t GAME IS ON GOING"
        else:
            player_identifier = str(uuid4())
            response = "ALLOWED\t"+player_identifier
            self.add_player_to_list(player_identifier, player_address)

        self.show_message(f' Response: {response} // to player: {player_address}')
        self.send_message_to_player(player_identifier, response)
        self.send_message_to_player(player_identifier,
                                    self.get_game_details())
        self.can_game_start()


def main():
    """ Create game server """
    game_server = GameServer('localhost', 4051, 2)
    game_server.configure_server()
    game_server.wait_for_players_and_start()
    # Game is started automatically


if __name__ == '__main__':
    main()
