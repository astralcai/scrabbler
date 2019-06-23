import os
import pickle
import string
import json
import gzip
from enum import Enum
from scrabbler.dictionary import Dictionary, DELIMITER, Arc
import utilities.logger as logger
import utilities.errors as errors

script_dir = os.path.dirname(__file__)
resource_dir = os.path.join(script_dir, "../resources")
full_saved_games_dir = os.path.join(script_dir, "../games/")


class Game:
    """stores information about a game"""

    def __init__(self, filename="", board="wwf15"):
        """constructor for a game

        Args:
            filename: the filename of a saved game if specified

        """

        logger.info("Initializing game...")

        # load the state of the board from a saved game
        if filename:
            filename = filename + ".p" if filename[-2:] != ".p" else filename
            logger.info("loading saved game from \"{}\"...".format(filename))
            game_data = self.__load_game_data_from_file(filename)
            self.board_type = game_data["board_type"]
            self.board = game_data["board"]
            self.filename = game_data["filename"]
        else:
            logger.info("starting new game and initializing board...")
            self.board_type = board
            self.board = Board(board)
            self.filename = None

        resource_directory = os.path.join(resource_dir, self.board_type)
        tile_path = os.path.join(resource_directory, "tile_list.txt")
        dictionary_path = os.path.join(resource_directory, "dictionary.txt")
        saved_dictionary_path = os.path.join(resource_directory, "dictionary.p")

        # load the list of tiles and their corresponding scores
        self.tiles = self.__load_tile_set_from_file(tile_path)

        # load a saved dictionary object or construct a new one
        if os.path.exists(saved_dictionary_path):
            logger.info("loading saved dictionary file...")
            self.dictionary = Dictionary.load_from_pickle(saved_dictionary_path)
        else:
            logger.info("constructing dictionary...")
            self.dictionary = Dictionary.construct_with_text_file(dictionary_path)
            logger.info("saving dictionary structure...")
            self.dictionary.store(saved_dictionary_path)

        logger.info("Game initialized successfully.")

    def save(self, filename=None):
        """saves an unfinished game to disk"""

        if not os.path.exists(full_saved_games_dir):
            os.makedirs(full_saved_games_dir)
        self.filename = filename if filename else self.filename if self.filename else generate_file_name()
        logger.info("Saving game to file \"{}\"...".format(self.filename))
        game_data = {
            "board_type": self.board_type,
            "board": self.board
            "name": self.filename
        }
        with gzip.open(os.path.join(full_saved_games_dir, "{}.p".format(filename)), "wb") as f:
            f.write(pickle.dumps(game_data))
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
            coordinate = self.board.offset(coordinate, direction, 1)

    def find_best_moves(self, rack, num=5):
        """returns the five best moves"""

        rack = list(rack)

        mid = int(self.board.size / 2)
        if self.board.empty:
            moves = self.board.generate_moves((mid, mid), "across", rack, self.dictionary, self.tiles, {})
        else:
            across_moves = self.board.find_best_moves(rack, "across", self.dictionary, self.tiles)
            down_moves = self.board.find_best_moves(rack, "down", self.dictionary, self.tiles)
            moves = across_moves + down_moves

        moves.sort(key=lambda move_: move_.score, reverse=True)
        for move in moves[0:num]:
            print(move)

    def show(self):
        """prints the board to terminal"""
        print(self.board)
    
    @staticmethod
    def __load_tile_set_from_file(filename) -> dict:
        with open(filename) as f:
            tiles = f.readlines()  # ['A 1\n', 'B 4\n', 'C 4\n', 'D 2\n', ...]
        return dict((tile[0], int(tile.strip("\n")[2:])) for tile in tiles)  # {'A': '1', 'B': '4', 'C': '4', ...}

    @staticmethod
    def __load_game_data_from_file(filename) -> dict:
        """loads an unfinished game from a file"""
        with gzip.open(os.path.join(full_saved_games_dir, filename), "rb") as f:
            return pickle.loads(f.read())


