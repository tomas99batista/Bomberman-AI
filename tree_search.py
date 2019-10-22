
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


# Nos de uma arvore de pesquisa (casas)
class SearchNode:
    def __init__(self,state,parent=None,depth=0): 
        self.state = state
        self.parent = parent
        self.depth = depth

    def in_parent(self,state):
        if self.parent == None:
            return False
        return self.parent.state == state or self.parent.in_parent(state)

    def __str__(self):
        return f"no({self.state}, {self.parent}, {self.depth})"

    def __repr__(self):
        return str(self)

# Arvores de pesquisa (árvore posições do mapa)
class SearchTree:

    # construtor
    def __init__(self,position, strategy='breadth'): 
        root = SearchNode(position, None,0)
        self.open_nodes = [root]
        self.strategy = strategy
        self.length = 0
        self.terminal = 0
        self.cost = 0
        self.non_terminal = 1
        self.depth_media = 0
        self.depths = [0]
        self.maxcost = 0
        self.costs = [0]


    # obter o caminho (sequencia de estados) da raiz ate um no
    def get_path(self,node):
        if node.parent == None:
            return [node.state]
        path = self.get_path(node.parent)
        path += [node.state]
        return(path)

    # procurar a solucao
    def search(self,limit):
        while self.open_nodes != []:
            node = self.open_nodes.pop(0)
            self.cost += node.cost
            self.depths.append(node.depth)
            self.depth_media = sum(self.depths)/len(self.depths)

            if node.cost == self.costs[0]:
                self.costs.append(node.cost)
            elif node.cost > self.costs[0]:
                del self.costs[:]
                self.costs.append(node.cost)
            self.maxcost = self.costs[0]
            
            if self.problem.goal_test(node.state):
                return self.get_path(node), node.cost
            lnewnodes = []
            for a in self.problem.domain.actions(node.state):
                newstate = self.problem.domain.result(node.state,a)
                if (not node.in_parent(newstate)) and node.depth < limit:
                    lnewnodes += [SearchNode(newstate, node, node.depth+1,
                                             node.cost + self.problem.domain.cost(node.state, a),
                                             self.problem.domain.heuristic(newstate, self.problem.goal))]
            self.length += 1
            self.cost += self.problem.domain.cost(node.state, a)
            self.add_to_open(lnewnodes)
            if lnewnodes == []:
                self.terminal += 1
                self.non_terminal -= 1
            
            self.non_terminal += len(lnewnodes)
            self.length+=1
            self.ramification = self.length/self.non_terminal



        return None

    # juntar novos nos a lista de nos abertos de acordo com a estrategia
    def add_to_open(self,lnewnodes):
        if self.strategy == 'breadth':
            self.open_nodes.extend(lnewnodes)
        elif self.strategy == 'depth':
            self.open_nodes[:0] = lnewnodes
        elif self.strategy == 'uniform':
            self.open_nodes = sorted(self.open_nodes + lnewnodes, key = lambda node : node.cost)
        elif self.strategy == 'greedy':
            self.open_nodes = sorted(self.open_nodes + lnewnodes, key=lambda no: no.heuristic)
        elif self.strategy == 'A*':
            self.open_nodes = sorted(self.open_nodes + lnewnodes, key=lambda no: no.cost + no.heuristic)