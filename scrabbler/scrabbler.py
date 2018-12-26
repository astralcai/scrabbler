import os
import pickle
import string
import json
import gzip
from enum import Enum
from scrabbler.dictionary import Dictionary, DELIMITER
import utilities.logger as logger
import utilities.errors as errors

script_dir = os.path.dirname(__file__)
full_tile_path = os.path.join(script_dir, "../resources/tile_list.txt")
full_dict_path = os.path.join(script_dir, "../resources/dictionary.txt")
full_board_path = os.path.join(script_dir, "../resources/board.json")
full_saved_games_dir = os.path.join(script_dir, "../games/")
full_pickled_dict_path = os.path.join(script_dir, "../resources/dictionary.p")


class Game:
    """stores information about a game"""

    def __init__(self, filename=""):
        """constructor for a game

        Args:
            filename: the filename of a saved game if specified

        """

        logger.info("Initializing game...")

        # load the list of tiles and their corresponding scores
        self.tiles = self.__load_tile_set_from_file(full_tile_path)

        # load the state of the board from a saved game
        if filename:
            logger.info("loading saved game from \"{}\"...".format(filename))
            self.board = self.__load_board_from_file(filename)
        else:
            logger.info("starting new game and initializing board...")
            self.board = Board()

        # load a saved dictionary object or construct a new one
        if os.path.exists(full_pickled_dict_path):
            logger.info("loading saved dictionary file...")
            self.dictionary = Dictionary.load_from_pickle(full_pickled_dict_path)
        else:
            logger.info("constructing dictionary...")
            self.dictionary = Dictionary.construct_with_text_file(full_dict_path)
            logger.info("saving dictionary structure...")
            self.dictionary.store(full_pickled_dict_path)

        logger.info("Game initialized successfully.")

    def save(self, filename=None):
        """saves an unfinished game to disk"""

        if not os.path.exists(full_saved_games_dir):
            os.makedirs(full_saved_games_dir)
        filename = filename if filename else generate_file_name()
        logger.info("Saving game to file \"{}\"...".format(filename))
        with gzip.open(os.path.join(full_saved_games_dir, "{}.p".format(filename)), "wb") as f:
            f.write(pickle.dumps(self.board))
        logger.info("Game saved.")

    def play(self, start_square, word, direction):
        """play a move on the board"""

        self.board.place_word(start_square, word, direction)

        # update affected cross sets
        self.board.update_cross_set(start_square, direction, self.dictionary)
        other_direction = "across" if direction == "down" else "down"
        coordinate = start_square
        for _ in word:
            self.board.update_cross_set(coordinate, other_direction, self.dictionary)
            coordinate = self.board.increment(coordinate, direction, 1)

    @staticmethod
    def __load_tile_set_from_file(filename) -> dict:
        with open(filename) as f:
            tiles = f.readlines()  # ['A 1\n', 'B 4\n', 'C 4\n', 'D 2\n', ...]
        return dict((tile[0], tile[-2]) for tile in tiles)  # {'A': '1', 'B': '4', 'C': '4', ...}

    @staticmethod
    def __load_board_from_file(filename) -> "Board":
        """loads an unfinished game from a file"""

        with gzip.open(os.path.join(full_saved_games_dir, filename), "rb") as f:
            return pickle.loads(f.read())