class Board:
    """stores a board and all current pieces on the board"""

    def __init__(self, board_type):
        """sets up the board as a list of concatenated lists of squares"""

        self.board_type = board_type
        self.empty = True

        board_path = os.path.join(resource_dir, board_type)
        full_board_path = os.path.join(board_path, "board.json")

        with open(full_board_path) as json_data:
            board_data = json.load(json_data)
        self.size = board_data['size']
        self._board = [Square() for _ in range(self.size * self.size)]

        special_squares = board_data['special_squares']
        for coordinate in special_squares['DL']:
            self.square(*coordinate).effect = SquareEffect.DL
        for coordinate in special_squares['DW']:
            self.square(*coordinate).effect = SquareEffect.DW
        for coordinate in special_squares['TL']:
            self.square(*coordinate).effect = SquareEffect.TL
        for coordinate in special_squares['TW']:
            self.square(*coordinate).effect = SquareEffect.TW

    def __str__(self):
        board_string = ""
        for i in range(self.size):
            row = (self.square(i, j).tile for j in range(self.size))
            row_string = "  ".join(tile if tile else "-" for tile in row)
            board_string = board_string + row_string + "\n"
        return board_string

    def square(self, row, col):
        """gets the square on the given coordinate, return None if out of bounds"""
        if any(index < 0 or index >= self.size for index in [row, col]):
            return None
        index = row * self.size + col
        return self._board[index] if index < self.size * self.size else None

    def place_word(self, start_coordinate, word, direction):
        """puts a word on the board"""

        end_coordinate = self.offset(start_coordinate, direction, len(word))
        if any(index > self.size for index in end_coordinate):
            raise errors.IllegalMoveError("The length of word is out of bounds of the board")

        coordinate = start_coordinate
        offset = 0
        word = word.upper()
        try:
            for char in word:
                self.square(*coordinate).tile = char
                offset = offset + 1
                coordinate = self.offset(start_coordinate, direction, offset)
        except errors.IllegalMoveError:
            offset = offset - 1
            while offset >= 0:
                self.square(*coordinate).remove_tile()
                offset = offset - 1
                coordinate = self.offset(start_coordinate, direction, offset)
            raise errors.IllegalMoveError("Cannot place this word on the given coordinates")
        self.empty = False

    def generate_moves(self, anchor, direction, rack, dictionary, tile_set, anchors_used):
        """generate all possible moves from a given anchor with the current rack"""

        from copy import deepcopy

        plays = []

        def gen(pos_, word_, rack_, arc_, new_tiles_, wild_cards_):

            rack_ = deepcopy(rack_)

            coordinate_ = self.offset(anchor, direction, pos_)
            tile_ = self.square(*coordinate_).tile
            if tile_:
                new_tiles_ = deepcopy(new_tiles_)
                go_on(pos_, tile_, word_, rack_, arc_.get_next(tile_), arc_, new_tiles_, wild_cards_)
            elif rack_:
                other_direction = "down" if direction == "across" else "across"
                for letter_ in (x for x in set(rack_) if x in self.square(*coordinate_).cross_set(other_direction)):
                    tmp_rack_ = deepcopy(rack_)
                    tmp_rack_.remove(letter_)
                    tmp_new_tiles_ = deepcopy(new_tiles_)
                    tmp_new_tiles_.append(pos_)
                    go_on(pos_, letter_, word_, tmp_rack_, arc_.get_next(letter_), arc_, tmp_new_tiles_, wild_cards_)
                if "?" in rack_:
                    for letter_ in (x for x in set(string.ascii_uppercase) if
                                    x in self.square(*coordinate_).cross_set(other_direction)):
                        tmp_rack_ = deepcopy(rack_)
                        tmp_rack_.remove("?")
                        tmp_new_tiles_ = deepcopy(new_tiles_)
                        tmp_new_tiles_.append(pos_)
                        tmp_wild_cards_ = deepcopy(wild_cards_)
                        tmp_wild_cards_.append(pos_)
                        next_arc = arc_.get_next(letter_)
                        go_on(pos_, letter_, word_, tmp_rack_, next_arc, arc_, tmp_new_tiles_, tmp_wild_cards_)

        def go_on(pos_, char_, word_, rack_, new_arc_, old_arc_, new_tiles_, wild_cards_):

            directly_left = self.offset(anchor, direction, pos_ - 1)
            directly_left_square = self.square(*directly_left)
            directly_right = self.offset(anchor, direction, pos_ + 1)
            directly_right_square = self.square(*directly_right)
            right_side = self.offset(anchor, direction, 1)
            right_side_square = self.square(*right_side)

            if pos_ <= 0:
                word_ = char_ + word_
                left_good = not directly_left_square or not directly_left_square.tile
                right_good = not right_side_square or not right_side_square.tile
                if char_ in old_arc_.letter_set and left_good and right_good and new_tiles_:
                    record_play(pos_, word_, rack_, new_tiles_, wild_cards_)
                if new_arc_:
                    if directly_left_square and directly_left not in anchors_used:
                        gen(pos_ - 1, word_, rack_, new_arc_, new_tiles_, wild_cards_)
                    new_arc_ = new_arc_.get_next(DELIMITER)
                    if new_arc_ and left_good and right_side_square:
                        gen(1, word_, rack_, new_arc_, new_tiles_, wild_cards_)
            else:
                word_ = word_ + char_
                right_good = not directly_right_square or not directly_right_square.tile
                if char_ in old_arc_.letter_set and right_good and new_tiles_:
                    left_most = pos_ - len(word_) + 1
                    record_play(left_most, word_, rack_, new_tiles_, wild_cards_)
                if new_arc_ and directly_right_square:
                    gen(pos_ + 1, word_, rack_, new_arc_, new_tiles_, wild_cards_)

        def record_play(offset_, word_, current_rack_, new_tile_register_, wild_cards_):
            start_square = self.offset(anchor, direction, offset_)
            effects_ = []
            word_score_ = 0
            cross_score_ = 0
            for pos_, letter_ in enumerate(word_):
                pos = pos_ + offset_
                coordinate_ = self.offset(anchor, direction, pos)
                tile_score = tile_set[letter_] if pos not in wild_cards_ else 0
                if pos in new_tile_register_:
                    effect = self.square(*coordinate_).effect
                    if effect == SquareEffect.DL:
                        tile_score = tile_score * 2
                    elif effect == SquareEffect.TL:
                        tile_score = tile_score * 3
                    elif effect in [SquareEffect.DW, SquareEffect.TW]:
                        effects_.append(effect)
                    cross_score_ = cross_score_ + cross_score(tile_score, coordinate_, effect)
                word_score_ = word_score_ + tile_score
            for effect_ in effects_:
                if effect_ == SquareEffect.TW:
                    word_score_ = word_score_ * 3
                elif effect_ == SquareEffect.DW:
                    word_score_ = word_score_ * 2
            if not current_rack_:
                bingo_bonus = 50 if self.board_type == "scrabble" else 35
                word_score_ = word_score_ + bingo_bonus
            plays.append(Move(word_, start_square, direction, word_score_ + cross_score_))

        def cross_score(tile_score_, coordinate_, effect_):

            other_direction = "across" if direction == "down" else "down"
            top = self.fast_forward(coordinate_, other_direction, -1)
            bottom = self.fast_forward(coordinate_, other_direction, 1)
            if top == coordinate_ and bottom == coordinate_:
                return 0  # so that tiles are not double counted

            word_score_ = tile_score_

            current_square_ = top
            while current_square_ != coordinate_:
                # go from top down
                tile_ = self.square(*current_square_).tile
                word_score_ = word_score_ + tile_set[tile_]
                current_square_ = self.offset(current_square_, other_direction, 1)
            current_square_ = bottom
            while current_square_ != coordinate_:
                # go from bottom up
                tile_ = self.square(*current_square_).tile
                word_score_ = word_score_ + tile_set[tile_]
                current_square_ = self.offset(current_square_, other_direction, -1)

            if effect_ == SquareEffect.TW:
                word_score_ = word_score_ * 3
            elif effect_ == SquareEffect.DW:
                word_score_ = word_score_ * 2

            return word_score_

        initial_arc = Arc("", dictionary.root)
        gen(0, "", deepcopy(rack), initial_arc, [], [])

        return plays

    def find_best_moves(self, rack, direction, dictionary, tile_set):

        anchors_used = []
        moves = []
        other_direction = "across" if direction == "down" else "down"

        def is_anchor(coordinate_):
            right = self.offset(coordinate_, direction, 1)
            above = self.offset(coordinate_, other_direction, -1)
            below = self.offset(coordinate_, other_direction, 1)
            cross_squares = (self.square(*block) for block in [above, below])
            if not self.square(*coordinate_).tile:
                return any(square and square.tile for square in cross_squares)
            return not self.square(*right) or not self.square(*right).tile

        corner = (0, 0)
        for i in range(self.size):
            left_most = self.offset(corner, other_direction, i)
            for j in range(self.size):
                current = self.offset(left_most, direction, j)
                if is_anchor(current):
                    moves.extend(self.generate_moves(current, direction, rack, dictionary, tile_set, anchors_used))
                    anchors_used.append(current)
        return moves

    def update_cross_set(self, start_coordinate, direction, dictionary):
        """update cross sets affected by this coordinate"""

        def __clear_cross_sets(start_coordinate_, direction_):
            right_most_square = self.fast_forward(start_coordinate_, direction_, 1)
            right_square_ = self.offset(right_most_square, direction_, 1)
            if self.square(*right_square_):
                self.square(*right_square_).set_cross_set(direction_, {})
            left_most_square = self.fast_forward(start_coordinate_, direction_, -1)
            left_square_ = self.offset(left_most_square, direction_, -1)
            if self.square(*left_square_):
                self.square(*left_square_).set_cross_set(direction_, {})

        def __check_candidate(coordinate_, candidate_, direction_, step):
            last_arc_ = candidate_
            state_ = candidate_.destination
            next_square_ = self.offset(coordinate_, direction_, step)
            while self.square(*next_square_) and self.square(*next_square_).tile:
                coordinate_ = next_square_
                tile_ = self.square(*coordinate_).tile
                last_arc_ = state_.arcs[tile_] if tile_ in state_.arcs else None
                if not last_arc_:
                    return False
                state_ = last_arc_.destination
                next_square_ = self.offset(coordinate_, direction_, step)
            return self.square(*coordinate_).tile in last_arc_.letter_set

        if not self.square(*start_coordinate) or not self.square(*start_coordinate).tile:
            return  # do not do anything if this square is out of bounds or empty
        end_coordinate = self.fast_forward(start_coordinate, direction, 1)

        # traverse the dictionary in reverse order of the word
        coordinate = end_coordinate
        last_state = dictionary.root
        state = last_state.get_next(self.square(*coordinate).tile)
        next_square = self.offset(coordinate, direction, -1)
        while self.square(*next_square) and self.square(*next_square).tile:
            coordinate = next_square
            last_state = state  # this saves the previous state before incrementing
            state = state.get_next(self.square(*coordinate).tile)
            if not state:  # if non-words are found existing on the board
                __clear_cross_sets(start_coordinate, direction)
                return
            next_square = self.offset(coordinate, direction, -1)

        # now that we're at the head of the word
        right_square = self.offset(end_coordinate, direction, 1)
        left_square = self.offset(coordinate, direction, -1)

        # check special case where there is a square with tiles on both sides
        left_of_left = self.offset(left_square, direction, -1)
        right_of_right = self.offset(right_square, direction, 1)

        if self.square(*left_of_left) and self.square(*left_of_left).tile:
            candidates = (arc for arc in state if arc.char != "#")
            cross_set = set(
                candidate.char for candidate in candidates if __check_candidate(left_square, candidate, direction, -1))
            self.square(*left_square).set_cross_set(direction, cross_set)
        elif self.square(*left_square):
            cross_set = last_state.get_arc(self.square(*coordinate).tile).letter_set
            self.square(*left_square).set_cross_set(direction, cross_set)

        if self.square(*right_of_right) and self.square(*right_of_right).tile:
            end_state = state.get_next(DELIMITER)
            candidates = (arc for arc in end_state if arc != "#") if end_state else {}
            cross_set = set(
                candidate.char for candidate in candidates if __check_candidate(right_square, candidate, direction, 1))
            self.square(*right_square).set_cross_set(direction, cross_set)
        elif self.square(*right_square):
            end_arc = state.get_arc(DELIMITER)
            cross_set = end_arc.letter_set if end_arc else {}
            self.square(*right_square).set_cross_set(direction, cross_set)

    @staticmethod
    def offset(coordinate, direction, offset):
        if direction == "across":
            new_coordinate = coordinate[0], coordinate[1] + offset
        elif direction == "down":
            new_coordinate = coordinate[0] + offset, coordinate[1]
        else:
            raise TypeError("invalid direction specified: {}".format(direction))
        return new_coordinate

    def fast_forward(self, start_coordinate, direction, step):
        """fast forward the coordinate to the last letter in the word"""
        coordinate = start_coordinate
        next_coordinate = self.offset(start_coordinate, direction, step)
        while self.square(*next_coordinate) and self.square(*next_coordinate).tile:
            coordinate = next_coordinate
            next_coordinate = self.offset(coordinate, direction, step)
        return coordinate


