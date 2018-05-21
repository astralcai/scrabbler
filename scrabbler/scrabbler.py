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

    def __init__(self):
        with open(full_tile_path) as f:
            tiles = f.readlines()
        self._tile_set = dict((t, int(s)) for t, s in
                              [tile.split() for tile in [x.rstrip('\n') for x in tiles]])
        self._dictionary = Dictionary()
        self._board = Board()


class Board(object):
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
            self._board[coordinate[0] * 15 + coordinate[1]].set_attribute(SquareAttribute.DL)
        for coordinate in special_squares['DW']:
            self._board[coordinate[0] * 15 + coordinate[1]].set_attribute(SquareAttribute.DW)
        for coordinate in special_squares['TL']:
            self._board[coordinate[0] * 15 + coordinate[1]].set_attribute(SquareAttribute.TL)
        for coordinate in special_squares['TW']:
            self._board[coordinate[0] * 15 + coordinate[1]].set_attribute(SquareAttribute.TW)

    def _get_square(self, row, col):
        return self._board[row * self._size + col]

    def _update_cross_sets(self):
        """calculate and update the cross sets for the squares"""


class Square(object):
    """A data structure that represents a square on the board"""

    __slots__ = '_cross_set', '_tile', '_attribute'

    def __init__(self):
        self._cross_set = None
        self._tile = None
        self._attribute = SquareAttribute.NULL
        self._cross_set = {'vertical': None,
                           'horizontal': None}

    def set_attribute(self, attribute):
        self._attribute = attribute

    def has_tile(self):
        return self._tile is not None

    def get_tile(self):
        return self._tile

    def update_cross_set(self, direction, cross_set):
        if direction == CrossSetDirection.HORIZONTAL:
            self._cross_set['horizontal'] = cross_set
        elif direction == CrossSetDirection.VERTICAL:
            self._cross_set['vertical'] = cross_set
        else:
            raise errors.InvalidInputError("The direction provided (" + direction + ") is invalid")

    def get_cross_set(self, direction):
        direction_string = ""
        if direction == CrossSetDirection.HORIZONTAL:
            direction_string = 'horizontal'
        elif direction == CrossSetDirection.VERTICAL:
            direction_string = 'vertical'
        else:
            raise errors.InvalidInputError("The direction provided (" + direction + ") is invalid")
        if self._cross_set[direction_string]:
            return self._cross_set[direction_string]
        else:
            return list(string.ascii_lowercase)


class SquareAttribute(Enum):
    """An enum for special attributes for a square"""

    NULL = 0
    DW = 1
    DL = 2
    TW = 3
    TL = 4


class CrossSetDirection(Enum):
    """An enum for directions specified for cross set generation"""

    HORIZONTAL = 0
    VERTICAL = 1
