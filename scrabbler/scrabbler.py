import os
import pickle
import string
import json
import gzip
from enum import Enum
from scrabbler.dictionary import Dictionary
import utilities.logger as logger
import utilities.errors as errors

script_dir = os.path.dirname(__file__)
full_tile_path = os.path.join(script_dir, "../resources/tile_list.txt")
full_board_path = os.path.join(script_dir, "../resources/board.json")
full_saved_games_dir = os.path.join(script_dir, "../games/")


class Game(object):
    """A data structure to store all information about a game"""

    __slots__ = '_tile_set', '_board', '_dictionary'

    def __init__(self, filename=None):
        with open(full_tile_path) as f:
            tiles = f.readlines()
        self._tile_set = dict((t, int(s)) for t, s in
                              [tile.split() for tile in [x.rstrip('\n') for x in tiles]])
        self._dictionary = Dictionary()
        if filename:
            self._load_from_file(filename)
        else:
            self._board = Board()

    def _save(self, filename):
        """saves an unfinished game to disk"""

        with gzip.open(os.path.join(full_saved_games_dir, filename), "wb") as f:
            f.write(pickle.dumps(self._board))
        logger.info("game object stored")

    def _load_from_file(self, filename):
        """loads an unfinished game from a file"""

        with gzip.open(os.path.join(full_saved_games_dir, filename), "rb") as f:
            logger.info("file found and opened")
            self._board = pickle.loads(f.read())

    def find_move(self, rack):
        """finds the best move given the rack"""

    def place_move(self, start_square, direction, word):
        """places a move on the board"""

        if direction == 'across':
            self._play_across(start_square, word)
        elif direction == 'down':
            self._play_down(start_square, word)
        else:
            raise errors.InvalidInputError(
                "Invalid direction argument: " + direction + ". Please use 'across' or 'down'")

    def _play_across(self, start_square, word):
        row, col = start_square
        if len(word) > self._board.get_size() - row:
            logger.error("The word is too long to fit in this position, squares needed: %d, squares left: %d"
                         % (len(word), self._board.get_size() - row))
            return
        offset = 0
        try:
            for char in word:
                self._board.get_square(row, col + offset).set_tile(char)
                offset = offset + 1
        except errors.IllegalMoveError:
            while offset > 0:
                offset = offset - 1
                self._board.get_square(row, col + offset).remove_tile()
            return
        for offset in range(len(word)):
            self._update_cross_set((row - 1, col + offset), MoveDirection.ACROSS)
            self._update_cross_set((row + 1, col + offset), MoveDirection.ACROSS)
        self._update_cross_set((row, col - len(word) - 1), MoveDirection.DOWN)
        self._update_cross_set((row, col), MoveDirection.DOWN)

    def _play_down(self, start_square, word):
        row, col = start_square
        if len(word) > self._board.get_size() - col:
            logger.error("The word is too long to fit in this position, squares needed: %d, squares left: %d"
                         % (len(word), self._board.get_size() - col))
            return
        offset = 0
        try:
            for char in word:
                self._board.get_square(row + offset, col).set_tile(char)
                offset = offset + 1
        except errors.IllegalMoveError:
            while offset > 0:
                offset = offset - 1
                self._board.get_square(row + offset, col).remove_tile()
            return
        for offset in range(len(word)):
            self._update_cross_set((row + offset, col - 1), MoveDirection.DOWN)
            self._update_cross_set((row + offset, col + 1), MoveDirection.DOWN)
        self._update_cross_set((row - 1, col), MoveDirection.ACROSS)
        self._update_cross_set((row + len(word), col), MoveDirection.ACROSS)

    def _update_cross_set(self, square_coordinates, direction):
        """calculate and update the cross sets for the squares"""

        row, col = square_coordinates

        if row < 0 or row >= self._board.get_size() or col < 0 or col >= self._board.get_size():
            return

        square = self._board.get_square(row, col)

        if square.has_tile():
            return
        if direction == MoveDirection.ACROSS:
            return
        elif direction == MoveDirection.DOWN:
            return
        else:
            raise errors.InvalidInputError("The direction provided (" + direction + ") is invalid")


class Board(object):
    """a data structure that stores all squares on a board"""

    __slots__ = '_board', '_size'

    def __init__(self):
        """sets up the board as a list of concatenated lists of squares"""

        self._board = list()
        with open(full_board_path) as json_data:
            board_data = json.load(json_data)
        self._size = board_data['size']
        for row in range(self._size):
            for square in range(self._size):
                self._board.append(Square())
        special_squares = board_data['special_squares']
        for coordinate in special_squares['DL']:
            self._board[coordinate[0] * self._size + coordinate[1]].set_attribute(SquareAttribute.DL)
        for coordinate in special_squares['DW']:
            self._board[coordinate[0] * self._size + coordinate[1]].set_attribute(SquareAttribute.DW)
        for coordinate in special_squares['TL']:
            self._board[coordinate[0] * self._size + coordinate[1]].set_attribute(SquareAttribute.TL)
        for coordinate in special_squares['TW']:
            self._board[coordinate[0] * self._size + coordinate[1]].set_attribute(SquareAttribute.TW)

    def get_square(self, row, col):
        return self._board[row * self._size + col]

    def get_size(self):
        return self._size


class Square(object):
    """A data structure that represents a square on the board"""

    __slots__ = '_cross_set', '_tile', '_attribute'

    def __init__(self):
        self._cross_set = None
        self._tile = None
        self._attribute = SquareAttribute.NULL
        self._cross_set = {'down': None,
                           'across': None}

    def set_attribute(self, attribute):
        self._attribute = attribute

    def has_tile(self):
        return self._tile is not None

    def get_tile(self):
        return self._tile

    def set_tile(self, char):
        if self._tile:
            raise errors.IllegalMoveError("a tile already exists on this square")
        elif char < 'a' or char > 'z':
            raise errors.IllegalMoveError("illegal move! Letter placed must be in the alphabet")
        self._tile = char

    def remove_tile(self):
        self._tile = None

    def update_cross_set(self, direction, cross_set):
        if direction == MoveDirection.ACROSS:
            self._cross_set['across'] = cross_set
        elif direction == MoveDirection.DOWN:
            self._cross_set['down'] = cross_set
        else:
            raise errors.InvalidInputError("The direction provided (" + direction + ") is invalid")

    def get_cross_set(self, direction):
        if direction == MoveDirection.ACROSS:
            direction_string = 'across'
        elif direction == MoveDirection.DOWN:
            direction_string = 'down'
        else:
            raise errors.InvalidInputError("The direction provided (" + direction + ") is invalid")
        if self._cross_set[direction_string]:
            return self._cross_set[direction_string]
        else:
            return list(string.ascii_lowercase)


class Move(object):
    """A data structure that represents a move"""

    __slots__ = '_word', '_start_square', '_direction', '_score'

    def __init__(self, word, start_square, direction, score):
        self._word = word
        self._start_square = start_square
        self._direction = direction
        self._score = score

    def __str__(self):
        direction_string = ""
        if self._direction == MoveDirection.ACROSS:
            direction_string = "across"
        elif self._direction == MoveDirection.DOWN:
            direction_string = "down"
        return "Play '%s' from square (%d, %d) %s to get %d points." % (
            self._word, self._start_square[0], self._start_square[1], direction_string, self._score)


class SquareAttribute(Enum):
    """An enum for special attributes for a square"""

    NULL = 0
    DW = 1
    DL = 2
    TW = 3
    TL = 4


class MoveDirection(Enum):
    """An enum for directions specified for cross set generation"""

    ACROSS = 0
    DOWN = 1
