import math
import random
import time

class TravelingSalesmanSolver:
    def __init__(self, nodes, edges, num_ants=10, num_iterations=100, alpha=1.0, beta=2.0, evaporation_rate=0.5):
        """
        Initialize the Traveling Salesman Solver using Ant Colony Optimization.

        Args:
            nodes (dict): Dictionary of nodes with names as keys and positions as values.
            edges (list): List of tuples (node1, node2, weight) representing the edges.
            num_ants (int): Number of ants.
            num_iterations (int): Number of iterations for the ACO algorithm.
            alpha (float): Influence of pheromone on decision-making.
            beta (float): Influence of edge weight on decision-making.
            evaporation_rate (float): Rate at which pheromones evaporate.
        """
        self.nodes = nodes
        self.edges = edges
        self.num_ants = num_ants
        self.num_iterations = num_iterations
        self.alpha = alpha
        self.beta = beta
        self.evaporation_rate = evaporation_rate

        # Create a distance and pheromone matrix
        self.node_names = list(nodes.keys())
        self.num_nodes = len(self.node_names)
        self.distances = [[float('inf')] * self.num_nodes for _ in range(self.num_nodes)]
        self.pheromones = [[1.0] * self.num_nodes for _ in range(self.num_nodes)]

        # Initialize distances based on edges
        self._initialize_distances()

    def _initialize_distances(self):
        for edge in self.edges:
            node1, node2, weight = edge
            i = self.node_names.index(node1)
            j = self.node_names.index(node2)
            self.distances[i][j] = weight
            self.distances[j][i] = weight

    def _probability(self, i, j):
        pheromone = self.pheromones[i][j] ** self.alpha
        visibility = (1.0 / self.distances[i][j]) ** self.beta
        return pheromone * visibility

    def _choose_next_node(self, current_node, visited):
        current_index = self.node_names.index(current_node)
        probabilities = []
        for j in range(self.num_nodes):
            if self.node_names[j] not in visited and self.distances[current_index][j] < float('inf'):
                probabilities.append(self._probability(current_index, j))
            else:
                probabilities.append(0)

        total_probability = sum(probabilities)
        if total_probability == 0:
            return None
        probabilities = [p / total_probability for p in probabilities]

        # Choose the next node based on probabilities
        next_index = random.choices(range(self.num_nodes), probabilities)[0]
        return self.node_names[next_index]

    def _update_pheromones(self, paths, costs):
        # Evaporate pheromones
        for i in range(self.num_nodes):
            for j in range(self.num_nodes):
                self.pheromones[i][j] *= (1 - self.evaporation_rate)

        # Add pheromones based on the paths
        for path, cost in zip(paths, costs):
            for i in range(len(path) - 1):
                start = self.node_names.index(path[i])
                end = self.node_names.index(path[i + 1])
                self.pheromones[start][end] += 1.0 / cost
                self.pheromones[end][start] += 1.0 / cost

    def solve(self):
        best_path = None
        best_cost = float('inf')
        start_time = time.time()

        for iteration in range(self.num_iterations):
            paths = []
            costs = []

            for _ in range(self.num_ants):
                visited = []
                current_node = random.choice(self.node_names)
                visited.append(current_node)

                while len(visited) < self.num_nodes:
                    next_node = self._choose_next_node(current_node, visited)
                    if next_node is None:
                        break
                    visited.append(next_node)
                    current_node = next_node

                # Complete the tour by returning to the starting node
                if len(visited) == self.num_nodes:
                    last_node = visited[-1]
                    first_node = visited[0]
                    last_index = self.node_names.index(last_node)
                    first_index = self.node_names.index(first_node)
                    if self.distances[last_index][first_index] < float('inf'):
                        visited.append(first_node)
                    else:
                        continue  # Skip this tour since it cannot complete a valid cycle

                # Calculate the cost of the path
                if len(visited) == self.num_nodes + 1:  # Valid complete tour
                    cost = sum(
                        self.distances[self.node_names.index(visited[i])][self.node_names.index(visited[i + 1])]
                        for i in range(len(visited) - 1)
                    )
                    paths.append(visited)
                    costs.append(cost)

                    # Update the best solution
                    if cost < best_cost:
                        best_cost = cost
                        best_path = visited

            # Update pheromones
            if paths:
                self._update_pheromones(paths, costs)

        end_time = time.time()

        # If no valid path found
        if best_path is None:
            return {
                "solution": None,
                "cost": None,
                "iterations": iteration + 1,
                "time_taken": end_time - start_time,
                "message": "No solution exists. The graph does not allow a complete tour."
            }

        return {
            "solution": best_path,
            "cost": best_cost,
            "iterations": iteration + 1,
            "time_taken": end_time - start_time,
            "message": "Solution found successfully."
        }
