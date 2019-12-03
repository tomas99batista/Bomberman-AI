# iia-ia-bomberman
Bomberman clone for AI teaching

![Demo](https://github.com/dgomes/iia-ia-bomberman/raw/master/data/DemoBomberman.gif)

## Highscores

http://bomberman-aulas.ws.atnog.av.it.pt/table.html


## How to install

Make sure you are running Python 3.5.

`$ virtualenv -p python3 venv`

`$ source ./venv/bin/activate`

`$ pip3 install -r requirements.txt`


## How to play

open 3 terminals:

`$ source ./venv/bin/activate`

`$ python3 server.py`

`$ python3 viewer.py`

`$ python3 client.py`

to play using the sample client make sure the client pygame hidden window has focus


## Debug Installation

Make sure pygame is properly installed:

python -m pygame.examples.aliens

# Tested on:
- Ubuntu 18.04
- OSX 10.14.6
- Windows 10.0.18362

