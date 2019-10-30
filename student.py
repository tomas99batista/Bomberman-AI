import sys, json, asyncio, websockets, getpass, os, math, logging  
from mapa import Map
from tree_search import *

'''
Author: tomas & flavia

Copyright (c) 2019 Tomas Batista & Flavia Figueiredo
'''
logger = logging.getLogger('Bomberman')
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M:%S')

# Class Agent
class Agent:
    def __init__(self, mapa):
        self.logger = logging.getLogger('Bomberman: ')
        self.mapa = mapa
        self.state = None
        self.actual_pos = None
        self.walls = None
        self.powerups = None
        self.bonus = None
        self.exit = None
        self.enemies = None
        self.level = 1      
        self.exit = None
        # Commands to execute
        self.commands = ['s', 'd']  

    # Update agent in each iteration
    def update_agent(self, state):
        self.state = state
        self.actual_pos = state['bomberman']
        # x, y da actual_pos
        self.x, self.y = self.actual_pos
        self.walls = state['walls']
        self.enemies = state['enemies']
        self.powerups = state['powerups']
        self.bonus = state['bonus']
        self.exit = state['exit']
        self.level = state['level']
        #self.logger.debug(f'-> State: {self.state}')
        self.logger.info(f'-> Actual_Pos: {self.actual_pos}')
        self.logger.info(f'-> Walls: {self.walls}')
        self.logger.info(f'-> Enemies: {self.enemies}')
        self.logger.info(f'-> Powerups: {self.powerups}')
        self.logger.info(f'-> Bonus: {self.bonus}')
        self.logger.info(f'-> Exit: {self.exit}')

    
    # Move function
    def move(self, strategy):
        # Defend
        if strategy == 'def':
            # usar aqui list comprehension das walls com lambda functions para key = hipotenusa
            closest_wall = self.closest_object(self.walls)
        # Attack
        if strategy == 'att':
            # usar a mm list comprehension c/ lambda functions, ter atençao q enemies é um dict
            closest_enemy = self.closest_object(self.enemies)

    # Search for the closest wall/enemy
    def closest_object(self, obj):
        act_x, act_y = self.actual_pos
        #self.logger.info(f'Actual pos (x,y): {act_x}, {act_y}')
        #self.logger.info(f'Walls {walls}')
        min_hyp = sys.maxsize
        best_wall = []
        for wall in obj:
            wall_x, wall_y = wall
            hyp = math.hypot(act_x - wall_x, act_y - wall_y)
            if hyp < min_hyp:
                min_hyp = hyp
                best_wall[:] = wall
        i = obj.index(best_wall)
        del obj[i]
        return best_wall

    # Close to the wall, wich place it's the best (Top, Bottom, Left, Right)  
    def best_spot_wall (self, wall):
        x_wall, y_wall = wall
        x_pos, y_pos = self.actual_position
        min_hypot = sys.maxsize        
        bomb_spot = ""  # The spot where the bomb will be placed
        bomb_spot_coords = [[0,0]]  # The coordinates where the bomb will be placed     
        
        # This will check if the walls are not on the limit of the map
        # and if they do not have any other wall arround it
        # ATTENTION: This will give false if there is a monster in the spot
        
        # If the spot above the wall it's free
        up = True if y_wall + 1 != 0 and not Map.is_blocked(self.mapa, [x_wall, y_wall + 1]) else False
        if up:
            hyp = math.hypot(x_pos - x_wall, y_pos - y_wall + 1)
            if hyp < min_hypot:
                min_hypot = hyp
                bomb_spot_coords[0] = [x_wall, y_wall+1] 
                bomb_spot = "UP"
            #self.logger.info(f'UP, Hyp: {hyp}')
        
        # If the spot under the wall it's free    
        down = True if y_wall - 1 != 0 and not Map.is_blocked(self.mapa, [x_wall, y_wall-1]) else False
        if down:
            hyp = math.hypot(x_pos - x_wall, y_pos - y_wall - 1)
            if hyp < min_hypot:
                min_hypot = hyp
                bomb_spot_coords[0] = [x_wall, y_wall - 1] 
                bomb_spot = "DOWN"
            #self.logger.info(f'DOWN, Hyp: {hyp}')
        
        # If the spot on the left of the wall it's free
        left = True if x_wall - 1 != 0 and not Map.is_blocked(self.mapa, [x_wall - 1, y_wall]) else False
        if left:
            hyp = math.hypot(x_pos - x_wall - 1, y_pos - y_wall)
            if hyp < min_hypot:
                min_hypot = hyp
                bomb_spot_coords[0] = [x_wall - 1, y_wall] 
                bomb_spot = "LEFT"
            #self.logger.info(f'LEFT, Hyp: {hyp}')
        
        # If the spot on the right of the wall it's free
        right = True if x_wall + 1 != 0 and not Map.is_blocked(self.mapa, [x_wall + 1, y_wall]) else False
        if right:
            hyp = math.hypot(x_pos - x_wall + 1, y_pos - y_wall + 1)
            if hyp < min_hypot:
                min_hypot = hyp
                bomb_spot_coords[0] = [x_wall + 1, y_wall] 
                bomb_spot = "RIGHT"
            #self.logger.info(f'RIGHT, Hyp: {hyp}')       
       
        #self.logger.info(f'UP: {up}, DOWN: {down}, LEFT: {left}, RIGHT: {right}.')
        self.logger.info(f'Bomb_Spot: {bomb_spot}, Bomb_Spot_Coordinates: {bomb_spot_coords}, Hyp: {min_hypot}')
        return bomb_spot_coords

    # Place the bomb on the spot
    def place_bomb_spot (self, destiny):
        pos_x, pos_y = self.actual_pos
        dest_x, dest_y = destiny
        problem = SearchProblem(celula, actual_pos, destiny)
        tree = SearchTree(problem, 'astar')
        tree.search
        
