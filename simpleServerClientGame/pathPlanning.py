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
    return [start]

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
    # path == [(0,0),(0,1),(0,2),(0,3),(0,4),(0,5),(0,6),(0,7),(0,8),(0,9)]
    for i in range(len(path)):
        assert(path[i][0] == 0)
        assert(path[i][1] == i)
    assert(len(path) == 10)
    # goal is reachable and there are several shortest paths (any one can be
    # returned)
    path = shortestPath(map, (0,0), (9,9))
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
    # goal is reachable
    path = shortestPath(map, (8,1), (1,8))
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
    # start and goal are in in the same quadrant
    path = shortestPath(map, (9,9), (6,5))
    assert(len(path) == 9)
    # start and goal are in different quadrants
    path = shortestPath(map, (9,9), (0,9))
    assert(len(path) == 0)

if __name__ == "__main__":
    testShortestPath()
