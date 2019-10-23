import sys, json, asyncio, websockets, getpass, os, math    
from mapa import Map
from tree_search import *

class Celulas(SearchDomain):
    def __init__(self,connections, coordinates):
        self.connections = connections
        self.coordinates = coordinates

    # verificar cada uma das 4 alternativas: cima, baixo, esquerda, direita
    def actions(self,cidade):
        actlist = []
        # if not self.map.blocked(cima) and cima != self.last_position:
            #actlist.append({'move', up})
        # REPETIR ISTO PARA TODAS AS DIRECTIONS
        return actlist 
    def result(self, position, move):
        # return move['move']
 
    def cost(self, state, action):
        return 1
            
    def heuristic(self, state, goal_state):
        pos1_x, pos1_y = self.coordinates[state]
        pos2_x, pos2_y = self.coordinates[goal_state]
        return math.hypot(pos1_x - pos2_x, pos1_y - pos2_y)

    def search_for_wall (actual_pos, walls):
        act_x, act_y = actual_pos
        #print(f'Actual pos (x,y): {act_x}, {act_y}')
        #print(f'Walls {walls}')
        min_hyp = sys.maxsize
        best_wall = []
        for wall in walls:
            wall_x, wall_y = wall
            hyp = math.hypot(act_x - wall_x, act_y - wall_y)
            if hyp < min_hyp:
                min_hyp = hyp
                best_wall[:] = wall
        i = walls.index(best_wall)
        del walls[i]
        return best_wall
        
    def best_spot_wall (mapa, wall, actual_position):
        x_wall, y_wall = wall
        x_pos, y_pos = actual_position
        # This will check if the walls are not on the limit of the map
        # and if they do not have any other wall arround it
        # ATTENTION: This will give false if there is a monster in the spot
        up = True if y_wall + 1 != 0 and not Map.is_blocked(mapa, [x_wall, y_wall + 1]) else False
        down = True if y_wall - 1 != 0 and not Map.is_blocked(mapa, [x_wall, y_wall-1]) else False
        left = True if x_wall - 1 != 0 and not Map.is_blocked(mapa, [x_wall - 1, y_wall]) else False
        right = True if x_wall + 1 != 0 and not Map.is_blocked(mapa, [x_wall + 1, y_wall]) else False
        print(f'UP: {up}, DOWN: {down}, LEFT: {left}, RIGHT: {right}.')
        min_hypot = sys.maxsize
        bomb_spot = ""  # The spot where the bomb will be placed
        bomb_spot_coords = [[0,0]]  # The coordinates where the bomb will be placed
        
        # If the spot above the wall it's free
        if up:
            hyp = math.hypot(x_pos - x_wall, y_pos - y_wall + 1)
            if hyp < min_hypot:
                min_hypot = hyp
                bomb_spot_coords[0] = [x_wall, y_wall+1] 
                bomb_spot = "UP"
            print(f'UP, Hyp: {hyp}')
        
        # If the spot under the wall it's free    
        if down:
            hyp = math.hypot(x_pos - x_wall, y_pos - y_wall - 1)
            if hyp < min_hypot:
                min_hypot = hyp
                bomb_spot_coords[0] = [x_wall, y_wall - 1] 
                bomb_spot = "DOWN"
            print(f'DOWN, Hyp: {hyp}')
        
        # If the spot on the left of the wall it's free
        if left:
            hyp = math.hypot(x_pos - x_wall - 1, y_pos - y_wall)
            if hyp < min_hypot:
                min_hypot = hyp
                bomb_spot_coords[0] = [x_wall - 1, y_wall] 
                bomb_spot = "LEFT"
            print(f'LEFT, Hyp: {hyp}')
    
        # If the spot on the right of the wall it's free
        if right:
            hyp = math.hypot(x_pos - x_wall + 1, y_pos - y_wall + 1)
            if hyp < min_hypot:
                min_hypot = hyp
                bomb_spot_coords[0] = [x_wall + 1, y_wall] 
                bomb_spot = "RIGHT"
            print(f'RIGHT, Hyp: {hyp}')
        print(f'Bomb_Spot: {bomb_spot}, Bomb_Spot_Coordinates: {bomb_spot_coords}, Hyp: {min_hypot}')
        return bomb_spot_coords
        
    def place_bomb_spot (actual_pos, bomb_spot):
        pos_x, pos_y = actual_pos
        bomb_x, bomb_y = bomb_spot
        print(f'Ok, got here, now I need to find best path')
        print(f'Next implementation: Tree Search')
    
    async def agent_loop(server_address="localhost:8000", agent_name="student"):
        async with websockets.connect(f"ws://{server_address}/player") as websocket:
            # Receive information about static game properties
            await websocket.send(json.dumps({"cmd": "join", "name": agent_name}))
            msg = await websocket.recv()
            game_properties = json.loads(msg)
            # You can create your own map representation or use the game representation:
            mapa = Map(size=game_properties["size"], mapa=game_properties["map"])
    
            while True:
                try:
                    state = json.loads(
                        await websocket.recv()
                    )  # receive game state, this must be called timely or your game will get out of sync with the server
                    actual_position = state['bomberman']
                    walls = state['walls']
                    powerups = state['powerups']
                    bonus = state['bonus']
                    exit = state['exit']
                    print(f'State: {state}')
                    print(f'Actual Pos: {actual_position}')
                    print(f'Walls: {walls}')
                    print(f'Powerups: {powerups}')
                    print(f'Bonus: {bonus}')
                    print(f'Exit: {exit}')
                    best_wall = search_for_wall(actual_position, walls)
                    print(f'-- Wall to destroy: {best_wall}')
                    bomb_spot_coords = best_spot_wall(mapa, best_wall, actual_position)
                    print(f'-- Best place to put bomb: {bomb_spot_coords}')
                    place_bomb_spot(actual_position, bomb_spot_coords[0])
                    
                    
                    await websocket.send(
                        json.dumps({"cmd": "key", "key": key})
                    )  # send key command to server - you must implement this send in the AI agent
                    break
                except websockets.exceptions.ConnectionClosedOK:
                    print("Server has cleanly disconnected us")
                    return
    
                # Next line is not needed for AI agent
                pygame.display.flip()

# DO NOT CHANGE THE LINES BELLOW
# You can change the default values using the command line, example:
# $ NAME='bombastico' python3 client.py
loop = asyncio.get_event_loop()
SERVER = os.environ.get("SERVER", "localhost")
PORT = os.environ.get("PORT", "8000")
NAME = os.environ.get("NAME", getpass.getuser())
loop.run_until_complete(agent_loop(f"{SERVER}:{PORT}", NAME))