class Board:
    """stores a board and all current pieces on the board"""

    def __init__(self):
        """sets up the board as a list of concatenated lists of squares"""

        with open(full_board_path) as json_data:
            board_data = json.load(json_data)
        self.size = board_data['size']
        self._board = [Square() for _ in range(self.size * self.size)]

        special_squares = board_data['special_squares']
        for coordinate in special_squares['DL']:
            self.square(*coordinate).attribute = SquareAttribute.DL
        for coordinate in special_squares['DW']:
            self.square(*coordinate).attribute = SquareAttribute.DW
        for coordinate in special_squares['TL']:
            self.square(*coordinate).attribute = SquareAttribute.TL
        for coordinate in special_squares['TW']:
            self.square(*coordinate).attribute = SquareAttribute.TW

    def square(self, row, col):
        """gets the square on the given coordinate, return None if out of bounds"""
        index = row * self.size + col
        return self._board[index] if index < self.size * self.size else None

    def place_word(self, start_coordinate, word, direction):
        """puts a word on the board"""

        end_coordinate = self.increment(start_coordinate, direction, len(word))
        if any(index < self.size for index in end_coordinate):
            raise errors.IllegalMoveError("The length of word is out of bounds of the board")

        coordinate = start_coordinate
        offset = 0
        try:
            for char in word:
                self.square(*coordinate).tile = char
                offset = offset + 1
                coordinate = self.increment(start_coordinate, direction, offset)
        except errors.IllegalMoveError:
            offset = offset - 1
            while offset >= 0:
                self.square(*coordinate).remove_tile()
                offset = offset - 1
                coordinate = self.increment(start_coordinate, direction, offset)
            raise errors.IllegalMoveError("Cannot place this word on the given coordinates")

    def update_cross_set(self, start_coordinate, direction, dictionary):
        """update cross sets affected by this coordinate"""

        def __clear_cross_sets(start_coordinate_, direction_):
            right_most_square = self.fast_forward(start_coordinate_, direction_, 1)
            right_square_ = self.increment(right_most_square, direction_, 1)
            if self.square(*right_square_):
                self.square(*right_square_).set_cross_set(direction_, {})
            left_most_square = self.fast_forward(start_coordinate_, direction_, -1)
            left_square_ = self.increment(left_most_square, direction_, -1)
            if self.square(*left_square_):
                self.square(*left_square_).set_cross_set(direction_, {})

        def __check_candidate(coordinate_, candidate_, direction_, step):
            last_arc_ = candidate_
            state_ = candidate_.destination
            next_square_ = self.increment(coordinate_, direction_, step)
            while self.square(*next_square_) and self.square(*next_square_).tile:
                coordinate_ = next_square_
                last_arc_ = state_.arcs[self.square(*coordinate_).tile]
                state_ = last_arc_.destination
                if not state:
                    return False
                next_square_ = self.increment(coordinate_, direction_, step)
            return self.square(*coordinate_).tile in last_arc_.letter_set

        if not self.square(*start_coordinate) or not self.square(*start_coordinate).tile:
            return  # do not do anything if this square is out of bounds or empty
        end_coordinate = self.fast_forward(start_coordinate, direction, 1)

        # traverse the dictionary in reverse order of the word
        coordinate = end_coordinate
        last_state = dictionary.root
        state = last_state.get_next(self.square(*coordinate).tile)
        next_square = self.increment(coordinate, direction, -1)
        while self.square(*next_square) and self.square(*next_square).tile:
            coordinate = next_square
            last_state = state  # this saves the previous state before incrementing
            state = state.get_next(self.square(*coordinate).tile)
            if not state:  # if non-words are found existing on the board
                __clear_cross_sets(start_coordinate, direction)
                return
            next_square = self.increment(coordinate, direction, -1)

        # now that we're at the head of the word
        right_square = self.increment(end_coordinate, direction, 1)
        left_square = self.increment(coordinate, direction, -1)

        # check special case where there is a square with tiles on both sides
        left_of_left = self.increment(left_square, direction, -1)
        right_of_right = self.increment(right_square, direction, 1)

        if self.square(*left_of_left) and self.square(*left_of_left).tile:
            candidates = (arc for arc in state if arc.char != "#")
            cross_set = set(
                candidate for candidate in candidates if __check_candidate(left_square, candidate, direction, -1))
            self.square(*left_square).set_cross_set(direction, cross_set)
        elif self.square(*left_square):
            cross_set = last_state.get_arc(self.square(*coordinate).tile).letter_set
            self.square(*left_square).set_cross_set(direction, cross_set)

        if self.square(*right_of_right) and self.square(*right_of_right).tile:
            end_state = state.get_next(DELIMITER)
            candidates = (arc for arc in end_state if arc != "#") if end_state else {}
            cross_set = set(
                candidate for candidate in candidates if __check_candidate(right_square, candidate, direction, 1))
            self.square(*left_square).set_cross_set(direction, cross_set)
        elif self.square(*right_square):
            end_arc = state.get_arc(DELIMITER)
            cross_set = end_arc.letter_set if end_arc else {}
            self.square(*right_square).set_cross_set(direction, cross_set)

    @staticmethod
    def increment(coordinate, direction, offset):
        if direction == "across":
            new_coordinate = coordinate[0] + offset, coordinate[1]
        elif direction == "down":
            new_coordinate = coordinate[0], coordinate[1] + offset
        else:
            raise TypeError("invalid direction specified: {}".format(direction))
        return new_coordinate

    def fast_forward(self, start_coordinate, direction, step):
        """fast forward the coordinate to the last letter in the word"""
        coordinate = start_coordinate
        next_coordinate = self.increment(start_coordinate, direction, step)
        while self.square(*next_coordinate) and self.square(*next_coordinate).tile:
            coordinate = next_coordinate
            next_coordinate = self.increment(start_coordinate, direction, step)
        return coordinate


class Square:
    """a square on the board

    Attributes:
        _tile: the tile occupying this square
        _cross_set: the set of letters that can form valid crosswords
        _attribute: score multiplier if present

    """

    __slots__ = "_cross_set", "_tile", "_attribute"

    def __init__(self):
        self._tile = None
        self._attribute = SquareAttribute.NULL
        self._cross_set = {'down': set(string.ascii_lowercase), 'across': set(string.ascii_lowercase)}

    @property
    def tile(self):
        return self._tile

    @tile.setter
    def tile(self, char):
        if self.tile and char != self.tile:
            raise errors.IllegalMoveError("a tile already exists on this square")
        if char < 'a' or char > 'z':
            raise errors.IllegalMoveError("illegal move! Letter placed must be in the alphabet")
        self._tile = char

    def remove_tile(self):
        self._tile = None

    def cross_set(self, direction):
        return self._cross_set[direction]

    def set_cross_set(self, direction, new_set):
        self._cross_set[direction] = new_set

    @property
    def attribute(self):
        return self._attribute

    @attribute.setter
    def attribute(self, attribute):
        self._attribute = attribute


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


def generate_file_name():
    """generates a filename for a saved game based on the time"""
    import datetime
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    filename = "game saved at {}".format(now)
    return filename
