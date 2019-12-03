import sys, json, asyncio, websockets, getpass, os, math, logging
from mapa import Map
from time import sleep
from characters import DIR

"""
Author: tomas & flavia

Copyright (c) 2019 Tomas Batista & Flavia Figueiredo
"""
logger = logging.getLogger("Bomberman")
logging.basicConfig(
	level=logging.WARNING,
	format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
	datefmt="%m-%d %H:%M:%S",
)

# Class Agent
class Agent:
	def __init__(self, mapa):
		self.logger = logging.getLogger("Bomberman: ")
		self.mapa = mapa
		self.state = None
		self.actual_pos = self.mapa._bomberman_spawn
		self.powerups = None
		self.bonus = None
		self.exit = None
		self.enemies = None
		self.level = 1
		self.last_pos = None
		self.bombs = None
		self.lifes = 3
		# Safe spot from the bomb
		self.safe_spot = None
		# My go_to
		self.move = None
		self.drop = False
		self.bomb_place = None
		self.go_exit = False
		self.best_path = []
		self.tries = None
		self.enemie_chasing = None

	# Update agent in each iteration
	def update_agent(self, state):
		self.state = state
		self.last_pos = self.actual_pos
		self.actual_pos = state["bomberman"]
		self.x, self.y = self.actual_pos
		self.mapa.walls = state["walls"]
		self.enemies = state["enemies"]
		self.enemies_spots = [(enemy.get('pos')[0], enemy.get('pos')[1]) for enemy in self.enemies]
		self.powerups = state["powerups"]
		self.bonus = state["bonus"]
		self.exit = state["exit"]
		self.level = state["level"]
		self.bombs = state['bombs']
		self.lifes = int(state['lives'])
	
	# Search for enemies/walls
	def place_bomb(self, distance: int, target):
		# Perceber onde tem inimigos no range da bomba
		min_hypot = sys.maxsize
		best_spot = (1,1)
		# This lambda-function-list-comprehension-super-pythonic way will give the enemy (the nearest) to KILL
		if target == 'enemy':
			objetive = min([(enemy.get('pos')[0], enemy.get('pos')[1], enemy.get('id'))  for enemy in self.enemies], key=lambda enemy: math.hypot(self.actual_pos[0] - enemy[0], self.actual_pos[1] - enemy[1]))
			self.enemie_chasing = objetive[2]
			self.logger.info(f'Nearest enemy: {objetive}')
		elif target == 'wall':
			objetive = min([(wall[0], wall[1]) for wall in self.mapa.walls], key=lambda wall: math.hypot(self.actual_pos[0] - wall[0], self.actual_pos[1] - wall[1]))
			self.logger.info(f'Nearest wall: {objetive}')
		# Now, for that enemy, look for the closes spot 2 blocks away from the enemy [top, down, left, right]
		# And see if they are not neither the border and are blocked
		# If the spot UP the enemy it's free
		up =    True if objetive[1] - distance < self.mapa.size[1] - distance and not self.mapa.is_blocked((objetive[0]     , objetive[1] - distance)) else False
		# If the spot DOWN the enemy it's free
		down =  True if objetive[1] + distance > 0 and not self.mapa.is_blocked((objetive[0]     , objetive[1] + distance)) else False
		# If the spot LEFT of the enemy it's free
		left =  True if objetive[0] - distance > 0 and not self.mapa.is_blocked((objetive[0] - distance , objetive[1]))     else False
		# If the spot RIGHT of the enemy it's free
		right = True if objetive[0] + distance < self.mapa.size[0] - distance and not self.mapa.is_blocked((objetive[0] + distance , objetive[1]))     else False
		# If UP has the lowest hyp
		if up:
			up_hyp = math.hypot(self.actual_pos[0] - objetive[0], self.actual_pos[1] - (objetive[1] - distance))
			if up_hyp < min_hypot and (objetive[0], objetive[1] - distance) not in self.enemies_spots:
				min_hypot = up_hyp
				best_spot = (objetive[0], objetive[1] - distance)
		# If DOWN has the lowest hyp
		if down:
			down_hyp = math.hypot(self.actual_pos[0] - objetive[0], self.actual_pos[1] - (objetive[1] + distance))
			if down_hyp < min_hypot and (objetive[0], objetive[1] + distance) not in self.enemies_spots:
				min_hypot = down_hyp
				best_spot = (objetive[0], objetive[1] + distance)
		# If LEFT has the lowest hyp
		if left :
			left_hyp = math.hypot(self.actual_pos[0] - (objetive[0] - distance), self.actual_pos[1] - objetive[1])
			if left_hyp < min_hypot and (objetive[0] - distance, objetive[1]) not in self.enemies_spots:
				min_hypot = left_hyp
				best_spot = (objetive[0] - distance, objetive[1])
		# If RIGHT has the lowest hyp
		if right:
			right_hyp = math.hypot(self.actual_pos[0] - (objetive[0] + distance), self.actual_pos[1]  + objetive[1])
			if right_hyp < min_hypot and (objetive[0] + distance, objetive[1])  not in self.enemies_spots:
				min_hypot = right_hyp
				best_spot = (objetive[0] + distance, objetive[1])       
		
		self.bomb_place = best_spot

		return best_spot
		
		# TODO: isto esta a funcionar, contudo, nao posso medir a distancia aos spots pela
		# hipotenusa pq essa é igual para todas, oq preciso de medir é o caminho para la,
		# ou seja, qtos passos vai ter o meu caminho para la, pq pelo caminh posso apanhar coisas

	# Find a safe spot not in the way of the bomb explosion
	def hide_spot(self):
		hide_spots = []
		
		# Case 1
		c1 = (self.mapa.is_blocked((self.bomb_place[0], self.bomb_place[1] - 1)) and self.mapa.is_blocked((self.bomb_place[0], self.bomb_place[1] + 1))) or \
				(self.mapa.is_blocked((self.bomb_place[0]  - 1, self.bomb_place[1])) and self.mapa.is_blocked((self.bomb_place[0] + 1, self.bomb_place[1])))
		# Case 2
		c2 = self.mapa.is_blocked((self.bomb_place[0] - 1, self.bomb_place[1] - 1)) and \
				self.mapa.is_blocked((self.bomb_place[0] - 1, self.bomb_place[1] + 1)) and \
				self.mapa.is_blocked((self.bomb_place[0] + 1, self.bomb_place[1] - 1)) and \
				self.mapa.is_blocked((self.bomb_place[0] + 1, self.bomb_place[1] + 1))
		# CASE 1 e CASE 2 
		# # CASE 1: 
		# S Z S         S = Safe spot   (x +- 1, y +- 1)
		# Z B Z         Z = Possible Wall or Tile
		# S Z S         B = Bomb Spot
		if c1:
			# If NW not blocked append, then select the lowest
			if not self.mapa.is_blocked((self.bomb_place[0] - 1, self.bomb_place[1] -  1)):
				fuga = (self.bomb_place[0] - 1, self.bomb_place[1] - 1)
				if fuga not in self.enemies_spots:
					hide_spots.append(fuga)
			# If SW not blocked append, then select the lowest
			if not self.mapa.is_blocked((self.bomb_place[0] - 1, self.bomb_place[1] + 1 )):
				fuga = (self.bomb_place[0] - 1, self.bomb_place[1] + 1)
				if fuga not in self.enemies_spots:
					hide_spots.append(fuga)
			# If NE not blocked append, then select the lowest
			if not self.mapa.is_blocked((self.bomb_place[0] + 1, self.bomb_place[1] - 1)):
				fuga = (self.bomb_place[0] + 1, self.bomb_place[1] - 1)
				if fuga not in self.enemies_spots:
					hide_spots.append(fuga)
			# If SE not blocked append, then select the lowest
			if not self.mapa.is_blocked((self.bomb_place[0] + 1, self.bomb_place[1] + 1)):
				fuga = (self.bomb_place[0] + 1, self.bomb_place[1] + 1)
				if fuga not in self.enemies_spots:
					hide_spots.append(fuga)     
		# # CASE 2:
		# 	# Check for 8 spots to run
		# 	# x 1 x 2 x
		# 	# 8 z z z 3
		# 	# x z B z x
		# 	# 7 z z z 4
		# 	# x 6 x 5 x 
		if c2:
			# 1
			if not (self.mapa.is_blocked(( self.bomb_place[0] - 1, self.bomb_place[1] - 2 ))):
				fuga = (self.bomb_place[0] - 1, self.bomb_place[1] -2 )
				if fuga not in self.enemies_spots:
					hide_spots.append(fuga)                  
			# 2
			if not (self.mapa.is_blocked(( self.bomb_place[0] + 1 , self.bomb_place[1] - 2 ))):
				fuga = (self.bomb_place[0] + 1 , self.bomb_place[1] - 2 )
				if fuga not in self.enemies_spots:
					hide_spots.append(fuga)                    
			# 3
			if not (self.mapa.is_blocked(( self.bomb_place[0] + 2, self.bomb_place[1] - 1 ))):
				fuga = (self.bomb_place[0] + 2, self.bomb_place[1] - 1)
				if fuga not in self.enemies_spots:
					hide_spots.append(fuga)
			# 4
			if not (self.mapa.is_blocked(( self.bomb_place[0] + 2 , self.bomb_place[1] + 1 ))):
				fuga = (self.bomb_place[0] + 2 , self.bomb_place[1] + 1 )
				if fuga not in self.enemies_spots:
					hide_spots.append(fuga)
			# 5
			if not (self.mapa.is_blocked(( self.bomb_place[0] + 1, self.bomb_place[1] + 2 ))):
				fuga = ( self.bomb_place[0] + 1, self.bomb_place[1] + 2)
				if fuga not in self.enemies_spots:
					hide_spots.append(fuga)
			# 6
			if not (self.mapa.is_blocked(( self.bomb_place[0] - 1, self.bomb_place[1] + 2 ))):
				fuga = ( self.bomb_place[0] - 1, self.bomb_place[1] + 2)
				if fuga not in self.enemies_spots:
					hide_spots.append(fuga)
			# 7
			if not (self.mapa.is_blocked(( self.bomb_place[0] - 2, self.bomb_place[1] + 1 ))):
				fuga = ( self.bomb_place[0] - 2, self.bomb_place[1] + 1 )
				if fuga not in self.enemies_spots:
					hide_spots.append(fuga)
			# 8
			if not (self.mapa.is_blocked(( self.bomb_place[0] - 2, self.bomb_place[1] - 1 ))):
				fuga = (self.bomb_place[0] - 2, self.bomb_place[1] - 1 )
				if fuga not in self.enemies_spots:
					hide_spots.append(fuga)
		if hide_spots != []:
			# Este return min n faz mto sentido pq eles têm todos a mm hipotenusa, 
			# oq importa é se no caminho eles têm paredes pelo meio oq implica q eles demorem + mas ok
			spot = min([(wall[0], wall[1]) for wall in hide_spots], key=lambda wall: math.hypot(self.bomb_place[0] - wall[0], self.bomb_place[1] - wall[1]))                  
			self.safe_spot = spot
			return spot
		else:
			print('OI?')
			return None

	# Move function
	def exec(self):
		# * --- Há bombas no mapa ---
		if self.bombs != []:
			# ! Se não estás a ir para o safe_spot, vai
			if self.move != self.safe_spot:
				self.move = self.hide_spot()
				self.logger.info(f'Going to safe spot: {self.move}')
			# ! Se já estás abrigado
			if tuple(self.actual_pos) == tuple(self.safe_spot):
				# Espera que a bomba rebente
				self.logger.info(f'At the Safe Spot: {self.actual_pos}')
				return "" # futuramente por A, qdo ele tiver o detonator
		# * --- Não há bombas no mapa ---
		else:            
			# ! Se houver powerups vai apanhar
			if self.powerups != []:
				# Vai ao powerup e da permissao de saida
				self.move = tuple(self.powerups[0][0])
				self.go_exit = True
				self.logger.info(f'Picking Powerup: {self.move}')
			# ! Se não tem
			else:
				# ! Se tiver inimigos para matar
				if self.enemies != []:
					# Ativa o drop da bomba e procura inimigo
					self.drop = True
					# Ver ha quanto tempo anda a tras do inimigo
					# Se ja e a 3a x q o tenta matar vai partir uma parede perto e volta, 
					# OU muda de inimigo e volta a este depois
					self.move = self.place_bomb(2, 'enemy')
					self.logger.info(f'Killing enemy: {self.move}')
					
					# ? if self.tries != None:
						# ? # Se ja tentou mais do que 3x, vai a uma parede
						# ? # Se ainda n tentou + do1 30x o enemy, vai
						# ? if self.tries[1] <= 30:
							# ? self.move = self.place_bomb(2, 'enemy')
							# ? self.tries[1] += 1
							# ? print(f'Trying enemy: {self.tries}')
						# ? # Se ja tentou + doq 30 iteraçoes matar o inimigo e a wall ainda continua por rebentar
						# ? if self.tries[1] > 30 and self.wall_chasing in self.mapa.walls:
							# ? self.move = self.place_bomb(1, 'wall')
							# ? print(f'Trying wall: {self.tries}')						
						# ? else:
							# ? self.tries = [self.enemie_chasing, 1]
							# ? self.move = self.place_bomb(2, 'enemy')
							# ? self.logger.info(f'Killing enemy: {self.move}')						
					# ? else:
						# ? self.tries = [self.enemie_chasing, 1]
						# ? self.move = self.place_bomb(2, 'enemy')
						# ? self.logger.info(f'Killing enemy: {self.move}')

				# ! Se já matou todos, vai as paredes
				else:   
					# ! Se já conhece a saída e já tem o powerup
					if self.exit != [] and self.go_exit:
						# Vai para a saida e desativa a flag go_exit
						self.move = tuple(self.exit)
						self.logger.info(f'Going to exit: {tuple(self.move)}')
					# ! Se ainda não conhece a saida/não descobriu o powerup
					else:
						# Ativa o drop da bomba e vai para a wall
						self.drop = True
						self.move = self.place_bomb(1, 'wall')
						self.logger.info(f'Destroying wall: {self.move}')
		
		# ! Se tem permissao para dropar bomba, fa-lo
		if self.drop and tuple(self.actual_pos) == self.bomb_place:
			self.drop = False
			print('bomb drop')
			self.logger.info(f'Bomb drop: {self.actual_pos}')
			return 'B'
		
		self.logger.info(f'Move: {self.move}')
		
		# ! Se n tenho best_path calculado
		if not self.best_path:
			celula = Celulas(self.mapa, self.last_pos, False)        
			best_path = celula.AStarSearch(tuple(self.actual_pos), self.move)  
			# ! Se mesmo assim nao calcula best_path é porque nao encontrou caminho para la
			# ! Entao liga-se o wall pass (True nos args das Celulas) para ele passar por cima
			# ! Das paredes ao calcuar o best path. O que vai acontecer é que quando ele se deparar com uma parede 
			# ! Tem de a rebentar.
			if not best_path:
				# True é para o wallpass
				celula = Celulas(self.mapa, self.last_pos, True)        
				best_path = celula.AStarSearch(tuple(self.actual_pos), self.move)
			# Digerir so meia lista
			size = int(len(best_path)/2)
			if size < 1: size = 1
			# Consumir meia lista
			self.best_path = best_path[:size]
		# Retira a posição a seguir
		pos = self.best_path.pop(0)
		# ! Se ve que a posiçao é uma wall (Qdo wallpass ta ligado) 
		# ! ou vai bater num inimigo, dropa um B 
		# ! E volta para a ultima posicao
		# Se vai bater num inimigo
		# TODO: Ver a 2 casas a seguir
		# ? if pos in self.mapa.walls or 
		if pos in self.enemies_spots:
			# volta para last position
			print('vou bater')
			return 'B' # TODO: por enquanto
			# ?  self.best_path = ['B']
			# ?  # Proxima pos é uma parede, rebenta
			# ?  pos = self.last_pos
			# ?  celula = Celulas(self.mapa, self.last_pos, False)        
			# ?  best_path = celula.AStarSearch(tuple(self.actual_pos), self.move)
		# Se tem best_path (O 'B' passado qdo ele tem inimigos a frente)
		#  ? if self.best_path:
			# ?  if self.best_path[0] == 'B':
				# ?  return 'B'
		#self.logger.info(f'Best_path: {self.best_path}')
		
		# ! Se a proxima posicao é a saida, volta a meter o go exit a false para o next lvl
		if self.exit == pos: self.go_exit = False
		
		# ! Perceber que key tem de pressionar a seguir
		if pos == (self.actual_pos[0] - 1, self.actual_pos[1]):
			return "a"
		elif pos == (self.actual_pos[0] + 1, self.actual_pos[1]):
			return "d"
		elif pos == (self.actual_pos[0], self.actual_pos[1] - 1):
			return "w"
		elif pos == (self.actual_pos[0], self.actual_pos[1] + 1):
			return "s"
		
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
				# receive game state, this must be called timely or your game will get out of sync with the server
				state = json.loads(await websocket.recv())  
				# Para comer todas as mensagens q estao entaladas
				while len(websocket.messages) > 0:
					state = json.loads(websocket.recv())
				# Para so enviar o score
				if len(state) > 1:
					agent.update_agent(state)
					key = agent.exec()
				await websocket.send(
					json.dumps({"cmd": "key", "key": key})
				)  # send key command to server - you must implement this send in the AI agent
			except websockets.exceptions.ConnectionClosedOK:
				#print("Server has cleanly disconnected us")
				return


