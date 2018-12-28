"""This file implements the dictionary as a finite state machine

The algorithm used is called GADDAG.

References:
    https://ericsink.com/downloads/faster-scrabble-gordon.pdf
    http://www.cs.cmu.edu/afs/cs/academic/class/15451-s06/www/lectures/scrabble.pdf

"""

import pickle
import gzip

DELIMITER = "#"


class Dictionary:
    """The full dictionary implemented as a GADDAG

    Attributes:
        root (State): the root state of the lexicon

    """

    __slots__ = "root"

    def __init__(self, root: "State"):
        self.root = root

    def store(self, filename: str):
        """stores a GADDAG data structure to the designated file"""

        with gzip.open(filename, "wb") as f:
            f.write(pickle.dumps(self.root))

    @classmethod
    def construct_with_text_file(cls, filename: str) -> "Dictionary":
        with open(filename) as f:
            words = f.readlines()
        word_list = set(x.rstrip('\n') for x in words)
        root = cls.__construct_lexicon_with_list_of_words(word_list)
        return cls(root)

    @classmethod
    def load_from_pickle(cls, filename: str) -> "Dictionary":
        root = cls.__load_picked_dictionary_from_file(filename)
        return cls(root)

    @staticmethod
    def __construct_lexicon_with_list_of_words(word_list: set) -> "State":
        """creates a dictionary lexicon with a set of words

        Args:
            word_list: the set of words

        Returns:
            the root state of the lexicon

        """
        root = State()
        for word in word_list:
            word = word.upper()
            Dictionary.__add_word(root, word)
        return root

    @staticmethod
    def __load_picked_dictionary_from_file(filename) -> "State":
        """loads a GADDAG data structure from a file"""

        with gzip.open(filename, "rb") as f:
            return pickle.loads(f.read())

    @staticmethod
    def __add_word(root: "State", word: str):
        """adds a word to the lexicon

        Args:
            root: the root state of the lexicon
            word: the word to be added

        """

        # create path from the last letter to the first letter
        state = root
        for char in word[len(word):1:-1]:  # for i from n down to 3
            state = state.add_arc(char)
        state.add_final_arc(word[1], word[0])

        # create path from second last to last
        state = root
        for char in word[len(word) - 2::-1]:  # for i from n-1 down to 1
            state = state.add_arc(char)
        state = state.add_final_arc(DELIMITER, word[-1])

        # add the remaining paths
        for m in range(len(word) - 2, 0, -1):  # for m from n-2 down to 1
            destination = state
            state = root
            for char in word[m - 1::-1]:  # for i from m down to 1
                state = state.add_arc(char)
            state = state.add_arc(DELIMITER)
            state.add_arc(word[m], destination)  # keep the current state at the second last node


class State:
    """a state in a GADDAG"""

    __slots__ = "arcs", "letter_set"

    def __init__(self):
        self.arcs = dict()
        self.letter_set = set()

    def __iter__(self):
        for char in self.arcs:
            yield self.arcs[char]

    def __contains__(self, char):
        return char in self.arcs

    def get_arc(self, char) -> "Arc":
        return self.arcs[char] if char in self.arcs else None

    def add_arc(self, char: str, destination: "State" = None) -> "State":
        """adds an arc from this node for the given letter

        Args:
            char: the letter for this node
            destination: the state this arc leads to, a new state will be created if this
                is left blank

        Returns:
            the new state that this arc leads to

        """
        if char not in self.arcs:
            self.arcs[char] = Arc(char, destination)
        return self.get_next(char)

    def add_final_arc(self, char: str, final: str) -> "State":
        """adds a final arc from this node for the given letter

        this completes a word by adding the second provided letter into the letter set of the new arc

        Args:
            char: the letter for this arc
            final: the letter which completes the word

        Returns:
            the new state that this arc leads to

        """
        if char not in self.arcs:
            self.arcs[char] = Arc(char)
        self.get_next(char).add_letter(final)
        return self.get_next(char)

    def add_letter(self, char: str):
        self.letter_set.add(char)

    def get_next(self, char: str) -> "State":
        """Gets the node that the given letter leads to"""
        return self.arcs[char].destination if char in self.arcs else None


class Arc:
    """an arc in a GADDAG

    Attributes:
        char: the letter corresponding to this arc
        destination: the node that this arc leads to

    """

    __slots__ = "char", "destination"

    def __init__(self, char: str, destination: "State" = None):
        self.char = char
        if not destination:
            destination = State()
        self.destination = destination

    def __contains__(self, char: str):
        return char in self.destination.letter_set

    def __eq__(self, other: str):
        return other == self.char

    @property
    def letter_set(self):
        return self.destination.letter_set if self.destination else set()

    def get_next(self, char: str):
        return self.destination.arcs[char] if char in self.destination.arcs else None
