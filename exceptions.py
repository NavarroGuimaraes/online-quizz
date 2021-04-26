class Error(Exception):
    pass


class PlayerCapacityReachedMaximum(Error):
    """ Raised when the number of players reached maximum """
    pass


class GameOver(Error):
    """ Raised when the game is over """
    pass
