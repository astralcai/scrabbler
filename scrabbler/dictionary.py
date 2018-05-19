import os
import pickle
import gzip
from utilities import logger

script_dir = os.path.dirname(__file__)
full_dict_path = os.path.join(script_dir, "../resources/dictionary.txt")
full_pickled_dict_path = os.path.join(script_dir, "../resources/dictionary.p")


class Dictionary(object):
    """A data structure to store all words in a dictionary

    The dictionary is stored as a partially minimized GADDAG. It uses the algorithm described
    in "A Faster Scrabble Move Generation Algorithm" written by Steven A. Gordon in 1997.

    Attributes:
        _root: A reference to the root edge of the GADDAG which points to the initial state


    """

    __slots__ = '_root'

    def __init__(self):
        logger.info("initializing dictionary object")
        if os.path.exists(full_pickled_dict_path):
            logger.info("loading from file")
            self._load_from_file()
            logger.info("dictionary object successfully instantiated")
        else:
            logger.info("creating data structure from word list")
            self._create()
            logger.info("storing dictionary object")
            self._store()

    def _create(self):
        """adds all words from dictionary file to GADDAG with partial minimization"""

        with open(full_dict_path) as f:
            logger.info("word list file opened")
            words = f.readlines()
        logger.info("parsing word list")
        word_list = set(x.rstrip('\n') for x in words)

        self._root = Node()

        logger.info("starting to construct GADDAG")
        for word in word_list:
            self._add_word(word)

    def _load_from_file(self):
        """loads a GADDAG data structure from a file"""

        with gzip.open(full_pickled_dict_path, "rb") as f:
            logger.info("file found and opened")
            self._root = pickle.loads(f.read())

    def _store(self):
        """stores a GADDAG data structure to the designated file"""

        with gzip.open(full_pickled_dict_path, "wb") as f:
            f.write(pickle.dumps(self._root))
        logger.info("dictionary object stored")

    def _add_word(self, word):
        """adds a word into the data structure"""

        # create path from last letter to the first
        state = self._root
        for char in word[len(word):1:-1]:
            state.add_edge(char)
            state = state.get_next(char)
        state.add_final_edge(word[1], word[0])

        # create path from second last character to the last
        state = self._root
        for char in word[len(word) - 2::-1]:
            state.add_edge(char)
            state = state.get_next(char)
        state.add_final_edge("#", word[-1])

        # add the remaining paths
        for m in range(len(word) - 2, 0, -1):
            destination = state
            state = self._root
            for char in word[m - 1::-1]:
                state.add_edge(char)
                state = state.get_next(char)
            state.add_edge("#")
            state.add_edge(word[m], destination)


class Node(object):
    """A node in a GADDAG"""

    __slots__ = '_edges'

    def __init__(self):
        self._edges = dict()

    def __iter__(self):
        for edge in self._edges:
            yield self._edges[edge]

    def __contains__(self, char):
        return char in self._edges

    def add_edge(self, char, destination=None):
        if char in self._edges:
            return
        if destination:
            self._edges[char] = Edge(char, destination)
        else:
            self._edges[char] = Edge(char)

    def add_final_edge(self, char, final):
        if char not in self._edges:
            self._edges[char] = Edge(char)
        self._edges[char].add_letter(final)

    def get_edge(self, char):
        return self._edges[char]

    def get_next(self, char):
        return self._edges[char].get_node()


class Edge(object):
    """An edge in a GADDAG."""

    __slots__ = '_char', '_letter_set', '_node'

    def __init__(self, char, node=None):
        self._letter_set = set()
        self._char = char
        if not node:
            node = Node()
        self._node = node
        if type(self._node) == str:
            print("the node is :" + self._node)

    def __eq__(self, other):
        return other == self._char

    def get_node(self):
        if type(self._node) == str:
            print("the node is :" + self._node)
        return self._node

    def add_letter(self, char):
        self._letter_set.add(char)
