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
        self.actual_pos = [1, 1]
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
        #self.logger.info(f'- BOMB_PLACED:{self.bomb_placed}')
        #self.logger.debug(f"-> State: {self.state}")
        #self.logger.info(f"- Actual_Pos: {self.actual_pos}")
        #self.logger.info(f"- Walls: {self.walls}")
        #self.logger.info(f"- Enemies: {self.enemies}")
        #self.logger.info(f"- Powerups: {self.powerups}")
        #self.logger.info(f"- Bonus: {self.bonus}")
        #self.logger.info(f"- Exit: {self.exit}")
        
    # Search for enemies
    def place_bomb_enemy(self):
        min_hypot = sys.maxsize
        best_spot = (1,1)
        # This lambda-function-list-comprehension-super-pythonic way will give the enemy  (the nearest) to KILL
        enemy = min([(enemy.get('pos')[0], enemy.get('pos')[1]) for enemy in self.enemies], key=lambda enemy: math.hypot(self.actual_pos[0] - enemy[0], self.actual_pos[1] - enemy[1]))
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
        print(best_spot)
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
        '''
        possible_spots = [(self.bomb_place[0] + 1, self.bomb_place[1] - 2),
                              (self.bomb_place[0] + 1, self.bomb_place[1] + 2),
                              (self.bomb_place[0] - 1, self.bomb_place[1] - 2),
                              (self.bomb_place[0] - 1, self.bomb_place[1] + 2),
                              (self.bomb_place[0] - 2, self.bomb_place[1] + 1),
                              (self.bomb_place[0] - 2, self.bomb_place[1] - 1),
                              (self.bomb_place[0] + 2, self.bomb_place[1] + 1),
                              (self.bomb_place[0] + 2, self.bomb_place[1] - 1)]
        '''
        # N = North, S = South, etc
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
        hide_spots = []
        # CASE 1: 
        if (Map.is_blocked(self.mapa, [self.bomb_place[0], self.bomb_place[1] - 1]) and Map.is_blocked(self.mapa, [self.bomb_place[0], self.bomb_place[1] + 1]) # N & S
            ) or (Map.is_blocked(self.mapa, [self.bomb_place[0]  - 1, self.bomb_place[1]]) and Map.is_blocked(self.mapa, [self.bomb_place[0] + 1, self.bomb_place[1]])):
            print('N & S blocked')
            # If NW not blocked append, then select the lowest
            if not Map.is_blocked(self.mapa, [self.bomb_place[0] - 1, self.bomb_place[1] - 1]):
                hide_spots.append((self.bomb_place[0] - 1, self.bomb_place[1] - 1))
            # If SW not blocked append, then select the lowest
            if not Map.is_blocked(self.mapa, [self.bomb_place[0] - 1, self.bomb_place[1] + 1]):
                hide_spots.append((self.bomb_place[0] - 1, self.bomb_place[1] + 1))
            # If NE not blocked append, then select the lowest
            if not Map.is_blocked(self.mapa, [self.bomb_place[0] + 1, self.bomb_place[1] - 1]):
                hide_spots.append((self.bomb_place[0] + 1, self.bomb_place[1] - 1))
            # If SE not blocked append, then select the lowest
            if not Map.is_blocked(self.mapa, [self.bomb_place[0] + 1, self.bomb_place[1] + 1]):
                hide_spots.append((self.bomb_place[0] + 1, self.bomb_place[1] + 1))

        # TODO FALTA IMPLEMENTAR O CASE 2, CASE 1 TÁ OK, ESTAVEL MAS PRECISA DE MTAS MELHORIAS
        # CASE 2:   
        # THIS TAKES TOO MUCH TIME (I THINK)
        if  Map.is_blocked(self.mapa, [self.bomb_place[0] - 1, self.bomb_place[1] - 1]) and Map.is_blocked(self.mapa, [self.bomb_place[0] - 1, self.bomb_place[1] + 1]) and Map.is_blocked(self.mapa, [self.bomb_place[0] + 1, self.bomb_place[1] - 1]) and Map.is_blocked(self.mapa, [self.bomb_place[0] + 1, self.bomb_place[1] + 1]):
            print('NE & NW & SE & SW are blocked')
            
            '''
            if (Map.is_blocked(self.mapa, [self.bomb_place[0], self.bomb_place[1] - 1])):
                print("N is blocked")
                possible_spots.remove((self.bomb_place[0] - 1, self.bomb_place[1] - 2))
                possible_spots.remove((self.bomb_place[0] + 1, self.bomb_place[1] - 2))
                
            if (Map.is_blocked(self.mapa, [self.bomb_place[0], self.bomb_place[1] + 1])):
                print("S is blocked")
                possible_spots.remove((self.bomb_place[0] - 1, self.bomb_place[1] + 2))
                possible_spots.remove((self.bomb_place[0] + 1, self.bomb_place[1] + 2))
                
            if (Map.is_blocked(self.mapa, [self.bomb_place[0] - 1 , self.bomb_place[1]])):
                print("E is blocked")
                possible_spots.remove((self.bomb_place[0] - 2, self.bomb_place[1] + 1))
                possible_spots.remove((self.bomb_place[0] - 2, self.bomb_place[1] - 1))
                
            if (Map.is_blocked(self.mapa, [self.bomb_place[0] + 1 , self.bomb_place[1]])):
                print("O is blocked")
                possible_spots.remove((self.bomb_place[0] + 2, self.bomb_place[1] + 1))
                possible_spots.remove((self.bomb_place[0] + 2, self.bomb_place[1] - 1))
                '''
           
            #-------------------------------------------------------------
            
            # If N is blocked
            if not (Map.is_blocked(self.mapa, [self.bomb_place[0], self.bomb_place[1] - 1])):
                if (self.bomb_place[0] - 1) > 0 and (self.bomb_place[1] - 2) > 0:
                    hide_spots.append((self.bomb_place[0] - 1, self.bomb_place[1] - 2))
                if (self.bomb_place[0] + 1) > 50 and (self.bomb_place[1] - 2) > 0:
                    hide_spots.append((self.bomb_place[0] + 1, self.bomb_place[1] - 2))
            # If S is blocked
            if not (Map.is_blocked(self.mapa, [self.bomb_place[0], self.bomb_place[1] + 1])):
                if (self.bomb_place[0] - 1) > 0 and (self.bomb_place[1] + 2) > 30:
                    hide_spots.append((self.bomb_place[0] - 1, self.bomb_place[1] + 2))
                if (self.bomb_place[0] + 1) > 50 and (self.bomb_place[1] + 2) > 30:
                    hide_spots.append((self.bomb_place[0] + 1, self.bomb_place[1] + 2))
            # If E is blocked
            if not (Map.is_blocked(self.mapa, [self.bomb_place[0] - 1 , self.bomb_place[1]])):
                if (self.bomb_place[0] - 2) > 0 and (self.bomb_place[1] + 1) > 30:
                    hide_spots.append((self.bomb_place[0] - 2, self.bomb_place[1] + 1))
                if (self.bomb_place[0] - 2) > 0 and (self.bomb_place[1] - 1) > 0:
                    hide_spots.append((self.bomb_place[0] - 2, self.bomb_place[1] - 1))
            # If O is blocked
            if not (Map.is_blocked(self.mapa, [self.bomb_place[0] + 1 , self.bomb_place[1]])):
                if (self.bomb_place[0] + 2) > 50 and (self.bomb_place[1] + 1) > 30:
                    hide_spots.append((self.bomb_place[0] + 2, self.bomb_place[1] + 1))
                if (self.bomb_place[0] + 2) > 50 and (self.bomb_place[1] - 1) > 0:
                    hide_spots.append((self.bomb_place[0] + 2, self.bomb_place[1] - 1))
            
                
        if hide_spots == []:
            print('not case 2 nor case 1, go to [1,1]')
            return((1,1))
        
        #print(hide_spots)
        print("MIN:",min([(wall[0], wall[1]) for wall in hide_spots], key=lambda wall: math.hypot(self.bomb_place[0] - wall[0], self.bomb_place[1] - wall[1])))
        return min([(wall[0], wall[1]) for wall in hide_spots], key=lambda wall: math.hypot(self.bomb_place[0] - wall[0], self.bomb_place[1] - wall[1]))

    
       
        
    
    # Move function
    def exec(self):
        celula = Celulas(self.mapa, self.last_pos)        
        
        # --- Há bombas no mapa --
        if self.bombs != []:
            # Se não estás a ir para o safe_spot, vai
            if not self.move == self.safe_spot:
                self.move = self.hide_spot()
                print(self.move)
                print("1")
                #PÀRA AQUI
            # Se já estás abrigado
            elif self.actual_pos == self.safe_spot:
                # Espera que a bomba rebente
                # Aqui não vai poder ficar a dormir, vai ter de ver se não tem nenhum inimigo em direção a ele
                sleep(3)
                print("2")
        
        else:            
            # Se houver powerups vai apanhar
            #if self.powerups != []:
            #    print('A IR PARA POWERUP ', self.powerups[0][1], self.powerups[0][0])
            #    move = self.powerups[0][0]
            # Se tiver inimigos vai matá-los
            if self.enemies != [] and self.walls == []:
            #    print(" STILL ENEMIES TO KILL ")
                # Perceber qual é o mais perto e aproximar-se até o matar
                self.drop = True
                self.move = self.place_bomb_enemy()
                print("3")
            # Se tiver paredes ainda para rebentar
            if self.walls != []:    # Enquanto tiver walls para partir
            #    #print(" STILL WALLS TO BLOW ")
                self.drop = True
                self.move = self.place_bomb_wall()
                print("4")
            if self.drop == True and (self.actual_pos[0], self.actual_pos[1]) == self.bomb_place:
                self.drop = False
                print("5")
                return 'B'

        #print(f'objetivo: {self.move} | Position: {self.actual_pos} | BOMB_DROP: {self.drop}')
        problem = SearchProblem(celula, self.actual_pos, self.move)  # Move é o sitio a ir
        tree = SearchTree(problem, "astar")
        best_path = (tree.search())  # Best_path = [ (x,y), (x-1,y)] AKA lista de (x,y) a seguir, perceber qdo desde e sobe, etc
        if best_path[1] == (self.actual_pos[0] - 1, self.actual_pos[1]):
            return "a"
        if best_path[1] == (self.actual_pos[0] + 1, self.actual_pos[1]):
            return "d"
        if best_path[1] == (self.actual_pos[0], self.actual_pos[1] - 1):
            return "w"
        if best_path[1] == (self.actual_pos[0], self.actual_pos[1] + 1):
            return "s"


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
                
                # Usar estrategias no agent, jogar à defensiva, ofensiva
                # As ofensiva: ir para o inimigo | defensiva: ir para as paredes
                # Ver se ele ainda tem muitas vidas, muitos inimigos, etc e isso tudo condiciona se ele vai ao ataque ou a defesa
                agent.update_agent(state)
                key = agent.exec()

                await websocket.send(
                    json.dumps({"cmd": "key", "key": key})
                )  # send key command to server - you must implement this send in the AI agent
            except websockets.exceptions.ConnectionClosedOK:
                print("Server has cleanly disconnected us")
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
            actlist.append(up)
        # DOWN
        if not self.mapa.is_blocked(down) and down != self.last_pos:
            actlist.append(down)
        # LEFT
        if not self.mapa.is_blocked(left) and left != self.last_pos:
            actlist.append(left)
        # RIGHT
        if not self.mapa.is_blocked(right) and right != self.last_pos:
            actlist.append(right)

        return actlist

    # resultado de uma accao num estado, ou seja, o estado seguinte
    def result(self, position, move):
        return move

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
