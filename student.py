import sys, json, asyncio, websockets, getpass, os, math, logging
from mapa import Map
from time import sleep
from tree_search import *

"""
Author: tomas & flavia

Copyright (c) 2019 Tomas Batista & Flavia Figueiredo
"""
logger = logging.getLogger("Bomberman")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
    datefmt="%m-%d %H:%M:%S",
)

# Class Agent
class Agent:
    def __init__(self, mapa):
        self.logger = logging.getLogger("Bomberman: ")
        self.mapa = mapa
        self.state = None
        self.actual_pos = None
        self.walls = None
        self.powerups = None
        self.bonus = None
        self.exit = None
        self.enemies = None
        self.level = 1
        self.last_pos = None
        self.bombs = None
        # Safe spot from the bomb
        self.safe_spot = None
        # My go_to
        self.move = None
        self.drop = False
        self.bomb_place = None
        self.enemy_place = None
        self.action_keys = []

    # Update agent in each iteration
    def update_agent(self, state):
        self.state = state
        self.last_pos = self.actual_pos
        self.actual_pos = state["bomberman"]
        self.x, self.y = self.actual_pos
        self.walls = state["walls"]
        self.enemies = state["enemies"]
        self.powerups = state["powerups"]
        self.bonus = state["bonus"]
        self.exit = state["exit"]
        self.level = state["level"]
        self.bombs = state['bombs']
        
    # Search for enemies
    def place_bomb_enemy(self):
        min_hypot = sys.maxsize
        best_spot = (1,1)
        # This lambda-function-list-comprehension-super-pythonic way will give the enemy  (the nearest) to KILL
        enemy = min([(enemy.get('pos')[0], enemy.get('pos')[1]) for enemy in self.enemies], key=lambda enemy: math.hypot(self.actual_pos[0] - enemy[0], self.actual_pos[1] - enemy[1]))
        # if math.hypot(self.actual_pos[0] - enemy[0], self.actual_pos[1] - enemy[1]) > (self.mapa.size[0]/2) :
            # print('enemies longe, vai ate ao meio')
            # return (25,15)
        self.enemy_place = enemy
        # Now, for that enemy, look for the closes spot 2 blocks away from the enemy [top, down, left, right]
        # If the spot UP the enemy it's free
        up =    True if enemy[1] + 2 != 0 and not Map.is_blocked(self.mapa, [enemy[0]     , enemy[1] - 2]) else False
        # If the spot DOWN the enemy it's free
        down =  True if enemy[1] - 2 != 0 and not Map.is_blocked(self.mapa, [enemy[0]     , enemy[1] + 2]) else False
        # If the spot LEFT of the enemy it's free
        left =  True if enemy[0] - 2 != 0 and not Map.is_blocked(self.mapa, [enemy[0] - 2 , enemy[1]])     else False
        # If the spot RIGHT of the enemy it's free
        right = True if enemy[0] + 2 != 0 and not Map.is_blocked(self.mapa, [enemy[0] + 2 , enemy[1]])     else False
        # If UP has the lowest hyp
        up_hyp = math.hypot(self.actual_pos[0] - enemy[0], self.actual_pos[1] - (enemy[1] - 2))
        if up and up_hyp < min_hypot:
            min_hypot = up_hyp
            best_spot = (enemy[0], enemy[1] - 2)
        # If DOWN has the lowest hyp
        down_hyp = math.hypot(self.actual_pos[0] - enemy[0], self.actual_pos[1] - (enemy[1] + 2))
        if down and down_hyp < min_hypot:
            min_hypot = down_hyp
            best_spot = (enemy[0], enemy[1] + 2)
        # If LEFT has the lowest hyp
        left_hyp = math.hypot(self.actual_pos[0] - (enemy[0] - 2), self.actual_pos[1] - enemy[1])
        if left and left_hyp < min_hypot:
            min_hypot = left_hyp
            best_spot = (enemy[0] - 2, enemy[1])
        # If RIGHT has the lowest hyp
        right_hyp = math.hypot(self.actual_pos[0] - (enemy[0] + 2), self.actual_pos[1]  + enemy[1])
        if right and right_hyp < min_hypot:
            min_hypot = right_hyp
            best_spot = (enemy[0] + 2, enemy[1])       
        logger.debug(f'Nearest wall: {enemy}')
        logger.debug(f'Best spot: {best_spot}')
        self.bomb_place = best_spot
        return best_spot             

    # Search for the closest wall
    def place_bomb_wall(self):
        min_hypot = sys.maxsize
        best_spot = (0,0)        
        # This lambda-function-list-comprehension-super-pythonic way will give the best_wall (the nearest) to put a bomb
        wall = min([(wall[0], wall[1]) for wall in self.walls], key=lambda wall: math.hypot(self.actual_pos[0] - wall[0], self.actual_pos[1] - wall[1]))
        # Now, for that wall, look for the closes spot near the wall [top, down, left, right]
        # If the spot UP the wall it's free
        up =    True if wall[1] + 1 != 0 and not Map.is_blocked(self.mapa, [wall[0]     , wall[1] - 1]) else False
        # If the spot DOWN the wall it's free
        down =  True if wall[1] - 1 != 0 and not Map.is_blocked(self.mapa, [wall[0]     , wall[1] + 1]) else False
        # If the spot LEFT of the wall it's free
        left =  True if wall[0] - 1 != 0 and not Map.is_blocked(self.mapa, [wall[0] - 1 , wall[1]])     else False
        # If the spot RIGHT of the wall it's free
        right = True if wall[0] + 1 != 0 and not Map.is_blocked(self.mapa, [wall[0] + 1 , wall[1]])     else False
        # If UP has the lowest hyp
        up_hyp = math.hypot(self.actual_pos[0] - wall[0], self.actual_pos[1] - (wall[1] - 1))
        if up and up_hyp < min_hypot:
            min_hypot = up_hyp
            best_spot = (wall[0], wall[1] - 1)
        # If DOWN has the lowest hyp
        down_hyp = math.hypot(self.actual_pos[0] - wall[0], self.actual_pos[1] - (wall[1] + 1))
        if down and down_hyp < min_hypot:
            min_hypot = down_hyp
            best_spot = (wall[0], wall[1] + 1)
        # If LEFT has the lowest hyp
        left_hyp = math.hypot(self.actual_pos[0] - (wall[0] - 1), self.actual_pos[1] - wall[1])
        if left and left_hyp < min_hypot:
            min_hypot = left_hyp
            best_spot = (wall[0] - 1, wall[1])
        # If RIGHT has the lowest hyp
        right_hyp = math.hypot(self.actual_pos[0] - (wall[0] + 1), self.actual_pos[1]  + wall[1])
        if right and right_hyp < min_hypot:
            min_hypot = right_hyp
            best_spot = (wall[0] + 1, wall[1])       
        logger.debug(f'Nearest wall: {wall}')
        logger.debug(f'Best spot: {best_spot}')
        self.bomb_place = best_spot
        return best_spot

    # Find a safe spot not in the way of the bomb explosion
    def hide_spot(self):
            # CASE 1
        # S Z S         S = Safe spot   (x +- 1, y +- 1)
        # Z B Z         Z = Possible Wall or Tile
        # S Z S         B = Bomb Spot
        # if (N & S == block) || (E & W == block):
        #   then its case 1

            # CASE 2
        # x S x S x
        # S z z z S
        # x z B z x
        # S z z z S
        # x S x S x 
        # if (NE & NW & SE & SW):
        #   then its case 2
        # esquerda = False
        # direita = False
        # cima = False
        # baixo = False
        
        # x_1, y_1 = self.enemy_place
        # x_2, y_2 = self.bomb_place
        # if x_2 < x_1:
        #     esquerda = True
        # elif x_2 > x_1:
        #     direita = True
        # elif y_2 < y_1:
        #     cima = True
        # elif y_2 > y_1:
        #     baixo = True
        hide_spots = []
        
        # Case 1
        c1 = (Map.is_blocked(self.mapa, [self.bomb_place[0], self.bomb_place[1] - 1]) and Map.is_blocked(self.mapa, [self.bomb_place[0], self.bomb_place[1] + 1])) or \
                (Map.is_blocked(self.mapa, [self.bomb_place[0]  - 1, self.bomb_place[1]]) and Map.is_blocked(self.mapa, [self.bomb_place[0] + 1, self.bomb_place[1]]))
        # Case 2
        c2 = Map.is_blocked(self.mapa, [self.bomb_place[0] - 1, self.bomb_place[1] - 1]) and \
                Map.is_blocked(self.mapa, [self.bomb_place[0] - 1, self.bomb_place[1] + 1]) and \
                Map.is_blocked(self.mapa, [self.bomb_place[0] + 1, self.bomb_place[1] - 1]) and \
                Map.is_blocked(self.mapa, [self.bomb_place[0] + 1, self.bomb_place[1] + 1])
                
        # CASE 1: 
        if c1 and not c2:
            # If NW not blocked append, then select the lowest
            if not Map.is_blocked(self.mapa, [self.bomb_place[0] - 1, self.bomb_place[1] - 1]):
                fuga = (self.bomb_place[0] - 1, self.bomb_place[1] - 1)
                if fuga != self.enemy_place:
                    hide_spots.append(fuga)
            # If SW not blocked append, then select the lowest
            if not Map.is_blocked(self.mapa, [self.bomb_place[0] - 1, self.bomb_place[1] + 1]):
                fuga = (self.bomb_place[0] - 1, self.bomb_place[1] + 1)
                if fuga != self.enemy_place:
                    hide_spots.append(fuga)
            # If NE not blocked append, then select the lowest
            if not Map.is_blocked(self.mapa, [self.bomb_place[0] + 1, self.bomb_place[1] - 1]):
                fuga = (self.bomb_place[0] + 1, self.bomb_place[1] - 1)
                if fuga != self.enemy_place:
                    hide_spots.append(fuga)
            # If SE not blocked append, then select the lowest
            if not Map.is_blocked(self.mapa, [self.bomb_place[0] + 1, self.bomb_place[1] + 1]):
                fuga = (self.bomb_place[0] + 1, self.bomb_place[1] + 1)
                if fuga != self.enemy_place:
                    hide_spots.append(fuga)     
            if hide_spots != []:
                # Este return min n faz mto sentido pq eles têm todos a mm hipotenusa, 
                # oq importa é se no caminho eles têm paredes pelo meio oq implica q eles demorem + mas ok
                spot = min([(wall[0], wall[1]) for wall in hide_spots], key=lambda wall: math.hypot(self.bomb_place[0] - wall[0], self.bomb_place[1] - wall[1]))                  
                self.safe_spot = spot
                return spot            
        # CASE 2:
        if  c2 and not c1:    
            # Check for 8 spots to run
            # x 1 x 2 x
            # 8 z z z 3
            # x z B z x
            # 7 z z z 4
            # x 6 x 5 x 
            # 1
            if not (Map.is_blocked(self.mapa, [ self.bomb_place[0] - 1, self.bomb_place[1] - 2 ])):
                fuga = (self.bomb_place[0] - 1, self.bomb_place[1] -2 )
                if fuga != self.enemy_place:
                    hide_spots.append(fuga)                  
            # 2
            if not (Map.is_blocked(self.mapa, [ self.bomb_place[0] + 1 , self.bomb_place[1] - 2 ])):
                fuga = (self.bomb_place[0] + 1 , self.bomb_place[1] - 2 )
                if fuga != self.enemy_place:
                    hide_spots.append(fuga)                    
            # 3
            if not (Map.is_blocked(self.mapa, [ self.bomb_place[0] + 2, self.bomb_place[1] - 1 ])):
                fuga = (self.bomb_place[0] + 2, self.bomb_place[1] - 1)
                if fuga != self.enemy_place:
                    hide_spots.append(fuga)
            # 4
            if not (Map.is_blocked(self.mapa, [ self.bomb_place[0] + 2 , self.bomb_place[1] + 1 ])):
                fuga = (self.bomb_place[0] + 2 , self.bomb_place[1] + 1 )
                if fuga != self.enemy_place:
                    hide_spots.append(fuga)
            # 5
            if not (Map.is_blocked(self.mapa, [ self.bomb_place[0] + 1, self.bomb_place[1] + 2 ])):
                fuga = ( self.bomb_place[0] + 1, self.bomb_place[1] + 2)
                if fuga != self.enemy_place:
                    hide_spots.append(fuga)
            # 6
            if not (Map.is_blocked(self.mapa, [ self.bomb_place[0] - 1, self.bomb_place[1] + 2 ])):
                fuga = ( self.bomb_place[0] - 1, self.bomb_place[1] + 2)
                if fuga != self.enemy_place:
                    hide_spots.append(fuga)
            # 7
            if not (Map.is_blocked(self.mapa, [ self.bomb_place[0] - 2, self.bomb_place[1] + 1 ])):
                fuga = ( self.bomb_place[0] - 2, self.bomb_place[1] + 1 )
                if fuga != self.enemy_place:
                    hide_spots.append(fuga)
            # 8
            if not (Map.is_blocked(self.mapa, [ self.bomb_place[0] - 2, self.bomb_place[1] - 1 ])):
                fuga = (self.bomb_place[0] - 2, self.bomb_place[1] - 1 )
                if fuga != self.enemy_place:
                    hide_spots.append(fuga)
            if hide_spots != []:
                # Este return min n faz mto sentido pq eles têm todos a mm hipotenusa, 
                # oq importa é se no caminho eles têm paredes pelo meio oq implica q eles demorem + mas ok
                spot = min([(wall[0], wall[1]) for wall in hide_spots], key=lambda wall: math.hypot(self.bomb_place[0] - wall[0], self.bomb_place[1] - wall[1]))                  
                self.safe_spot = spot
                return spot           
            
        else:
            #print('c1 e c2 ao mm tempo')
            return (1,1)
        
    # Move function
    def exec(self):
        # Se tem teclas em espera para executar
        if self.action_keys != []:
            # self.logger.info(f'ACTION_KEYS: {self.action_keys}')
            key = self.action_keys.pop(0)
            return key
        # Se nao calcula teclas
        else:
            # --- Há bombas no mapa --
            if self.bombs != []:
                # Se não estás a ir para o safe_spot, vai
                if self.move != self.safe_spot:
                    self.move = self.hide_spot()
                    self.logger.info(f'ir para safe_spot: {self.move}')
                # Se já estás abrigado
                if (self.actual_pos[0], self.actual_pos[1]) == (self.safe_spot[0], self.safe_spot[1]):
                    # Espera que a bomba rebente
                    # Aqui não vai poder ficar a dormir, vai ter de ver se não tem nenhum inimigo em direção a ele
                    # self.move = self.dodge_enemies()
                    self.logger.info(f'tou no safe_spot: {self.actual_pos}')
                    return "A" # futuramente por A, qdo ele tiver o detonator
            # --- Não há bombas no mapa--
            else:            
                # Se houver powerups vai apanhar
                if False: #self.powerups != []:
                   #print(f'ir para powerup: {self.powerups[0][0]}')
                   #move = (self.powerups[0][0])
                   pass
                # Se não tem
                else:
                    # Se tiver inimigos para matar
                    if self.enemies != []:
                        self.drop = True
                        self.move = self.place_bomb_enemy()
                        self.logger.info(f'proximo enemie: {self.move}')
                    else:    
                        # Se já matou todos, vai as paredes
                        # Se já não tem inimigos e já conhece a saída, poẽ-te a andar
                        if self.exit != []:
                            self.logger.info(self.state)
                            self.logger.info(f'Exit: {self.exit}')
                            self.move = (self.exit[0], self.exit[1])
                        else:
                            self.drop = True
                            self.move = self.place_bomb_wall()
                            self.logger.info(f'wall: {self.move}')

            if self.drop == True and (self.actual_pos[0], self.actual_pos[1]) == self.bomb_place:
                self.drop = False
                self.logger.info(f'bomb_drop: {self.actual_pos}')
                return 'B'

            # self.logger.info(f'Move: {self.move}')
            celula = Celulas(self.mapa, self.last_pos)        
            problem = SearchProblem(celula, self.actual_pos, self.move)  # Move é o sitio a ir
            tree = SearchTree(problem, "astar")
            best_path = tree.search()  # Best_path = [ (x,y), (x-1,y)] AKA lista de (x,y) a seguir, perceber qdo desde e sobe, etc
            # self.logger.info(f'Best_path: {best_path}')
            if best_path == []:
                self.logger.info("N TENHO PARA ONDE IR")
            lp = (self.actual_pos[0], self.actual_pos[1])
            for mv in best_path:
                x, y = mv
                a, b = lp
                if (x,y) == (a, b - 1):
                    self.action_keys.append("w")
                if (x,y) == (a, b + 1):
                    self.action_keys.append("s")
                if (x,y) == (a - 1 , b):
                    self.action_keys.append("a")
                if (x,y) == (a + 1, b):
                    self.action_keys.append("d")
                lp = mv
            return ''


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
                mapa.walls = state['walls']
                agent.update_agent(state)
                key = agent.exec()

                await websocket.send(
                    json.dumps({"cmd": "key", "key": key})
                )  # send key command to server - you must implement this send in the AI agent
            except websockets.exceptions.ConnectionClosedOK:
                #print("Server has cleanly disconnected us")
                return


