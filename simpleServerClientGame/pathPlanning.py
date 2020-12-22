"""
In this document, you will be implementing the A* path planning algorithm.
It will take in a map, a start location, and a goal location, and return the
shortest path between those locations. Use the following resources:

- An inuitive explanation of A* and other path planning algorithms with
  pseudocode. https://www.redblobgames.com/pathfinding/a-star/introduction.html
"""

from queue import PriorityQueue
# See https://dbader.org/blog/priority-queues-in-python
# for examples of how to use a PriorityQueue
import numpy as np

def shortestPath(map, start, goal):
    """
    - map is a 2D numpy array of booleans. map[i, j] is a boolean value that is
      True if the cell at row i and column j is occupied, and False otherwise.
    - start is a tuple (start_i, start_j) that indicates an unoccupied cell in
      the map that our agent will start from.
    - goal is a tuple (goal_i, goal_j) that indicates a cell in the map that our
      agent is trying to get to.
    - if goal is reachable from start, this function should return a list of
      tuples [(i_0, j_0), (i_1, j_1), ..., (i_n, j_n)] where (i_0, j_0) = start,
      (i_n, j_n) = goal, and every tuple is unoccupied on the map, within
      the bounds of the map, and is a distance of 1 away from the previous
      tuple.
    - if goal is not reachable from start, return []
    """
    frontier = PriorityQueue()
    frontier.put(start, False)
    # open_list = []
    # closed_list = []
    # open_list.insert(start, 0)

    came_from = {}
    cost_so_far = {}
    came_from[start] = None
    cost_so_far[start] = 0
    current = None

    # check if start is a valid position using same three checks, if not valid, return empty list
    # remove all types from file including heuristic function types
    # if not start[0] < 0 or start[0] >= map.shape[0]: # returns a tuple of nxm and gives us n
    #     return []
    # if not start[1] < 0 or start[1] >= map.shape[1]:
    #     return []
    # if not map[start[0], start[1]]:
    #     return []

    while not frontier.empty():
        current = frontier.get()

        if current == goal:
            break

        (i,j) = current  #just getting values within current
        for nexti, nextj in [(i+1, j), (i, j+1), (i-1, j), (i, j-1)]:
            if nexti < 0 or nexti >= map.shape[0]: # returns a tuple of nxm and gives us n
                continue
            if nextj < 0 or nextj >= map.shape[1]:
                continue
            if map[nexti, nextj]:
                continue
            new_cost = cost_so_far[current] + 1
            next_val = (nexti, nextj)
            if next_val not in cost_so_far or new_cost < cost_so_far[next_val]:
                cost_so_far[next_val] = new_cost
                priority = new_cost + heuristic(next_val, goal)
                frontier.put(next_val, priority)
                came_from[next_val] = current

    #outside of the while loop
    print("current ", current)
    print("goal ", goal)
    if current != goal:
        return []

    path = [goal]
    while(current != start):
        current = came_from[current]
        path.insert(0, current)
    return path


def heuristic(a, b):
    (x1, y1) = a
    (x2, y2) = b
    return abs(x1 - x2) + abs(y1 - y2)

def testShortestPath():
    """
    these are a few test cases to start off with, feel free to add more
    """
    # A map without obstacles
    map = np.array(
        [[0,0,0,0,0,0,0,0,0,0],
         [0,0,0,0,0,0,0,0,0,0],
         [0,0,0,0,0,0,0,0,0,0],
         [0,0,0,0,0,0,0,0,0,0],
         [0,0,0,0,0,0,0,0,0,0],
         [0,0,0,0,0,0,0,0,0,0],
         [0,0,0,0,0,0,0,0,0,0],
         [0,0,0,0,0,0,0,0,0,0],
         [0,0,0,0,0,0,0,0,0,0],
         [0,0,0,0,0,0,0,0,0,0]]
    ).astype(np.bool)
    # goal is off of the map and is hence unreachable
    path = shortestPath(map, (0,0), (0,10))
    assert(len(path) == 0)
    # goal is reachable and there is precisely one shortest path
    path = shortestPath(map, (0,0), (0,9))
    print(path)
    # path == [(0,0),(0,1),(0,2),(0,3),(0,4),(0,5),(0,6),(0,7),(0,8),(0,9)]
    for i in range(len(path)):
        assert(path[i][0] == 0)
        assert(path[i][1] == i)
    assert(len(path) == 10)
    # goal is reachable and there are several shortest paths (any one can be
    # returned)
    path = shortestPath(map, (0,0), (9,9))
    print(path)
    assert(len(path) == 19)

    # A map with obstacles and only one path through it
    map = np.array(
        [[1,1,1,1,1,1,1,1,1,1],
         [1,0,0,0,1,0,0,0,1,0],
         [1,0,1,0,1,0,1,0,1,0],
         [1,0,1,0,1,0,1,0,1,0],
         [1,0,1,0,1,0,1,0,1,0],
         [1,0,1,0,1,0,1,0,1,0],
         [1,0,1,0,1,0,1,0,1,0],
         [1,0,1,0,1,0,1,0,1,0],
         [1,0,1,0,0,0,1,0,0,0],
         [1,1,1,1,1,1,1,1,1,1]]
    ).astype(np.bool)
    # goal is reachable (mridula - changed this test case to go to (1,9) instead of (1,8), so it is reachable)
    path = shortestPath(map, (8,1), (1,9))
    print("path: ", path)
    # changed pathAnswer to follow the previous change
    pathAnswer = [
        (8,1),(7,1),(6,1),(5,1),(4,1),(3,1),(2,1),(1,1),(1,2),
        (1,3),(2,3),(3,3),(4,3),(5,3),(6,3),(7,3),(8,3),(8,4),
        (8,5),(7,5),(6,5),(5,5),(4,5),(3,5),(2,5),(1,5),(1,6),
        (1,7),(2,7),(3,7),(4,7),(5,7),(6,7),(7,7),(8,7),(8,8),
        (8,9),(7,9),(6,9),(5,9),(4,9),(3,9),(2,9),(1,9),
    ]
    for i in range(len(pathAnswer)):
        assert(path[i][0] == pathAnswer[i][0])
        assert(path[i][1] == pathAnswer[i][1])

    # goal is a wall
    path = shortestPath(map, (8,1), (9,2))
    assert(len(path) == 0)
    # start is a wall
    path = shortestPath(map, (9,2), (8,1))
    assert(len(path) == 0)

    # map with two disconnected components
    map = np.array(
        [[1,1,1,1,1,1,0,0,0,0],
         [1,1,1,1,1,1,0,0,0,0],
         [1,1,1,1,1,1,0,0,0,0],
         [1,1,1,1,1,1,0,0,0,0],
         [1,1,1,1,1,1,0,0,0,0],
         [1,1,1,1,1,1,0,0,0,0],
         [0,0,0,0,0,0,1,1,1,1],
         [0,0,0,0,0,0,1,1,1,1],
         [0,0,0,0,0,0,1,1,1,1],
         [0,0,0,0,0,0,1,1,1,1]]
    ).astype(np.bool)
    # start and goal are in in the same quadrant (Mridula - changed (9,9) to be (9,0)))
    path = shortestPath(map, (9,0), (6,5))
    print(path)
    assert(len(path) == 9)
    # start and goal are in different quadrants
    path = shortestPath(map, (9,9), (0,9))
    assert(len(path) == 0)

if __name__ == "__main__":
    testShortestPath()
