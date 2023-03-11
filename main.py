import scrabbler as sc
import random 
# from learning.rl_algo import choose_move
# from learning.rl_algo import board_to_array

LETTER_VALUE = {}
with open("resources/scrabble/tile_list.txt") as f:
    for line in f:
        (key, val) = line.split()
        LETTER_VALUE[key] = int(val)

RACK_MAX = 7

bag = ["A","A","A","A","A","A","A","A","A",
        "B","B", 
        "C","C",
        "D", "D","D","D",
        "E","E","E","E","E","E","E","E","E","E","E","E",
        "F","F",
        "G","G","G",
        "H", "H",
        "I","I","I","I","I","I","I","I","I",
        "J",
        "K",
        "L","L","L","L",
        "M", "M", 
        "N","N","N","N","N","N",
        "O","O","O","O","O","O","O","O",
        "P", "P",
        "Q",
        "R","R","R","R","R","R",
        "S","S","S","S",
        "T","T","T","T","T","T",
        "U","U","U","U",
        "V", "V",
        "W", "W",
        "X",
        "Y", "Y",
        "Z"]


# player 1 and player 2 draws tiles:
random.shuffle(bag)
rack1_list = []
rack2_list = []
for _ in range(RACK_MAX):
    rack1_list.append(bag.pop())
    rack2_list.append(bag.pop())

rack1 = ''.join(rack1_list)
rack2 = ''.join(rack2_list)

# start the game:
game = sc.Game()
score1 = 0
score2 = 0
round = 1

# for RL, keep track of what has been played:
played = []

while len(bag) > 0:
    # player 1 plays; update score:
    moves = game.find_best_moves(rack1, num = 1)
    if moves:
        ##################### PLAY ALGORITHM HERE #####################

        # for now, simply play move with highest instantaneous reward:
        game.play(moves[0].start_square, moves[0].word, moves[0].direction)

        ###############################################################
        score1 = score1 + moves[0].score

        # remove those tiles from player's rack, while drawing new tiles::
        for i in range(len(moves[0].word)):
            
            # keep track of what has been played, to be passed into RL algo:
            played.append(moves[0].word[i])
            if len(bag) > 0:
                rack1 = rack1.replace(moves[0].word[i], bag.pop(), 1)
            else:
                rack1 = rack1.replace(moves[0].word[i], '', 1)

    else:
        
        # If can't make a play, exchange all greater than 4 point letters:
        for l in range(len(rack1)):
            if LETTER_VALUE[rack1[l]] > 4:
                bag.append(rack1[l])
                random.shuffle(bag)
                rack1 = rack1.replace(rack1[l], bag.pop(), 1)
                
    # player 2 plays:
    moves = game.find_best_moves(rack2, num = 1)
    if moves:
        ##################### PLAY ALGORITHM HERE #####################
        # move = choose_move(moves, get_board())
        # game.play(move.start_squre, move.word, move.direction)
        # for now, simply play move with highest instantaneous reward:
        game.play(moves[0].start_square, moves[0].word, moves[0].direction)
        ###############################################################

        for i in range(len(moves[0].word)):
            # keep track of what has been played, to be passed into RL algo:
            played.append(moves[0].word[i])
            if len(bag) > 0:
                rack2 = rack2.replace(moves[0].word[i], bag.pop(), 1)
            else:
                rack2 = rack2.replace(moves[0].word[i], '', 1)

        score2 = score2 + moves[0].score

    else:
        for l in range(len(rack2)):
            if LETTER_VALUE[rack2[l]] > 4:
                bag.append(rack2[l])
                random.shuffle(bag)
                rack2 = rack2.replace(rack2[l], bag.pop(), 1)


    print("----- After round", round , "------")
    round = round + 1
    print("Player 1 score: ", score1)
    print("Player 2 score: ", score2)
    print("Tiles remaining: ", len(bag))

print("Game terminated.")
game.show()