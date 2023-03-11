import scrabbler as sc
import random
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
game.save("start_state")

