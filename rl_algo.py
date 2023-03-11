import random
import os

import scrabbler as sc
from scrabbler.dictionary import Dictionary
import utilities.logger as logger

RACK_MAX = 7

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


def main():

    game = sc.Game(filename="/Users/sbrosh1/Documents/GitHub/scrabbler/games/start_state.p",
                   global_dictionary=global_dictionary)

    bag = bag_o.copy()

    random.shuffle(bag)
    rack1_list = []
    for _ in range(RACK_MAX):
        rack1_list.append(bag.pop())
    rack1 = ''.join(rack1_list)

    moves = game.find_best_moves(rack1, num=100)
    print(policy_gradient(moves, rack1, game, 1, 1, bag, 0, 0))

#################################################################
# Function: policy_gradient
# Inputs:
# moves; list of tuples which holds data on candidate move,
# including word, start squre, direction, and score
# board; the current state of the board (what has been played and
# where)
# theta; policy parameter
# b; baseline
# Reason:
# Carry out the "Vanilla" policy gradient algorithm: generate
# episodes given a certain policy, compute the return and
# advantage, and update policy.
# Output:
# theta; the parameterized policy.
#################################################################


def policy_gradient(moves, rack1, game, theta, b, bag, score1, score2):

    for iter in range(1):
        trajectory = []
        for t in range(100):
            print("trajectory #:", t)
            bag = bag_o.copy()
            score1 = 0  # resetting the scores and bag:
            score2 = 0

            trajectory.append(compute_trajectory(
                rack1, game, bag, score1, score2))
            game = sc.Game(filename="/Users/sbrosh1/Documents/GitHub/scrabbler/games/start_state.p",
                           global_dictionary=global_dictionary, enable_logger=False)
            

        return trajectory


#################################################################
# Function: compute_trajectory
# Inputs: moves; list of (100) possible moves to be played,
# generally will be the highest immediate scoring 100 moves.
# game; current game state
# bag; tiles left in bag
# score1; current player 1 score
# score2; current player 2 score
# lookahead; how many moves (each player) in an episode.
# Reason: input a game state and a list of possible moves to be
# played. The move will be chosen using the choose_move funciton,
# and the game will be played randomly for default 2 plays
# lookahead. The function will compute one episode.
# output; output the resulting return (the difference between
# score 1 and score 2).
#################################################################

def compute_trajectory(rack1, game, bag, score1, score2, lookahead=2):

    random.shuffle(bag)

    rack2 = ""
    for i in range(RACK_MAX):
        rack2 = rack2 + bag.pop()

    for i in range(lookahead):
        moves = game.find_best_moves(rack1, num = 20)
        move1 = choose_move(moves, game, bag)
        game.play(move1.start_square, move1.word, move1.direction)
        game.show()

        if len(bag) > 0:
            rack1 = rack1.replace(move1.word[i], bag.pop(), 1)
        else:
            rack1 = rack1.replace(move1.word[i], '', 1)

        score1 = score1 + move1.score

        moves2 = game.find_best_moves(rack2, num=1)

        game.play(moves2[0].start_square, moves2[0].word, moves2[0].direction)
        game.show()

        if len(bag) > 0:
            rack2 = rack2.replace(moves2[0].word[i], bag.pop(), 1)
        else:
            rack2 = rack2.replace(moves2[0].word[i], '', 1)

        score2 = score2 + moves2[0].score

    # return the difference between the scores (try to maximize)
    return score1 - score2


# def board_to_array(board):
#     print(board.square(*(7, 7)).tile)

#################################################################
# Function: choose_move
# Inputs:
# moves; list of tuples which holds data on candidate move,
# including word, start squre, direction, and score
# board; the current state of the board (what has been played and
# where)
# Reason:
# use reinforcement learning to play the optimal move given a
# list of candidate moves and the board state.
# Output:
# move; the algorithm-deemed optimal move.
#################################################################

def choose_move(moves, game=None, bag=None, played=None):
    # start by running an episode for the first move:
    eps = 1
    r = random.uniform(0, 1)
    if r <= eps:
        move = random.choice(moves)
    else:
        # the parameterized policy will select the move, given the state (board, bag, played, etc.)
        pass

    return move



def vectorize(board, rack):
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
    
    
    

if __name__ == "__main__":
    main()
