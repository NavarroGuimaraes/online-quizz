import socket

# Server properties
server_ip = "127.0.0.1"
server_port = 616
server_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
server_socket.bind((server_ip, server_port))

# CONSTANTS
BUFFER_SIZE = 1024
WELCOME_MESSAGE = "Welcome to the best \"quizz\" ever! Oh sorry, I saw the list upside down :("
MAX_NUM_OF_PLAYERS = 6

# Game Variables
player_list = []