class Square:
    """a square on the board

    Attributes:
        _tile: the tile occupying this square
        _cross_set: the set of letters that can form valid crosswords
        _effect: score multiplier if present

    """

    __slots__ = "_cross_set", "_tile", "_effect"

    def __init__(self):
        self._tile = None
        self._effect = SquareEffect.NULL
        self._cross_set = {'down': set(string.ascii_uppercase), 'across': set(string.ascii_uppercase)}

    @property
    def tile(self):
        return self._tile

    @tile.setter
    def tile(self, char):
        if self.tile and char != self.tile:
            raise errors.IllegalMoveError("a tile already exists on this square")
        if char < 'A' or char > 'Z':
            raise errors.IllegalMoveError("illegal move! Letter placed must be in the alphabet")
        self._tile = char

    def remove_tile(self):
        self._tile = None

    def cross_set(self, direction):
        return self._cross_set[direction]

    def set_cross_set(self, direction, new_set):
        self._cross_set[direction] = new_set

    @property
    def effect(self):
        return self._effect

    @effect.setter
    def effect(self, effect):
        self._effect = effect


class Move(object):
    """A data structure that represents a move"""

    __slots__ = 'word', 'start_square', 'direction', 'score'

    def __init__(self, word, start_square, direction, score):
        self.word = word
        self.start_square = start_square
        self.direction = direction
        self.score = score

    def __str__(self):
        return "Play \"{}\" {} from {} to get {} points.".format(
            self.word, self.direction, self.start_square, self.score)


class SquareEffect(Enum):
    """An enum for special attributes for a square"""

    NULL = 0
    DW = 1
    DL = 2
    TW = 3
    TL = 4


def generate_file_name():
    """generates a filename for a saved game based on the time"""
    import datetime
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    filename = "game saved at {}".format(now)
    return filename
