import utilities.logger as logger


class ScrabbleBaseError(Exception):
    """This is the base error for all exceptions in this package"""

    def __init__(self, message):
        super().__init__(message)
        logger.error(message)


class IllegalMoveError(ScrabbleBaseError):
    """This error should be raised when an illegal move is placed"""

    def __init__(self, message):
        super(message)


class InvalidInputError(ScrabbleBaseError):
    """This error should be raised when an input argument is invalid"""

    def __init__(self, message):
        super(message)
