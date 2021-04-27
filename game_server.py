import threading
import server  # This is our own server
from uuid import uuid4
from time import time, sleep
from random import randint


class GameServer(server.Server):
    players_list = {}
    JOIN = 'JOIN'
    ANSWER = 'ANS'
    INFO = 'INFO'
    UPDATE_INFO = 'UPDT'
    QUESTIONS = []
    ANSWERS = []
    ENCODING = 'UTF-8'
    QUESTION = 'QST'
    REQUEST_ANSWER = 'RAN'
    players_score = {}
    players_who_answered = []
    QUEST_TIME = 10
    ANSWER_IS_CORRECT = "RGT"
    ANSWER_IS_WRONG = "WRG"

    def __init__(self, address, port, max_num_of_players):

        super().__init__(address, port)
        self.max_num_of_players = max_num_of_players
        self.session_lock = threading.Lock()  # Isso garante que executaremos as funções uma em cada thread

        self.max_wait_time = 30  # in seconds
        self.timer_started_at = None
        self.timer = None
        self.is_game_started = False
        self.qt_questions_made = 0
        self.current_question = None
        self.current_answer = None
        self.timer_to_wait_answer = None
        self.is_game_over = False
        self.timeout_already_covered = False
        self.was_scoreboard_shown = False
        self.all_answered = True

        with open('questions.txt', 'r', encoding='UTF-8') as file:
            for row in file:
                row = row.strip()
                question, answer = row.split('\t')
                self.QUESTIONS.append(question)
                self.ANSWERS.append(answer)

    def add_player_to_list(self, player_identifier, player_address):
        self.players_list[player_identifier] = player_address
        self.players_score[player_identifier] = 0

    def get_remaining_time_to_begin(self):
        return int(self.max_wait_time - (time() - self.timer_started_at))

    def handle_timer_wait_limit(self):
        self.timer = None
        self.timer_started_at = None
        self.show_message("Tempo encerrado, vamos iniciar o jogo!")
        self.send_message_to_all_players("INFO\tTempo de aguardo encerrado, iniciaremos o jogo!")
        sleep(5)
        self.start_game()

    def start_server_timer(self):
        self.show_message(f'Aguardaremos a entrada dos jogadores ou iniciaremos em {self.max_wait_time} segundos!')
        self.timer_started_at = time()
        self.timer = threading.Timer(self.max_wait_time, self.handle_timer_wait_limit)
        self.timer.start()
        sleep(2)

    def handle_player_answer(self, answer, identifier):
        if self.current_answer.upper() == answer.upper():
            self.players_score[identifier] += 25
            message = self.ANSWER_IS_CORRECT+"\tSua Resposta está correta!"

        else:
            self.players_score[identifier] -= 5
            message = f"WRG\tInfelizmente você errou! A resposta correta seria: {self.current_answer}"

        self.players_who_answered.append(identifier)
        self.send_message_to_player(identifier, message)

    def handle_player_request(self, data, player_address):
        """ Handle Player request """

        player_message = data.decode(self.ENCODING)
        player_operation = player_message.split('\t')
        player_wants_to = player_operation[0]

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
            sleep(1)
            self.all_answered = True

    def can_game_start(self):
        if len(self.players_list) == self.max_num_of_players:
            self.start_game()

    def send_message_to_all_players(self, message):
        for identifier, address in self.players_list.items():
            self.send_message_to_player(identifier, message)

    def finish_game(self):
        self.is_game_started = False
        self.is_game_over = True

    def ask_and_wait_or_timeout(self):
        self.players_who_answered = []
        self.send_message_to_all_players(self.QUESTION+"\t"+self.current_question)
        sleep(4)
        self.send_message_to_all_players(self.REQUEST_ANSWER)
        while not self.all_answered:
            try:
                data, player_address = self.server_socket.recvfrom(self.BUFFER_SIZE)
                self.handle_player_request(data, player_address)
            except OSError:
                self.timeout_quest_time()
                pass

    def timeout_quest_time(self):
        with self.session_lock:
            if not self.timeout_already_covered:
                self.send_message_to_all_players("INFO\tTempo esgotado!")
                players_who_didnt_answered = [identifier for identifier in self.players_list if identifier
                                              not in self.players_who_answered]
                for player in players_who_didnt_answered:
                    self.players_score[player] -= 1
                    self.send_message_to_player(player, f"A resposta correta seria: {self.current_answer}")
                self.timeout_already_covered = True
                self.all_answered = True

    def start(self):
        self.is_game_started = True
        self.send_message_to_all_players("INFO\tPreparados?")
        self.do_play()

    def do_play(self):

        while True:
            if self.is_game_over:
                self.show_scoreboard()
                self.send_message_to_all_players("END\tPartida finalizada!")
                self.shutdown_server()
                break
            else:
                try:
                    if self.qt_questions_made < 5:
                        if self.all_answered:
                            self.send_message_to_all_players(f"INFO\tVamos para a {self.qt_questions_made + 1}ª pergunta!")
                            sleep(3)
                            index = randint(0, len(self.QUESTIONS)-1)
                            self.current_question = self.QUESTIONS.pop(index)
                            self.current_answer = self.ANSWERS.pop(index)
                            self.timeout_already_covered = False
                            self.qt_questions_made += 1
                            self.all_answered = False
                            self.ask_and_wait_or_timeout()
                    else:
                        self.finish_game()
                except OSError:
                    continue
                except KeyboardInterrupt:
                    self.shutdown_server()

    def start_game(self):
        self.send_message_to_all_players(f'INFO\tVocê terá até {self.QUEST_TIME} segundos para responder às '
                                         f'perguntas. Seja rápido!')
        sleep(10)

        self.send_message_to_all_players("INFO\tO jogo inicará em 5 segundos!")  # warn the players
        self.show_message("O jogo vai iniciar em 5 segundos!")  # warn the server
        game_timer = threading.Timer(5, self.start)
        game_timer.start()

    def wait_for_players_and_start(self):
        """Wait for players to join the game and start the game"""

        try:
            self.start_server_timer()
            while not self.is_game_started:
                try:
                    data, player_address = self.server_socket.recvfrom(self.BUFFER_SIZE)
                    player_thread = threading.Thread(target=self.handle_player_request, args=(data, player_address))
                    player_thread.daemon = True
                    player_thread.start()
                except OSError as error:
                    # self.show_message(error)
                    continue

        except KeyboardInterrupt:
            self.shutdown_server()

    def send_message_to_player(self, player_identifier, response):
        player_address = self.players_list[player_identifier]
        # self.show_message(f"Enviando {response} para {player_address}")
        # with self.session_lock:
        self.server_socket.sendto(response.encode(self.ENCODING), player_address)

    def show_scoreboard(self):
        with self.session_lock:
            if not self.was_scoreboard_shown:
                ordered_players = dict(sorted(self.players_score.items(), key=lambda item: item[1], reverse=True))
                text = ""
                for position, key in enumerate(ordered_players):
                    text += "\n"
                    text += f"{position+1}º colocado - {key} - {ordered_players[key]} pontos"

                self.send_message_to_all_players("INFO\t"+text)
                self.was_scoreboard_shown = True

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

        self.send_message_to_player(player_identifier, response)
        self.send_message_to_player(player_identifier,
                                    self.get_game_details())
        self.can_game_start()


def main():
    """ Create game server """
    game_server = GameServer('localhost', 4051, 5)
    game_server.configure_server()
    game_server.wait_for_players_and_start()
    # Game is started automatically


if __name__ == '__main__':
    main()
