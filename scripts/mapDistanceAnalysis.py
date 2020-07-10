import json
import math
import pprint
import random
import datetime
import copy
import matplotlib.pyplot as plt

def processMapDistances(filename):
    with open(filename, "r") as f:
        mapData = json.loads(f.read())
        mapDistances = mapData["distances"]
        semanticLabelToXYForTargets = mapData["semanticLabelToXYForTargets"]

    # Bucket the distances and graph them out
    bucketSize = 5
    minDist = None
    maxDist = None
    distances = []
    sortedDistanceBuckets = []
    distanceBucketsToCount = {}
    distanceBucketsToEdges = {} # distancebucket -> node -> list of neighboring nodes
    uniqueNodes = set()
    for node0 in mapDistances:
        uniqueNodes.add(node0)
        for node1 in mapDistances[node0]:
            dist = mapDistances[node0][node1]["distance"]
            distBucket = (dist//bucketSize)*bucketSize
            if distBucket not in distanceBucketsToCount:
                distanceBucketsToCount[distBucket] = 0
                distanceBucketsToEdges[distBucket] = {}
                sortedDistanceBuckets.append(distBucket)
            distanceBucketsToCount[distBucket] += 1
            if node0 not in distanceBucketsToEdges[distBucket]:
                distanceBucketsToEdges[distBucket][node0] = set()
            distanceBucketsToEdges[distBucket][node0].add(node1)
            distances.append(dist)
            if minDist is None or dist < minDist: minDist = dist
            if maxDist is None or dist > maxDist: maxDist = dist
    sortedDistanceBuckets.sort()

    print(uniqueNodes)
    assert len(uniqueNodes) == 31

    print("Num unique buckets: ", len(distanceBucketsToCount))
    print("minDist/maxDist", minDist, maxDist)

    # # Histogram
    # plt.hist(distances, int(round((maxDist-minDist)/bucketSize)), facecolor='blue')
    # plt.show()

    # # Scatterplot
    # xs = [dist for dist in distanceBucketsToCount]
    # ys = [distanceBucketsToCount[dist]/2 for dist in xs] # Divide by two since the graph is bidirectional
    #
    # fig = plt.figure()
    # ax = fig.add_subplot(111)
    # ax.scatter(xs, ys, marker='o')
    # ax.set_xlabel('Distances')
    # ax.set_ylabel('Count')
    # plt.show()

    # Accumulate the data for the ranges that are fully connected
    rangeToData = {} # (i, j) -> (avgConnectivity, avgMinTime)
    rangeToMergedAdjacencyList = {}

    # For every possible range, take the subset of edges within that range
    for i in range(len(sortedDistanceBuckets)):
        for j in range(i, len(sortedDistanceBuckets)):
            iDist = max(sortedDistanceBuckets[i], minDist)
            jDist = sortedDistanceBuckets[j+1] if j < len(sortedDistanceBuckets)-1 else maxDist
            startNode = None
            # Merge the adjacency lists for all distance buckets from index i to j (inclusive)
            mergedAdjacencyList = {}
            for k in range(i, j+1):
                distBucket = sortedDistanceBuckets[k]
                adjacencyList = distanceBucketsToEdges[distBucket]
                for node0 in adjacencyList:
                    if startNode is None: startNode = node0
                    if node0 not in mergedAdjacencyList:
                        mergedAdjacencyList[node0] = set()
                    for node1 in adjacencyList[node0]:
                        mergedAdjacencyList[node0].add(node1)
            # Check if the graph is connected
            if startNode is None:
                raise Exception("No nodes satisfy i %d, j %d" % (i, j))
            visited = set()
            queue = [startNode]
            while len(queue) > 0:
                node = queue.pop(0)
                visited.add(node)

                if node in mergedAdjacencyList:
                    for neighbor in mergedAdjacencyList[node]:
                        if neighbor not in visited:
                            queue.append(neighbor)
            print("(i, j) (%d, %d), (iDist, jDist) (%d, %d), %d/%d nodes reached" % (i, j, iDist, jDist, len(visited), len(uniqueNodes)))
            if len(visited) == len(uniqueNodes):
                print("Graph connected!")
                # Get the average connectivity of this graph
                totalDegree = 0
                for node0 in mergedAdjacencyList:
                    totalDegree += len(mergedAdjacencyList[node0])
                avgDegree = totalDegree/len(visited)
                # Get the average time to go between two nodes in this graph
                totalDistance = 0
                numEdges = 0
                for node0 in mergedAdjacencyList:
                    for node1 in mergedAdjacencyList[node0]:
                        dist = mapDistances[node0][node1]["distance"]
                        totalDistance += dist
                        numEdges += 1
                avgTime = (totalDistance/numEdges)*0.2 # the player takes 200ms/unit
                rangeToData[(i, j)] = [avgDegree, avgTime, jDist-iDist, (iDist, jDist)]
                rangeToMergedAdjacencyList[(i, j)] = mergedAdjacencyList
    # Print rangeToData
    print("Ranges that result in connected graphs, sorted by rangeSize")
    pprint.pprint(sorted(rangeToData.items(), key=lambda x: x[1][2]))

    return rangeToMergedAdjacencyList, rangeToData, semanticLabelToXYForTargets, mapDistances

def generateTaskSequence(adjacencyList, semanticLabelToXYForTargets, n=100):
    # Generates n random task sequences, under the constraint that it starts from
    # Room 1, is length 28, and every third one, starting from the second (after Room 1), is in freeTaskNodes
    startNode = "Room 1 Start"
    freeTimeNodes = ["Lounge Start", "Restroom A Start", "Restroom B Start", "Restroom C Start", "Game Room Start"]

    # Make a copy of the adjacency list that is randomly shuffled
    adjacencyListRandom = {}
    for node0 in adjacencyList:
        for node1 in adjacencyList[node0]:
            if node0 not in adjacencyListRandom:
                adjacencyListRandom[node0] = []
            adjacencyListRandom[node0].append(node1)
    for node0 in adjacencyListRandom:
        random.shuffle(adjacencyListRandom[node0])

    # A subset of the adjacency list that only contains nodes that can reach free time nodes
    adjacencyListFreeTimeNodes = {}
    adjacencyListNotFreeTimeNodes = {}
    for node0 in adjacencyListRandom:
        for node1 in adjacencyListRandom[node0]:
            if node1 in freeTimeNodes:
                if node0 not in adjacencyListFreeTimeNodes:
                    adjacencyListFreeTimeNodes[node0] = []
                adjacencyListFreeTimeNodes[node0].append(node1)
            else:
                if node0 not in adjacencyListNotFreeTimeNodes:
                    adjacencyListNotFreeTimeNodes[node0] = []
                adjacencyListNotFreeTimeNodes[node0].append(node1)

    sequence = [startNode] + [None for i in range(28)]
    nodeGroups = [
        ("Room 1 Start", "Room 2 Start", "Room 3 Start", "Room 4 Start"),
        ("Room 6 Start", "Room 7 Start", "Room 8 Start", "Room 12 Start"),
        ("Room 5 Start", "Room 10 Start", "Room 11 Start"),
        ("Room 20 Start", "Room 32 Start", "Room 33 Start"),
        ("Room 30 Start", "Room 31 Start"),
        ("Room 21 Start", "Room 22 Start", "Room 34 Start"),
        ("Room 41 Start", "Room 42 Start", "Room 43 Start", "Room 44 Start", "Room 45 Start", "Room 46 Start", "Room 47 Start"),
        ("Lounge Start", ),
        ("Restroom A Start", ),
        ("Restroom B Start", ),
        ("Restroom C Start", ),
        ("Game Room Start", ),
    ];
    nodeToNodeGroup = {}
    for j in range(len(nodeGroups)):
        for node in nodeGroups[j]:
            nodeToNodeGroup[node] = j
    nodeGroupsToNumTimesVisited = {j : 0 for j in range(len(nodeGroups))}
    nodesToNumTimesVisited = {node : 0 for node in adjacencyList}
    nodesToNumTimesVisited[startNode] += 1
    startFreeTimeI = 2
    freeTimePeriod = 3

    def constructSequence(i, foundSequences):
        if (i == 29):
            foundSequences.append(copy.deepcopy(sequence))
            return foundSequences
        prevNode = sequence[i-1]
        def sortingFunction(node0):
            # Order nodes from least visited to most visited
            numTimesVisited = nodesToNumTimesVisited[node0]
            numTimesVisitedGroup = nodeGroupsToNumTimesVisited[nodeToNodeGroup[node0]]
            # return numTimesVisited
            # Order nodes from greatest distance to past nodes to least distance
            minDistance = None
            for j in range(max(0, i-3), i):
                node1 = sequence[j]
                # print("node1", node1, "i", i, "sequence",sequence)
                p1 = semanticLabelToXYForTargets[node1]
                p0 = semanticLabelToXYForTargets[node0]
                dist = ((p1["x"]-p0["x"])**2+(p1["y"]-p0["y"])**2)**0.5
                if minDistance is None or dist < minDistance:
                    minDistance = dist
            return (-1*minDistance + (numTimesVisited+numTimesVisitedGroup)*7)
        # If it is a free time index
        if i >= startFreeTimeI and (i - startFreeTimeI) % freeTimePeriod == 0:
            if prevNode in adjacencyListFreeTimeNodes:
                visitingOrder = sorted(adjacencyListFreeTimeNodes[prevNode], key=sortingFunction)
            else:
                return foundSequences
        else:
            if prevNode in adjacencyListNotFreeTimeNodes:
                visitingOrder = sorted(adjacencyListNotFreeTimeNodes[prevNode], key=sortingFunction)
            else:
                return foundSequences
        for currNode in visitingOrder:
            sequence[i] = currNode
            nodesToNumTimesVisited[currNode] += 1
            nodeGroupsToNumTimesVisited[nodeToNodeGroup[currNode]] += 1
            foundSequences = constructSequence(i+1, foundSequences)
            nodesToNumTimesVisited[currNode] -= 1
            nodeGroupsToNumTimesVisited[nodeToNodeGroup[currNode]] -= 1
            if (len(foundSequences) >= n): return foundSequences
        return foundSequences

    foundSequences = constructSequence(1, foundSequences=[])

    # pprint.pprint([[node[:-8] for node in foundSequence] for foundSequence in foundSequences])

    if len(foundSequences) > 0:
        totalNumDifferentRooms = 0
        for foundSequence in foundSequences:
            totalNumDifferentRooms += len(set(foundSequence))
        avgNumDifferentRooms = totalNumDifferentRooms/len(foundSequences)
    else:
        avgNumDifferentRooms = 0

    return avgNumDifferentRooms, foundSequences

def generateRobotTargets(finalSequence, robotAppearsAfterTaskIndex, mapDistances):
    freeTimeNodes = ["Lounge Start", "Restroom A Start", "Restroom B Start", "Restroom C Start", "Game Room Start"]
    bucketSize = 5
    minDist = None
    maxDist = None
    distances = []
    sortedDistanceBuckets = []
    distanceBucketsToCount = {}
    distanceBucketsToEdges = {} # completedTaskI -> distancebucket -> list of nodes
    for completedTaskI in robotAppearsAfterTaskIndex:
        humanSourceNode = finalSequence[completedTaskI]
        humanGoalNode = finalSequence[completedTaskI+1]
        halfwayLocation = mapDistances[humanSourceNode][humanGoalNode]["halfwayLocation"]
        distanceBucketsToEdges[completedTaskI] = {}
        for node in mapDistances:
            if (node == humanGoalNode): continue
            dist = mapDistances[humanSourceNode][humanGoalNode]["halfwayToRoomsDistance"][node] + mapDistances[node][humanGoalNode]["distance"] - mapDistances[humanSourceNode][humanGoalNode]["halfwayToRoomsDistance"][humanGoalNode]
            distBucket = (dist//bucketSize)*bucketSize
            if distBucket not in distanceBucketsToCount:
                distanceBucketsToCount[distBucket] = 0
                sortedDistanceBuckets.append(distBucket)
            distanceBucketsToCount[distBucket] += 1
            if distBucket not in distanceBucketsToEdges[completedTaskI]:
                distanceBucketsToEdges[completedTaskI][distBucket] = set()
            distanceBucketsToEdges[completedTaskI][distBucket].add(node)
            distances.append(dist)
            if minDist is None or dist < minDist: minDist = dist
            if maxDist is None or dist > maxDist: maxDist = dist
    sortedDistanceBuckets.sort()

    print("distances", distances)
    pprint.pprint(distanceBucketsToCount)

    # # Histogram
    # plt.hist(distances, int(round((maxDist-minDist)/bucketSize)), facecolor='blue')
    # plt.show()

    # For robot distances, the designation of ranges is relatively arbitray --
    # it depends on how large I want the task to be. Since the human task
    # distances are (25, 35) and the robot appears approximately half way, then
    # if the human helps the robot the traversed distance will be 1.5*distance.
    # So I'll set that for now, and then see how it goes.
    completedTaskIToMergedNodes = {}
    for completedTaskI in robotAppearsAfterTaskIndex:
        # Get all the nodes for the (25, 35) change
        mergedNodes = set()
        for distBucket in [35, 40]:
            if distBucket in distanceBucketsToEdges[completedTaskI]:
                for node in distanceBucketsToEdges[completedTaskI][distBucket]:
                    if node not in freeTimeNodes: mergedNodes.add(node) # The robot should never go to free time nodes
        if len(mergedNodes) == 0:
            print("No merged Nodes for completedTaskI", completedTaskI)
        completedTaskIToMergedNodes[completedTaskI] = list(mergedNodes)

    finalRobotGoals = [None for completedTaskI in robotAppearsAfterTaskIndex]
    def constructSequence(i, foundSequences):
        if i >= len(robotAppearsAfterTaskIndex):
            foundSequences.append(copy.deepcopy(finalRobotGoals))
            return foundSequences
        completedTaskI = robotAppearsAfterTaskIndex[i]
        mergedNodes = completedTaskIToMergedNodes[completedTaskI]

        humanGoalNode = finalSequence[completedTaskI+1]
        humanSourceNode = finalSequence[completedTaskI]
        humanPrevSourceNode = finalSequence[completedTaskI-1]
        prevRobotGoal = finalRobotGoals[i-1] if finalRobotGoals[i-1] is not None else humanSourceNode
        prevPrevRobotGoal = finalRobotGoals[i-2] if finalRobotGoals[i-2] is not None else humanSourceNode

        def sortingFunction(node):
            humanDistancesToMinimize = []
            robotDistancesToMinimize = []
            if humanGoalNode in mapDistances[node]:
                humanDistancesToMinimize.append(mapDistances[node][humanGoalNode]["distance"])
            if humanSourceNode in mapDistances[node]:
                humanDistancesToMinimize.append(mapDistances[node][humanSourceNode]["distance"])
            if humanPrevSourceNode in mapDistances[node]:
                humanDistancesToMinimize.append(mapDistances[node][humanPrevSourceNode]["distance"])
            if prevRobotGoal in mapDistances[node]:
                robotDistancesToMinimize.append(mapDistances[node][prevRobotGoal]["distance"])
            if prevPrevRobotGoal in mapDistances[node]:
                robotDistancesToMinimize.append(mapDistances[node][prevPrevRobotGoal]["distance"])
            minDist = min(humanDistancesToMinimize) + (min(robotDistancesToMinimize)*5 if len(robotDistancesToMinimize) > 0 else 0)
            return -1*minDist
        mergedNodes.sort(key=sortingFunction)
        for currNode in mergedNodes:
            if currNode not in finalRobotGoals:# and currNode != humanSourceNode:# and currNode != humanPrevSourceNode:
                finalRobotGoals[i] = currNode
                foundSequences = constructSequence(i+1, foundSequences)
        return foundSequences

    foundSequences = constructSequence(0, foundSequences=[])

    pprint.pprint(foundSequences)

    return foundSequences[0]

    # finalRobotGoals = []
    # for completedTaskI in robotAppearsAfterTaskIndex:
    #     # Get all the nodes for the (25, 35) change
    #     mergedNodes = set()
    #     for distBucket in [45, 50]:
    #         if distBucket in distanceBucketsToEdges[completedTaskI]:
    #             for node in distanceBucketsToEdges[completedTaskI][distBucket]:
    #                 if node not in freeTimeNodes: mergedNodes.add(node) # The robot should never go to free time nodes
    #     if len(mergedNodes) == 0:
    #         print("No merged Nodes for completedTaskI", completedTaskI)
    #     mergedNodes = list(mergedNodes)
    #     # For every node, get the max distance between it and the human's
    #     # current goal, previous goal, and previous-previous goal, as well as
    #     # the last two robot goals. We want to pick the node that maximizes
    #     # that distance
    #     humanGoalNode = finalSequence[completedTaskI+1]
    #     humanSourceNode = finalSequence[completedTaskI]
    #     humanPrevSourceNode = finalSequence[completedTaskI-1]
    #     prevRobotGoal = finalRobotGoals[-1] if len(finalRobotGoals) > 0 else humanSourceNode
    #     prevPrevRobotGoal = finalRobotGoals[-2] if len(finalRobotGoals) > 1 else humanSourceNode
    #     def sortingFunction(node):
    #         # The robot cannot ask for the help to the same location twice
    #         if node in finalRobotGoals or node == humanSourceNode or node == humanPrevSourceNode:
    #             return 10000
    #         # The robot cannot go to the same goal consecutively
    #         # if len(finalRobotGoals) > 0 and node == prevRobotGoal:
    #         #     return 1000
    #         humanDistancesToMinimize = []
    #         robotDistancesToMinimize = []
    #         if humanGoalNode in mapDistances[node]:
    #             humanDistancesToMinimize.append(mapDistances[node][humanGoalNode]["distance"])
    #         if humanSourceNode in mapDistances[node]:
    #             humanDistancesToMinimize.append(mapDistances[node][humanSourceNode]["distance"])
    #         if humanPrevSourceNode in mapDistances[node]:
    #             humanDistancesToMinimize.append(mapDistances[node][humanPrevSourceNode]["distance"])
    #         if prevRobotGoal in mapDistances[node]:
    #             robotDistancesToMinimize.append(mapDistances[node][prevRobotGoal]["distance"])
    #         if prevPrevRobotGoal in mapDistances[node]:
    #             robotDistancesToMinimize.append(mapDistances[node][prevPrevRobotGoal]["distance"])
    #         minDist = min(humanDistancesToMinimize) + min(robotDistancesToMinimize)*3
    #         return -1*minDist
    #     mergedNodes.sort(key=sortingFunction)
    #     finalRobotGoals.append(mergedNodes[0])

if __name__ == "__main__":
    random.seed(datetime.datetime.now())

    rangeToMergedAdjacencyList, rangeToData, semanticLabelToXYForTargets, mapDistances = processMapDistances("../flask/assets/map_distances.json")

    # Based on the valid ranges, the best ranges seem to be:
    # ((5, 5), [3.4838709677419355, 6.455555555555556, 5, (30, 35)]),
    # ((6, 6), [3.225806451612903, 7.408, 5, (35, 40)]),
    # ((1, 2), [4.774193548387097, 2.9216216216216218, 10, (10, 20)]),
    # ((3, 4), [6.645161290322581, 4.998058252427185, 10, (20, 30)]),
    # ((4, 5), [7.419354838709677, 5.883478260869566, 10, (25, 35)]),
    # ((5, 6), [6.709677419354839, 6.913461538461539, 10, (30, 40)]),
    # ((6, 7), [5.935483870967742, 7.878260869565217, 10, (35, 45)]),
    # ((7, 8), [5.0, 8.863225806451613, 10, (40, 50)])

    numRepeats = 20 # to account for random factors
    for validRange in [(5,5), (6,6), (1,2), (3,4), (4,5), (5,6), (6,7), (7,8)]:
        print("validRange", validRange)
        totalAvgNumDifferentRooms = 0
        for _ in range(numRepeats):
            adjacencyList = rangeToMergedAdjacencyList[validRange]
            avgNumDifferentRooms, foundSequences = generateTaskSequence(adjacencyList, semanticLabelToXYForTargets)
            totalAvgNumDifferentRooms += avgNumDifferentRooms
        rangeToData[validRange].append(totalAvgNumDifferentRooms/numRepeats)
        print("totalAvgNumDifferentRooms/numRepeats", totalAvgNumDifferentRooms/numRepeats)

    # Based on the data, I will go with range (4,5)

    adjacencyList = rangeToMergedAdjacencyList[(4,5)]
    avgNumDifferentRooms, foundSequences = generateTaskSequence(adjacencyList, semanticLabelToXYForTargets)
    pprint.pprint(sorted(foundSequences, key=lambda x: len(set(x)), reverse=True)[0])

    # Based on that, this is the final sequence:
    finalSequence = ['Room 1 Start',
    'Room 10 Start',
    'Lounge Start',
    'Room 33 Start',
    'Room 47 Start',
    'Game Room Start',
    'Room 7 Start',
    'Room 3 Start',
    'Restroom C Start',
    'Room 34 Start',
    'Room 41 Start',
    'Restroom A Start',
    'Room 30 Start',
    'Room 2 Start',
    'Restroom C Start',
    'Room 21 Start',
    'Room 31 Start',
    'Restroom A Start',
    'Room 6 Start',
    'Room 20 Start',
    'Lounge Start',
    'Room 11 Start',
    'Room 22 Start',
    'Restroom B Start',
    'Room 43 Start',
    'Room 31 Start',
    'Game Room Start',
    'Room 8 Start',
    'Room 4 Start']
    # # Old
    # ['Room 1 Start',
    # 'Room 10 Start',
    # 'Lounge Start',
    # 'Room 33 Start',
    # 'Room 47 Start',
    # 'Game Room Start',
    # 'Room 30 Start',
    # 'Room 2 Start',
    # 'Restroom C Start',
    # 'Room 34 Start',
    # 'Room 44 Start',
    # 'Game Room Start',
    # 'Room 7 Start',
    # 'Room 3 Start',
    # 'Restroom C Start',
    # 'Room 21 Start',
    # 'Room 46 Start',
    # 'Game Room Start',
    # 'Room 31 Start',
    # 'Room 1 Start',
    # 'Restroom B Start',
    # 'Room 22 Start',
    # 'Room 11 Start',
    # 'Lounge Start',
    # 'Room 20 Start',
    # 'Room 6 Start',
    # 'Restroom A Start',
    # 'Room 12 Start',
    # 'Room 5 Start']

    robotAppearsAfterTaskIndex = [1,2,4,5,6,8,9,11,12,13,15,16,18,19,20,22,23,25,26,27]
    robotTargets = generateRobotTargets(finalSequence, robotAppearsAfterTaskIndex, mapDistances)

    humanRobotSequence = []
    j = 0
    for i in range(len(finalSequence)):
        if i == robotAppearsAfterTaskIndex[j]+1:
            humanRobotSequence.append((finalSequence[i][:-6], robotTargets[j][:-6]))
            j += 1
        else:
            humanRobotSequence.append((finalSequence[i][:-6], None))
    pprint.pprint(humanRobotSequence)

    # # humanRobotSequence
    # [('Room 1', None),
    # ('Room 10', None),
    # ('Lounge', 'Room 30'),
    # ('Room 33', 'Room 22'),
    # ('Room 47', None),
    # ('Game Room', 'Room 42'),
    # ('Room 7', 'Room 3'),
    # ('Room 3', 'Room 12'),
    # ('Restroom C', None),
    # ('Room 34', 'Room 46'),
    # ('Room 41', 'Room 11'),
    # ('Restroom A', None),
    # ('Room 30', 'Room 2'),
    # ('Room 2', 'Room 20'),
    # ('Restroom C', 'Room 33'),
    # ('Room 21', None),
    # ('Room 31', 'Room 43'),
    # ('Restroom A', 'Room 1'),
    # ('Room 6', None),
    # ('Room 20', 'Room 7'),
    # ('Lounge', 'Room 10'),
    # ('Room 11', 'Room 21'),
    # ('Room 22', None),
    # ('Restroom B', 'Room 6'),
    # ('Room 43', 'Room 31'),
    # ('Room 31', None),
    # ('Game Room', 'Room 44'),
    # ('Room 8', 'Room 4'),
    # ('Room 4', 'Room 32')]

    # Manually selected targets within the rooms in the sequence. "None" for the starting position "Room 1"
    targets = [None,2,2,2,1,2,1,1,1,3,1,1,2,1,1,1,2,1,1,1,1,1,2,1,1,4,3,2,1]

    busynessLevels = ["high", "medium", "free time"]
    jsonRetval = {
        "player_start_location": {
        "x": 4,
        "y": 4,
      },
      "robot_offscreen_location": {
        "x": -1,
        "y": -1,
      },
      "tasks" : [],
    }

    for taskI in range(1, len(finalSequence)):
        jsonRetval["tasks"].append({
            "semanticLabel": finalSequence[taskI][:-6],
            "str": finalSequence[taskI][:-6],
            "target": targets[taskI],
            "busyness": busynessLevels[taskI%3],
        })

    specialProprtions = {
        0 : 0.65,
        18 : 0.75,
        19 : 0.75,
        24 : 0.7,
        26 : 0.7,
    }

    for gameID in range(5):
        jsonRetval["robotActions"] = [];
        for i in range(len(robotAppearsAfterTaskIndex)):
            afterTaskI = robotAppearsAfterTaskIndex[i]-1
            jsonRetval["robotActions"].append({
                "afterHumanTaskIndex": afterTaskI,
                "humanDistanceProportionToNextGoal": specialProprtions[afterTaskI] if afterTaskI in specialProprtions else 0.5,
            })
            if gameID == 0:
                timesToAsk = [4]
            elif gameID == 1:
                timesToAsk = [1,4]
            elif gameID == 2:
                timesToAsk = [1,2,4]
            elif gameID == 3:
                timesToAsk = [0,1,2,4]
            elif gameID == 4:
                timesToAsk = [0,1,2,3,4]
            if (i % 5) in timesToAsk:
                jsonRetval["robotActions"][-1]["robotAction"] = {
                    "query": "leadMe",
                    "targetStr": robotTargets[i][:-6],
                    "targetSemanticLabel": robotTargets[i][:-6],
                }
            else:
                jsonRetval["robotActions"][-1]["robotAction"] = {
                    "query": "walkPast",
                }
        with open("../flask/assets/tasks/{}.json".format(gameID), "w") as f:
            f.write(json.dumps(jsonRetval, indent=4))