async def agent_loop(server_address="localhost:8000", agent_name="student"):
    async with websockets.connect(f"ws://{server_address}/player") as websocket:
        # Receive information about static game properties

        await websocket.send(json.dumps({"cmd": "join", "name": agent_name}))
        msg = await websocket.recv()
        game_properties = json.loads(msg)
        # You can create your own map representation or use the game representation:
        mapa = Map(size=game_properties["size"], mapa=game_properties["map"])
        # Create instance of Agent
        agent = Agent(mapa)
        while True:
            try:
                state = json.loads(
                    await websocket.recv()
                )  # receive game state, this must be called timely or your game will get out of sync with the server
                agent.update_agent(state)
                # Usar estrategias no agent, jogar à defensiva, ofensiva
                # As ofensiva: ir para o inimigo | defensiva: ir para as paredes
                # Ver se ele ainda tem muitas vidas, muitos inimigos, etc e isso tudo condiciona se ele vai ao ataque ou a defesa
                agent.move('def')
                # Se ele ainda tiver as 3 vidas e muitos inimigos
                # agent.move('att')
                celula = Celulas(mapa)
                
                for key in agent.commands:
                    await websocket.send(
                        json.dumps({"cmd": "key", "key": key})
                    )  # send key command to server - you must implement this send in the AI agent
                    break
            except websockets.exceptions.ConnectionClosedOK:
                print("Server has cleanly disconnected us")
                return

class Celulas(SearchDomain):
    def __init__(self,mapa):
        self.mapa = mapa

    # verificar cada uma das 4 alternativas: cima, baixo, esquerda, direita
    def actions(self,cidade):
        actlist = []
        # if not self.map.blocked(cima) and cima != self.last_position:
            #actlist.append({'move', up})
        # REPETIR ISTO PARA TODAS AS DIRECTIONS
        return actlist 
        
    def result(self, position, move):
        return move['move']
 
    def cost(self, state, action):
        return 1
            
    def heuristic(self, state, goal_state):
        pos1_x, pos1_y = self.coordinates[state]
        pos2_x, pos2_y = self.coordinates[goal_state]
        return math.hypot(pos1_x - pos2_x, pos1_y - pos2_y)

# DO NOT CHANGE THE LINES BELLOW
# You can change the default values using the command line, example:
# $ NAME='bombastico' python3 client.py
loop = asyncio.get_event_loop()
SERVER = os.environ.get("SERVER", "localhost")
PORT = os.environ.get("PORT", "8000")
NAME = os.environ.get("NAME", getpass.getuser())
loop.run_until_complete(agent_loop(f"{SERVER}:{PORT}", NAME))