class Celulas:
	def __init__(self, mapa, last_pos, wallpass):
		self.mapa = mapa
		self.last_pos = last_pos
		self.wallpass = wallpass

	# verificar cada uma das 4 alternativas: cima, baixo, esquerda, direita
	def actions(self, pos):
		actlist = []
		for d in DIR:
			next_pos = self.mapa.calc_pos(pos, d, self.wallpass)
			if next_pos != pos:
				actlist.append(next_pos)
		return actlist

	def heuristic(self, pos, goal):
		pos1_x, pos1_y = pos
		pos2_x, pos2_y = goal
		return math.hypot(pos1_x - pos2_x, pos1_y - pos2_y)
	
	# procurar a solucao
	def AStarSearch(self, start, end):
		G = {} #Actual movement cost to each position from the start position
		F = {} #Estimated movement cost of start to end going via this position
	
		#Initialize starting values
		G[start] = 0 
		F[start] = self.heuristic(start, end)
	
		closedVertices = set()
		openVertices = set([start])
		cameFrom = {}
	
		while len(openVertices) > 0:
			#Get the vertex in the open list with the lowest F score
			current = None
			currentFscore = None
			for pos in openVertices:
				if current is None or F[pos] < currentFscore:
					currentFscore = F[pos]
					current = pos
	
			#Check if we have reached the goal
			if current == end:
				#Retrace our route backward
				path = [current]
				while current in cameFrom:
					current = cameFrom[current]
					path.append(current)
				path.reverse()
				return path[1:]
	
			#Mark the current vertex as closed
			openVertices.remove(current)
			closedVertices.add(current)
	
			#Update scores for vertices near the current position
			for neighbour in self.actions(current):
				if neighbour in closedVertices: 
					continue #We have already processed this node exhaustively
				candidateG = G[current] + 1
	
				if neighbour not in openVertices:
					openVertices.add(neighbour) #Discovered a new vertex
				elif candidateG >= G[neighbour]:
					continue #This G score is worse than previously found
				
				#Adopt this G score
				cameFrom[neighbour] = current
				G[neighbour] = candidateG
				H = self.heuristic(neighbour, end)
				F[neighbour] = G[neighbour] + H
	
		return []
		


# DO NOT CHANGE THE LINES BELLOW
# You can change the default values using the command line, example:
# $ NAME='bombastico' python3 client.py
loop = asyncio.get_event_loop()
SERVER = os.environ.get("SERVER", "localhost")
PORT = os.environ.get("PORT", "8000")
NAME = os.environ.get("NAME", getpass.getuser())
loop.run_until_complete(agent_loop(f"{SERVER}:{PORT}", NAME))