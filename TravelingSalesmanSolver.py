import random
import time
import numpy as np

class TravelingSalesmanSolver:
    def __init__(
        self,
        nodes,
        edges,
        num_ants = 20,
        num_iterations = 150,
        alpha = 1.0,
        beta = 2.5,
        evaporation_rate = 0.1,
        initial_pheromone = 0.1
    ):


        if num_ants <= 0 or num_iterations <= 0:
            raise ValueError("num_ants and num_iterations must be positive")
        if alpha < 0 or beta < 0:
            raise ValueError("alpha and beta must be non-negative")
        if not 0 <= evaporation_rate <= 1:
            raise ValueError("evaporation_rate must be between 0 and 1")
        if initial_pheromone <= 0:
            raise ValueError("initial_pheromone must be positive")

        self.nodes = nodes
        self.edges = edges
        self.num_ants = num_ants
        self.num_iterations = num_iterations
        self.alpha = alpha
        self.beta = beta
        self.evaporation_rate = evaporation_rate
        self.initial_pheromone = initial_pheromone

        self.node_names = list(nodes.keys())
        self.node_indices = {name: i for i, name in enumerate(self.node_names)}
        self.num_nodes = len(self.node_names)
        
        self.distances = np.full((self.num_nodes, self.num_nodes), float('inf'))
        self.pheromones = np.full((self.num_nodes, self.num_nodes), initial_pheromone)

        self._initialize_matrices()
        
        self._probability_cache = {}

    def _initialize_matrices(self):
        for edge in self.edges:
            node1, node2, weight = edge
            i = self.node_indices[node1]
            j = self.node_indices[node2]
            self.distances[i][j] = weight
            self.distances[j][i] = weight 

        self.visibility = np.zeros_like(self.distances)
        mask = self.distances != float('inf')
        self.visibility[mask] = 1.0 / self.distances[mask]

    def _probability(self, i, j):
        cache_key = (i, j)
        if cache_key not in self._probability_cache:
            self._probability_cache[cache_key] = (
                self.pheromones[i][j] ** self.alpha * 
                self.visibility[i][j] ** self.beta
            )
        return self._probability_cache[cache_key]

    def _choose_next_node(self, current_index: int, unvisited):
        if not unvisited:
            return None

        probabilities = []
        nodes = list(unvisited)
        
        total_probability = 0
        for j in nodes:
            if self.distances[current_index][j] != float('inf'):
                prob = self._probability(current_index, j)
                probabilities.append(prob)
                total_probability += prob
            else:
                probabilities.append(0)

        if total_probability == 0:
            return None

        r = random.random() * total_probability
        cumsum = 0
        for j, prob in zip(nodes, probabilities):
            cumsum += prob
            if cumsum >= r:
                return j

        return nodes[-1] 

    def _update_pheromones(self, paths, costs) -> None:
        self._probability_cache.clear()

        for i in range(self.num_nodes):
            for j in range(i + 1, self.num_nodes):  
                self.pheromones[i][j] *= (1 - self.evaporation_rate)
                self.pheromones[j][i] = self.pheromones[i][j]

        min_cost = min(costs)
        for path, cost in zip(paths, costs):
            deposit = 1.0 / cost
            if cost == min_cost:
                deposit *= 2 

            for i in range(len(path) - 1):
                start, end = path[i], path[i + 1]
                self.pheromones[start][end] += deposit
                self.pheromones[end][start] = self.pheromones[start][end]

    def solve(self):
      
        best_path = None
        best_cost = float('inf')
        start_time = time.time()
        stagnation_counter = 0
        
        for iteration in range(self.num_iterations):
            paths = []
            costs = []
            iteration_best_cost = float('inf')

            for _ in range(self.num_ants):
                current_index = random.randrange(self.num_nodes)
                unvisited = set(range(self.num_nodes)) - {current_index}
                path = [current_index]
                
                while unvisited:
                    next_index = self._choose_next_node(current_index, unvisited)
                    if next_index is None:
                        break
                    path.append(next_index)
                    unvisited.remove(next_index)
                    current_index = next_index

                if not unvisited and self.distances[path[-1]][path[0]] != float('inf'):
                    path.append(path[0])
                    cost = sum(self.distances[path[i]][path[i + 1]] 
                             for i in range(len(path) - 1))
                    
                    paths.append(path)
                    costs.append(cost)
                    iteration_best_cost = min(iteration_best_cost, cost)

                    if cost < best_cost:
                        best_cost = cost
                        best_path = path
                        stagnation_counter = 0
                    
            if paths:
                self._update_pheromones(paths, costs)
            
            stagnation_counter += 1
            if stagnation_counter >= 20:  
                for i in range(self.num_nodes):
                    for j in range(i + 1, self.num_nodes):
                        if random.random() < 0.1: 
                            self.pheromones[i][j] = self.initial_pheromone
                            self.pheromones[j][i] = self.initial_pheromone
                stagnation_counter = 0

        end_time = time.time()

        named_path = [self.node_names[i] for i in best_path] if best_path else None

        return {
            "solution": named_path,
            "cost": best_cost if best_cost != float('inf') else None,
            "iterations": iteration + 1,
            "time_taken": end_time - start_time,
            "message": "Solution found successfully." if best_path else 
                      "No solution exists. The graph does not allow a complete tour."
        }