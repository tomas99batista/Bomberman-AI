
# Modulo: tree_search
# 
# Fornece um conjunto de classes para suporte a resolucao de 
# problemas por pesquisa em arvore:
#    SearchDomain  - dominios de problemas
#    SearchProblem - problemas concretos a resolver 
#    SearchNode    - nos da arvore de pesquisa
#    SearchTree    - arvore de pesquisa, com metodos para 
#                    a respectiva construcao
#
#  (c) Luis Seabra Lopes
#  Introducao a Inteligencia Artificial, 2012-2018,
#  Inteligência Artificial, 2014-2018

from abc import ABC, abstractmethod

# Dominios de pesquisa
# Permitem calcular
# as accoes possiveis em cada estado, etc
class SearchDomain(ABC):

    # construtor
    @abstractmethod
    def __init__(self):
        pass

    # lista de accoes possiveis num estado
    @abstractmethod
    def actions(self, state):
        pass

    # resultado de uma accao num estado, ou seja, o estado seguinte
    @abstractmethod
    def result(self, state, action):
        pass

    # custo de uma accao num estado
    @abstractmethod
    def cost(self, state, action):
        pass

    # custo estimado de chegar de um estado a outro
    @abstractmethod
    def heuristic(self, state, goal_state):
        pass

# Problemas concretos a resolver
# dentro de um determinado dominio
class SearchProblem:
    def __init__(self, domain, initial, goal):
        self.domain = domain
        self.initial = initial
        self.goal = goal
    def goal_test(self, state):
        return state == self.goal

# Nos de uma arvore de pesquisa
class SearchNode:
    def __init__(self,state,parent=None, depth=0, cost=0, heuristic=0): 
        self.state = state
        self.parent = parent
        self.depth = depth  # Profundidade do no
        self.cost = cost    # Custo acumulado da raiz ate ao no
        self.heuristic = heuristic

        
    def in_parent(self, state):
        if self.parent == None: # Se o parent é none, estamos na root
            return False
        # se sol enconrada e aq queremos, return, se n entra na func again
        return self.parent.state == state or self.parent.in_parent(state) 
    
    def __str__(self):
        return f"no({self.state}, {self.parent}, {self.depth})"
    def __repr__(self):
        return str(self)

# Arvores de pesquisa
class SearchTree:

    # construtor
    def __init__(self,problem, strategy='breadth'): 
        self.problem = problem
        root = SearchNode(problem.initial, None, 0, 0, self.problem.domain.heuristic(problem.initial, self.problem.goal))
        self.open_nodes = [root]
        self.strategy = strategy
        self.length = 0  # comprimento da soluçao encontrada
        self.terminal = 0 
        self.non_terminal = 1 # qdo começamos a raiz é nao terminal
        self.ram_media = 0 # Ramificaçao media: ratio entre o num de nós filhos e o num de nós pais
        self.cost = 0

        self.costs = [[0, 'teste']]
        self.depth_media = 0
        self.depths = []

    # obter o caminho (sequencia de estados) da raiz ate um no
    def get_path(self,node):
        if node.parent == None:
            return [node.state]
        path = self.get_path(node.parent)
        path += [node.state] #+ str(node.depth)] #So [node] imprime todas as infos do node
        return(path)

    # procurar a solucao
    def search(self, limit):    
        while self.open_nodes != []:
            node = self.open_nodes.pop(0)
            self.cost += node.cost
            
            # --------------------------------------------------
            # Depth media
            self.depths.append(node.depth)
            self.depth_media = sum(self.depths)/len(self.depths)
            # Distancia(s) maior
            if node.cost > self.costs[0][0]:
                del self.costs[:]
                self.costs.append([node.cost, node.state])
            if node.cost == self.costs[0][0]:
                self.costs.append([node.cost, node.state])
            # Se a distancia for igual, adiciona, se for maior apaga array e mete la
            # --------------------------------------------------
            
            if self.problem.goal_test(node.state):
                self.ramification = (self.terminal + self.non_terminal -1) / self.non_terminal
                return self.get_path(node), node.cost
            lnewnodes = []
            for a in self.problem.domain.actions(node.state):
                newstate = self.problem.domain.result(node.state,a)
                # N queremos adicionar a lista se eles ja estiverem la
                if (not node.in_parent(newstate)) and node.depth < limit: 
                # in_parent vai confirmar todos os anteriores a ele // So pesquisa se o depth do node
                    # estiver dentro do limite
                    lnewnodes += [SearchNode(newstate,
                                            node,
                                            node.depth+1, 
                                            node.cost + self.problem.domain.cost(node.state, a),
                                            self.problem.domain.heuristic(newstate, self.problem.goal))]
            self.add_to_open(lnewnodes)
            if lnewnodes == []: # Se n tiver new nodes entao é terminal
                self.terminal += 1 
                self.non_terminal -= 1
            # Qdo expandimos um ganhamos os novos q derivavam desse Mas perdemos (-1) o que expandimos, q vira nao terminal
            # Se o no passou a ter filhos, aumentam os nao terminais
            self.non_terminal += len(lnewnodes) 
            self.length += 1
            self.ram_media = self.length/self.non_terminal
        return None     

    # juntar novos nos a lista de nos abertos de acordo com a estrategia
    def add_to_open(self,lnewnodes):
        if self.strategy == 'breadth':
            self.open_nodes.extend(lnewnodes)
        elif self.strategy == 'depth':
            self.open_nodes[:0] = lnewnodes #[:0] c/ os : ele insere na pos 0 s/ apagar, insert x   
        elif self.strategy == 'uniform':
            self.open_nodes = sorted(self.open_nodes + lnewnodes, key=lambda no: no.cost)
        elif self.strategy == 'greedy':
            self.open_nodes = sorted(self.open_nodes + lnewnodes, key=lambda no: no.heuristic)
        elif self.strategy == 'A*':
            self.open_nodes = sorted(self.open_nodes + lnewnodes, key=lambda no: no.cost + no.heuristic)
