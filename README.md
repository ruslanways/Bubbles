# BUBBLES

_This is a simple **game** implemented on **Python3** demonstrating capabilities of built-in (starting with Python 3.7 ) **tkinter** library._

![BUBBLES process](img/demo_for_readme.png)

## Game process
The goal of the game is to pop a bubbles that appear in random location. Smallest bubbles gives you 7 points, small bubbles 5 points, medium bubbles 2 points and the biggest one gives you 1 point. A transparent bubbles reduce your score by 5. You can use pause function pressing \<space> during the game. The game finishes with 'win' when you get 35 score or 'lose' if you miss the bubble. 
***

## Technical arrangements
To execute the game you should have installed **Python enterpreter starting version 3.7**. Also please ensure you have installed **pygame module** (install with command: `pip install pygame`). For some Linux users may be nessesary to install Tcl/Tk on your system, because some Linux distributions separate Tcl/Tk librariy from default Python. In that case you can install it by executing command in you terminal: `sudo apt install python3-tk`
For storing players scores it uses Python **sqlite3** library, that possibly already included in your Python release. If not - please take care to install it.
***

## Start the game
To start the game you should **run the main.py script**. You can do that in your terminal (or command line shell in Windows): `python3 main.py`

## License
MIT

***
&copy; Developed by Ruslan Mansurov 