class Celulas(SearchDomain):
    def __init__(self, mapa, last_pos):
        self.mapa = mapa
        self.last_pos = last_pos

    # verificar cada uma das 4 alternativas: cima, baixo, esquerda, direita
    def actions(self, pos):
        actlist = []
        up = (pos[0], pos[1] - 1)
        down = (pos[0], pos[1] + 1)
        left = (pos[0] - 1, pos[1])
        right = (pos[0] + 1, pos[1])
        # UP
        if not self.mapa.is_blocked(up) and up != self.last_pos:
            actlist.append('w')
        # DOWN
        if not self.mapa.is_blocked(down) and down != self.last_pos:
            actlist.append('s')
        # LEFT
        if not self.mapa.is_blocked(left) and left != self.last_pos:
            actlist.append('a')
        # RIGHT
        if not self.mapa.is_blocked(right) and right != self.last_pos:
            actlist.append('d')

        return actlist

    # resultado de uma accao num estado, ou seja, o estado seguinte
    def result(self, pos, move):
        if move == 'w':
            mv = (pos[0], pos[1] - 1)
        elif move == 's':
            mv = (pos[0], pos[1] + 1)
        elif move == 'a':
            mv = (pos[0] - 1, pos[1])
        elif move == 'd':
            mv = (pos[0] + 1, pos[1])
        return mv

    def cost(self, state, action):
        return 1

    def heuristic(self, pos, goal):
        pos1_x, pos1_y = pos
        pos2_x, pos2_y = goal
        return math.hypot(pos1_x - pos2_x, pos1_y - pos2_y)


# DO NOT CHANGE THE LINES BELLOW
# You can change the default values using the command line, example:
# $ NAME='bombastico' python3 client.py
loop = asyncio.get_event_loop()
SERVER = os.environ.get("SERVER", "localhost")
PORT = os.environ.get("PORT", "8000")
NAME = os.environ.get("NAME", getpass.getuser())
loop.run_until_complete(agent_loop(f"{SERVER}:{PORT}", NAME))