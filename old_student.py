import sys
import json
import asyncio
import websockets
import getpass
import os
import math

from mapa import Map


# Next 2 lines are not needed for AI agent
import pygame

pygame.init()
on_hold_commands = []
destroyed_walls = []
'''
    IMPORTANT:  y is odd  -----------------> area is free
                y is even --> x is odd  ---> area is free
                              x is even ---> area is ocuppied 
'''
def is_even(x):
    if ((x % 2) == 0):
        return True
    else:
        return False

def commands(state,free_box):
    print(free_box)
    x_1, y_1 = free_box
    x_2, y_2 = state
    #Se estás mais abaixo da free box
    if x_2 > x_1:
        print("TEM QUE SUBIR")
        if not is_even(x_2):
            n = (x_1 - x_2)
            while n >= 1:
                on_hold_commands.append("a")
                n = n - 1
        else:
            on_hold_commands.append("d")
            x_2 = x_2 + 1
            new_state = x_2,y_2
            commands(new_state,free_box)
    #Se estás mais acima
    elif x_2 < x_1:
        print("TEM QUE DESCER")
        if not is_even(x_2):
            n = (x_1 - x_2)
            print("N :",format(n))
            while n >= 1:
                on_hold_commands.append("d")
                n = n - 1
        else:
            on_hold_commands.append("d")
            x_2 = x_2 + 1
            new_state = x_2,y_2
            commands(new_state,free_box)
    #Se estás mais para a direita
    elif y_2 > y_1:
        print("TEM QUE IR PARA A ESQUERDA")
        if not is_even(y_2):
            n = (y_1 - y_2)
            while n >= 1:
                on_hold_commands.append("w")
                n = n - 1
        else:
            on_hold_commands.append("s")
            y_2 = y_2 + 1
            new_state = x_2,y_2
            commands(new_state,free_box)
    #Se estás mais para a esquerda
    elif y_2 < y_1:
        print("TEM QUE IR PARA A DIREITA")
        if not is_even(y_2):
            n = (y_1 - y_2)
            while n >= 1:
                on_hold_commands.append("s")
                n = n - 1
        else:
            on_hold_commands.append("s")
            y_2 = y_2 + 1
            new_state = x_2,y_2
            commands(new_state,free_box)

    if not is_even(x_2):
       
        if not is_even(x_1):
            n = (x_1 - x_2)
            while n >= 1:
                on_hold_commands.append("s")
                n = n - 1

def get_box(closest_wall):
    x,y = closest_wall
    if not is_even(x):
        y = y - 1
        wall = x,y
    else:
        x = x + 1
        wall = x,y
    return wall


def search_for_walls(state):
    d = 1000
    x_1,  y_1 = state["bomberman"]
    closest_wall = [0]
    for wall in state["walls"]:
        x,y = wall
        new_d = math.sqrt(math.pow((x-x_1), 2) + math.pow((y-y_1), 2))
        if new_d < d and wall:
            if wall in destroyed_walls:
                pass
            else:
                del closest_wall[:]
                closest_wall.append(wall)
                d = new_d
    #print(d)
    print(closest_wall[0])
    wall = closest_wall[0]
    print("WALL TO DESTROY: ",format(closest_wall[0]))
    return wall

async def agent_loop(server_address="localhost:8000", agent_name="student"):
    async with websockets.connect(f"ws://{server_address}/player") as websocket:

        # Receive information about static game properties
        await websocket.send(json.dumps({"cmd": "join", "name": agent_name}))
        msg = await websocket.recv()
        game_properties = json.loads(msg)

        # You can create your own map representation or use the game representation:
        mapa = Map(size=game_properties["size"], mapa=game_properties["map"])

        # Next 3 lines are not needed for AI agent
        SCREEN = pygame.display.set_mode((299, 123))
        SPRITES = pygame.image.load("data/pad.png").convert_alpha()
        SCREEN.blit(SPRITES, (0, 0))


        while True:
            try:
                state = json.loads(  
                    await websocket.recv()
                )  # receive game state, this must be called timely or your game will get out of sync with the server

                # Next lines are only for the Human Agent, the key values are nonetheless the correct ones!
                #key = "d"
                
                print('State: ', format(state["bomberman"]))

                #print('Walls: ', format(state["walls"]))
                wall = search_for_walls(state)
                box = get_box(wall)
                print("Free Box : ", format(box))
                if not on_hold_commands:
                    commands(state["bomberman"],box)
                    on_hold_commands.append("B")
                    destroyed_walls.append(wall)


                x,y = state["bomberman"]
                
                if on_hold_commands:
                    print(on_hold_commands)
                    key = on_hold_commands[0]

                
                if on_hold_commands[0] == "B":
                    print("BOOM")                


                await websocket.send(
                    json.dumps({"cmd": "key", "key": key})
                )  # send key command to server - you must implement this send in the AI agent
                #break
                
                if on_hold_commands:
                    on_hold_commands.pop(0)
                
                        
                       
                        
            except websockets.exceptions.ConnectionClosedOK:
                print("Server has cleanly disconnected us")
                return

            

# DO NOT CHANGE THE LINES BELLOW
# You can change the default values using the command line, example:
# $ NAME='bombastico' python3 client.py
loop = asyncio.get_event_loop()
SERVER = os.environ.get("SERVER", "localhost")
PORT = os.environ.get("PORT", "8000")
NAME = os.environ.get("NAME", getpass.getuser())
loop.run_until_complete(agent_loop(f"{SERVER}:{PORT}", NAME))