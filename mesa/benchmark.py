import timeit
import random
from space import SingleGrid, MultiGrid
from agent import Agent

# Sample agent class
class Agent:
    def __init__(self, unique_id, pos=None):
        self.unique_id = unique_id
        self.pos = pos

# Grid dimensions
width, height = 100, 100

# Number of agents
num_agents = 1000

# Setup for SingleGrid
def setup_single_grid():
    grid = SingleGrid(width, height, False)
    agents = [Agent(i) for i in range(num_agents)]
    for agent in agents:
        while True:
            x, y = random.randint(0, width - 1), random.randint(0, height - 1)
            if grid.is_cell_empty((x, y)):
                grid.place_agent(agent, (x, y))
                break
    return grid, agents

# Setup for MultiGrid
def setup_multi_grid():
    grid = MultiGrid(width, height, False)
    agents = [Agent(i) for i in range(num_agents)]
    for agent in agents:
        x, y = random.randint(0, width - 1), random.randint(0, height - 1)
        grid.place_agent(agent, (x, y))
    return grid, agents

# Benchmark functions
def benchmark(n_repeat=25):
    # SingleGrid Benchmarks
    single_grid, single_agents = setup_single_grid()

    # Check if a specific cell is empty (SingleGrid)
    time_single_check_empty = timeit.repeat(lambda: single_grid.is_cell_empty((0, 0)), number=10000, repeat=n_repeat)

    # Getting a list of all empty cells (SingleGrid)
    time_single_list_empty = timeit.repeat(lambda: list(single_grid.get_all_empty_cells()), number=100, repeat=n_repeat)

    # Move an agent to a new grid position (SingleGrid)
    def move_single_agent():
        agent = random.choice(single_agents)
        single_grid.move_to_empty(agent)
    time_single_move_agent = timeit.repeat(move_single_agent, number=10000, repeat=n_repeat)

    # MultiGrid Benchmarks
    multi_grid, multi_agents = setup_multi_grid()

    # Check if a specific cell is empty (MultiGrid)
    time_multi_check_empty = timeit.repeat(lambda: multi_grid.is_cell_empty((0, 0)), number=10000, repeat=n_repeat)

    # Getting a list of all empty cells (MultiGrid)
    time_multi_list_empty = timeit.repeat(lambda: list(multi_grid.get_all_empty_cells()), number=100, repeat=n_repeat)

    # Move an agent to a new grid position (MultiGrid)
    def move_multi_agent():
        agent = random.choice(multi_agents)
        multi_grid.move_to_empty(agent)
    time_multi_move_agent = timeit.repeat(move_multi_agent, number=10000, repeat=n_repeat)

    # Iterate over agents in specified cells (MultiGrid only)
    def iterate_multi_agents():
        cells = [(x, y) for x in range(10) for y in range(10)]  # Sample cells
        list(multi_grid.iter_cell_list_contents(cells))
    time_multi_iterate_agents = timeit.repeat(iterate_multi_agents, number=10000, repeat=n_repeat)

    # Print benchmark results
    print(f"SingleGrid - Check Empty: {time_single_check_empty}s")
    print(f"SingleGrid - List Empty: {time_single_list_empty}s")
    print(f"SingleGrid - Move Agent: {time_single_move_agent}s")
    print(f"MultiGrid - Check Empty: {time_multi_check_empty}s")
    print(f"MultiGrid - List Empty: {time_multi_list_empty}s")
    print(f"MultiGrid - Move Agent: {time_multi_move_agent}s")
    print(f"MultiGrid - Iterate Agents: {time_multi_iterate_agents}s")

    # Save all benchmark results as a dict to a pickle file
    import pickle
    results = {
        "single_check_empty": time_single_check_empty,
        "single_list_empty": time_single_list_empty,
        "single_move_agent": time_single_move_agent,
        "multi_check_empty": time_multi_check_empty,
        "multi_list_empty": time_multi_list_empty,
        "multi_move_agent": time_multi_move_agent,
        "multi_iterate_agents": time_multi_iterate_agents
    }
    with open("benchmark_results.pkl", "wb") as f:
        pickle.dump(results, f)


if __name__ == "__main__":
    benchmark()
