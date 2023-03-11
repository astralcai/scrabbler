RACK_MAX = 7
FV_WEIGHT_NUM = 234

import random
import os
import numpy as np

import scrabbler as sc
from scrabbler.dictionary import Dictionary
import utilities.logger as logger

RACK_MAX = 7

LETTER_VALUE = {}
with open("resources/scrabble/tile_list.txt") as f:
    for line in f:
        (key, val) = line.split()
        LETTER_VALUE[key] = int(val)

script_dir = os.path.dirname(__file__)
resource_dir = os.path.join(script_dir, "resources")
resource_directory = os.path.join(resource_dir, "scrabble")
saved_dictionary_path = os.path.join(resource_directory, "dictionary.p")

logger.info("loading saved dictionary file...")
global_dictionary = Dictionary.load_from_pickle(saved_dictionary_path)
bag_o = ["A", "A", "A", "A", "A", "A", "A", "A", "A",
         "B", "B",
         "C", "C",
         "D", "D", "D", "D",
         "E", "E", "E", "E", "E", "E", "E", "E", "E", "E", "E", "E",
         "F", "F",
         "G", "G", "G",
         "H", "H",
         "I", "I", "I", "I", "I", "I", "I", "I", "I",
         "J",
         "K",
         "L", "L", "L", "L",
         "M", "M",
         "N", "N", "N", "N", "N", "N",
         "O", "O", "O", "O", "O", "O", "O", "O",
         "P", "P",
         "Q",
         "R", "R", "R", "R", "R", "R",
         "S", "S", "S", "S",
         "T", "T", "T", "T", "T", "T",
         "U", "U", "U", "U",
         "V", "V",
         "W", "W",
         "X",
         "Y", "Y",
         "Z"]


STEP_SIZE = 1e-3


# Experimentation with full game play-out from no state.

def main():
    weights = np.random.normal(size = (FV_WEIGHT_NUM, 1))

    for i in range(1000):
        print(i)
        bag = bag_o.copy()
        random.shuffle(bag)
        score1 = 0  # resetting the scores and bag:
        score2 = 0
        game = sc.Game(filename="/Users/sbrosh1/Documents/GitHub/scrabbler/games/start_state.p",
                                global_dictionary=global_dictionary, enable_logger=False)
        rack1 = ""
        rack2 = ""
        for i in range(RACK_MAX):
            rack1 = rack1 + bag.pop()
            rack2 = rack2 + bag.pop()

        
        start_move = np.random.randint(0, 4, 1)

        # And now approximate our value function:

        turn = 0

        while len(bag) > 0:

            # once we hit our start move, we initiate the value function method:
            if turn == start_move:
                feature_vector = vectorize(game.board, rack1, score1, score2)
                approx_vf = np.dot(feature_vector, weights)

            moves = game.find_best_moves(rack1, num = 20)
            if moves:
                move = choose_move(moves)
                game.play(move.start_square, move.word, move.direction)
                score1 = score1 + move.score

                if len(move.word) == 7:
                    score1 = score1 + 50

                for i in range(len(move.word)):                    
                    if len(bag) > 0:
                        rack1 = rack1.replace(move.word[i], bag.pop(), 1)
                    else:
                        rack1 = rack1.replace(move.word[i], '', 1)

            else:
                for l in range(len(rack1)):
                    if LETTER_VALUE[rack1[l]] > 4:
                        bag.append(rack1[l])
                        random.shuffle(bag)
                        rack1 = rack1.replace(rack1[l], bag.pop(), 1)
            

            moves = game.find_best_moves(rack2, num = 20)
            if moves:
                game.play(moves[0].start_square, moves[0].word, moves[0].direction)
                score2 = score2 + moves[0].score

                if len(moves[0].word) == 7:
                    score2 = score2 + 50

                for i in range(len(moves[0].word)):                    
                    if len(bag) > 0:
                        rack2 = rack2.replace(moves[0].word[i], bag.pop(), 1)
                    else:
                        rack2 = rack2.replace(moves[0].word[i], '', 1)

            else:
                for l in range(len(rack2)):
                    if LETTER_VALUE[rack2[l]] > 4:
                        bag.append(rack2[l])
                        random.shuffle(bag)
                        rack2 = rack2.replace(rack2[l], bag.pop(), 1)

            if turn == start_move + 2:
                # just break out of the while loop:
                bag = []
            
            turn = turn + 1

        true_vf = score1 - score2
        print("true_vf = ", true_vf, "approx_vf = ", approx_vf)
        delw = STEP_SIZE * (true_vf - approx_vf) * weights 
        weights = weights + delw 
    
    # np.save(weights)
    print(weights)


def vectorize(board, rack, score1, score2):
    # First, place the (simplified) board state into the feature vector:
    vec = []
    for i in range(15):
        for j in range(15):
            if board.square(i, j)._tile:
                vec.append(ord(board.square(i, j)._tile))
            else:
                vec.append(0)

    # Next, place the entirety of the rack into the feature vector:
    for i in range(RACK_MAX):
        vec.append(ord(rack[i]))

    vec.append(score1)
    vec.append(score2)
    return vec


def choose_move(moves, game=None, bag=None, played=None):
    # start by running an episode for the first move:
    eps = 0.01
    r = random.uniform(0, 1)
    if r <= eps:
        move = random.choice(moves)
    else:
        # the parameterized policy will select the move, given the state (board, bag, played, etc.)
        move = moves[0]

    return move


if __name__ == "__main__":
    main()
