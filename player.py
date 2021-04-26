class Player:

    def __init__(self):
        self.identifier = None
        self.score = 0
        self.name = ""

    def increase_score(self, number_to_increase = 1):
        self.score += number_to_increase

    def reduce_score(self, number_to_reduce = 1):
        self.score -= number_to_reduce

    def get_identifier(self):
        return self.identifier

    def set_identifier(self, identifier):
        self.identifier = identifier
        return self.identifier

    def set_name(self, name):
        self.name = name
        return self.name
