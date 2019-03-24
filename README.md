Scrabbler
=========
Scrabbler is a smart move generator that works in Python. It supports Words With Friends as well as standard Scrabble boards. This package is an implementation of the scrabble move generation algorithm proposed by Steve A. Gordon in 1994, called the GADDAG.

Getting Started
---------------
You need Python 3 for this package. Simply clone this repository and navigate to the root directory. Start the Python console there and you can start using this package like so:
```python
import scrabbler as sc
```

How To Use This Package
-----------------------
The "resource" directory includes the dictionary file and board configuration files. When you create a game for the first time, a GADDAG will be construed using the dictionary file, and it will be saved for future usage.

To start a game, simply call the constructor to the Game class.
```python
game = sc.Game()
```
By default, the 15 by 15 Words With Friends board is used, but you can also specify the board type yourself.
```python
game = sc.Game(board="wwf11")
```
The available board types include the default "wwf15", the "wwf11" and "scrabble".

To place tiles on the board, either to record your own move or your opponent's move,
```python
game.play((7, 7), "word", "across")
```
The first argument is the coordinate of the starting square for this word. The first of the tuple is the row index, and the second is the column. The index starts at 0. The second argument is the actual word to be placed. The third argument is the direction, either "across" or "dowm".

To find the highest scoring moves available to you,
```python
game.find_best_moves("WDERSER")
```
The first argument to thi method is the rack of letters you have to work with. By default, it will show you 5 highest scoring words, but you can specify the number of results you want to see.
```python
game.find_best_moves("WDERSER", num=10) # this will show 10 results
```

To see the current board,
```python
game.show()
```
