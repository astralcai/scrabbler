import os
import pickle
import string
import json
from enum import Enum
from scrabbler.dictionary import Dictionary
import utilities.logger as logger

script_dir = os.path.dirname(__file__)
full_tile_path = os.path.join(script_dir, "../resources/tile_list.txt")
full_board_path = os.path.join(script_dir, "../resources/board.json")


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

    def set_attribute(self, attribute):
        self._attribute = attribute

    def get_cross_set(self, direction):
        if not self._cross_set:
            return list(string.ascii_lowercase)
        if direction == CrossSetDirection.HORIZONTAL:
            return self._cross_set['horizontal']
        elif direction == CrossSetDirection.VERTICAL:
            return self._cross_set['vertical']
        else:
            logger.error("The direction provided (" + direction + ") is invalid")


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
