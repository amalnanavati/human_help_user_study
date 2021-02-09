import csv, pprint, os, json, pickle
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from mpl_toolkits.mplot3d import Axes3D
from enum import Enum
import numpy as np
import datetime
import traceback
import shutil
import scipy.stats
import random
import time
import pickle

class PlayerState(Enum):
    NAVIGATION_TASK = 0
    DISTRACTION_TASK = 1
    COMPLETED_TASKS = 2

class RobotState(Enum):
    OFFSCREEN = 0
    APPROACH_HUMAN = 1
    WALK_PAST_HUMAN = 2
    STATIONARY = 3
    LEAVE_SCREEN = 4
    GO_TOWARDS_GOAL = 5

class EventType(Enum):
    MOVEMENT = 0
    CLICK = 1
    INITIAL = 2
    SPACEBAR_START = 3
    SPACEBAR_END = 4
    PLAYER_STATE_CHANGE = 5
    ROBOT_STATE_CHANGE = 6
    SET_HELP_BUBBLE = 7
    SCORE_CHANGE = 8
    TUTORIAL_NEXT_BUTTON_PRESSED = 9
    TUTORIAL_LOAD_STATE = 10
    SHIFT_GAME_KILL = 11
    SHOWING_ENDING_SCREEN = 12
    SHIFT_PRESSED = 13

class ResponseToHelpQuery(Enum):
    IGNORED = 0 # Walked past the robot
    CANT_HELP = 1 # The user clicked "can't help"
    HELPED_ACCURATELY = 2 # the user clicked "yes" and then "stop following" sufficiently close to the robot's goal
    HELPED_INACCURATELY = 3 # the user clicked "yes" and then "stop following" far from to the robot's goal
    HELPED_MISTAKENLY = 4 # the user clicked "yes" and then immediately "stop following"
    AVOIDED = 5 # The user saw the robot and then changed directions to avoid it
    DID_PLAYER_TASK_FIRST = 6 # The user clicked "yes," but then completed their task before / instead of helping the robot

    def toNumber(response):
        if response == ResponseToHelpQuery.HELPED_ACCURATELY:
            return 1
        else:
            return 0

noRobotTaskI = [0,3,7,10,14,17,21,24]
robotAppearsTaskI = [1,2,4,5,6,8,9,11,12,13,15,16,18,19,20,22,23,25,26,27]
robotAppearsBusyness = ["free time", "high", "free time", "high", "medium", "high", "medium", "high", "medium", "free time", "medium", "free time", "medium", "free time", "high", "free time", "high", "free time", "high", "medium"]
taskIForSlowness = [0,3,21,24] # All Medium Busyness
lowestGIDToSharedTaskI = {
    0 : [13,20,27],
    1 : [ 9,13,16,20,23,27],
    2 : [ 9,11,13,16,18,20,23,25,27],
    3 : [ 8, 9,11,13,15,16,18,20,22,23,25,27],
    4 : [ 8, 9,11,12,13,15,16,18,19,20,22,23,25,26,27],
}
lowestGIDToSharedRobotInteractionSeqI = {
    gid : [robotAppearsTaskI.index(taskI) for taskI in lowestGIDToSharedTaskI[gid]] for gid in lowestGIDToSharedTaskI
}

busynessNumericRepresentation = {"high":1/3.0, "medium":1/7.0, "free time":0}

def loadGameLog(filepath, sort=True):
    """
    Input:
      - a filepath that points to a log file

    Output:
      - a list of game logs as dictionaries, ordered by time
    """
    gameLog = []
    with open(filepath, "r") as f:
        for _, line in enumerate(f):
            if len(line.strip()) == 0:
                break
            logEntry = json.loads(line)
            gameLog.append(logEntry)
        # Sometimes, the data arrives a few ms out of order
        if sort:
            if "gameStateID" in gameLog[0]:
                gameLog.sort(key=lambda x : int(x['gameStateID']))
            else:
                gameLog.sort(key=lambda x : int(x['dtime']))
    return gameLog

def loadTaskDefinitionFile(filepath):
    with open(filepath, "r") as f:
        taskDefinition = json.load(f)
    return taskDefinition

def addMinTaskTime(taskDefinitions, filepath):
    with open(filepath, "r") as f:
        minTaskTime = json.load(f)["minTimes"]
    for gid in taskDefinitions:
        for i in range(len(taskDefinitions[gid]["tasks"])):
            taskDefinitions[gid]["tasks"][i]["minTime"] = minTaskTime[i]

def processGameLog(gameLog, taskDefinition, afterTaskI=-1):
    previousLogEntry = None
    playerTaskI = 0
    isRobotHelpQueryActive = False
    didRobotAppear = False
    humanHelpSequence = {"high":[], "medium":[], "free time":[], "overall":[], "robot interaction sequence":[None for i in range(len(taskDefinition["robotActions"]))]}
    didSayYesInRecentPast = False

    print("UUID %s, GID %s" % (gameLog[0]["uuid"], gameLog[0]["gid"]))
    # print("humanHelpSequence", humanHelpSequence)
    # print("taskDefinition", taskDefinition)

    dtimeAtBeginningOfTask = None
    breakTimeDuringTask = 0.0 # Time the user spent away from the tab
    breakTimeThreshold = 30000 # if consecutive dtimes jump by more than this, view it as a break. To account for the 10 sec pressing space
    hasPressedSpaceForThisTaskI = False

    slownessesPerTask = []

    for logEntry in gameLog:
        if previousLogEntry is None:
            dtimeAtBeginningOfTask = int(logEntry["dtime"])
            previousLogEntry = logEntry
            continue

        if "robot" not in previousLogEntry or "robot" not in logEntry:
            previousLogEntry = logEntry
            continue

        if int(logEntry["dtime"]) - int(previousLogEntry["dtime"]) >= breakTimeThreshold:
            print("User took a break between dtime {} and dtime {}".format(previousLogEntry["dtime"], logEntry["dtime"]))
            breakTimeDuringTask += int(logEntry["dtime"]) - int(previousLogEntry["dtime"])

        if "taskI" in logEntry["player"]:
            playerTaskI = int(logEntry["player"]["taskI"])
        else:
            if (int(previousLogEntry["player"]["currentState"]) == PlayerState.DISTRACTION_TASK.value and
                int(logEntry["player"]["currentState"]) == PlayerState.NAVIGATION_TASK.value):
                playerTaskI += 1
                isRobotHelpQueryActive = False
                print("taskI changed", playerTaskI, logEntry["dtime"])

        # print("playerTaskI", playerTaskI, taskDefinition["tasks"])
        if (not hasPressedSpaceForThisTaskI):
            if (int(logEntry["eventType"]) == EventType.SPACEBAR_START.value):
                playerTaskIForPressedSpace = playerTaskI
            elif int(previousLogEntry["player"]["taskI"]) != playerTaskI:
                playerTaskIForPressedSpace = int(previousLogEntry["player"]["taskI"])
            else:
                playerTaskIForPressedSpace = None
            if (playerTaskIForPressedSpace is not None and playerTaskIForPressedSpace < len(taskDefinition["tasks"]) and
                "minTime" in taskDefinition["tasks"][playerTaskIForPressedSpace]):
                print("adding slowness for taskI {} dtime {}".format(playerTaskIForPressedSpace, logEntry["dtime"]))
                hasPressedSpaceForThisTaskI = True
                if int(logEntry["eventType"]) == EventType.SPACEBAR_START.value:
                    elapsedTimeForThisNavigationTask = int(logEntry["dtime"]) - dtimeAtBeginningOfTask - breakTimeDuringTask
                else: # If for some reason space start did not get logged
                    elapsedTimeForThisNavigationTask = int(logEntry["dtime"]) - dtimeAtBeginningOfTask - 10000 - breakTimeDuringTask # the 10 secs for the detraction task
                # print("taskDefinition", taskDefinition, taskDefinition["tasks"], taskDefinition["tasks"][playerTaskIForPressedSpace])
                slowness = elapsedTimeForThisNavigationTask / int(taskDefinition["tasks"][playerTaskIForPressedSpace]["minTime"])
                slownessesPerTask.append(slowness)

        if int(previousLogEntry["player"]["taskI"]) != playerTaskI:
            dtimeAtBeginningOfTask = logEntry["dtime"]
            breakTimeDuringTask = 0.0
            hasPressedSpaceForThisTaskI = False

        previousRobotState = int(previousLogEntry["robot"]["currentState"])
        currentRobotState = int(logEntry["robot"]["currentState"])

        # if playerTaskI == 12:
        #     print(
        #         currentRobotState,
        #         int(logEntry["robot"]["currentTile"]["x"]),
        #         int(logEntry["robot"]["currentTile"]["y"]),
        #         int(logEntry["player"]["currentTile"]["x"]),
        #         int(logEntry["player"]["currentTile"]["y"]),
        #     )

        if didSayYesInRecentPast and len(logEntry["robot"]["taskPlan"]) > 0:
            robotTaskPlanWhenTheHumanSaidYes = logEntry["robot"]["taskPlan"]
            didSayYesInRecentPast = False

        if "buttonName" in logEntry and logEntry["buttonName"] == "Yes":
            didHumanSayYes = True
            didHumanSayStopFollowing = False
            wasHelpAccurate = False
            didHumanSayCantHelp = False
            didSayYesInRecentPast = True
        elif "buttonName" in logEntry and logEntry["buttonName"] == "Stop Following":
            didHumanSayStopFollowing = True
            wasHelpAccurate = len(logEntry["robot"]["taskPlan"]) <= 8 # task plan is the plan to the room, not to the chair within the room
            didHumanSayCantHelp = False
            robotTaskPlanWhenTheHumanSaidStopFollowing = logEntry["robot"]["taskPlan"]
        elif "buttonName" in logEntry and logEntry["buttonName"] == "Can't Help":
            didHumanSayYes = False
            didHumanSayStopFollowing = False
            wasHelpAccurate = False
            didHumanSayCantHelp = True

        if (previousRobotState == RobotState.APPROACH_HUMAN.value and currentRobotState == RobotState.STATIONARY.value):
            print("Began Asking For Help", playerTaskI, logEntry["dtime"])
            isRobotHelpQueryActive = True
            didHumanSayYes = False
            didHumanSayStopFollowing = False
            didHumanSayCantHelp = False
            wasHelpAccurate = False
            if "buttonName" in logEntry and logEntry["buttonName"] == "Yes":
                didHumanSayYes = True
                didHumanSayStopFollowing = False
                wasHelpAccurate = False
                didHumanSayCantHelp = False
                didSayYesInRecentPast = True
            elif "buttonName" in logEntry and logEntry["buttonName"] == "Stop Following":
                didHumanSayStopFollowing = True
                wasHelpAccurate = len(logEntry["robot"]["taskPlan"]) <= 8
                didHumanSayCantHelp = False
                robotTaskPlanWhenTheHumanSaidStopFollowing = logEntry["robot"]["taskPlan"]
            elif "buttonName" in logEntry and logEntry["buttonName"] == "Can't Help":
                didHumanSayYes = False
                didHumanSayStopFollowing = False
                wasHelpAccurate = False
                didHumanSayCantHelp = True
        elif ((isRobotHelpQueryActive and
            ((previousRobotState == RobotState.STATIONARY.value and currentRobotState == RobotState.WALK_PAST_HUMAN.value) or
            (didHumanSayYes and previousRobotState == RobotState.APPROACH_HUMAN.value and currentRobotState == RobotState.WALK_PAST_HUMAN.value) or
            (didHumanSayStopFollowing and previousRobotState == RobotState.APPROACH_HUMAN.value and currentRobotState == RobotState.GO_TOWARDS_GOAL.value))) or  # Bug where the robot goes briefly into approach human for a few steps before walk past -- should be fixed
            didRobotAppear and previousRobotState == RobotState.APPROACH_HUMAN.value and currentRobotState == RobotState.WALK_PAST_HUMAN.value):
            print("Stopped Asking For Help", playerTaskI, logEntry["dtime"], didHumanSayYes, wasHelpAccurate)
            busyness = taskDefinition["tasks"][playerTaskI]["busyness"]
            robotActionI = previousLogEntry["robot"]["currentActionI"]
            if (didHumanSayYes):
                if (wasHelpAccurate):
                    response = ResponseToHelpQuery.HELPED_ACCURATELY
                else:
                    currentPlayerState = int(logEntry["player"]["currentState"])
                    if currentPlayerState == PlayerState.DISTRACTION_TASK.value: # the player completed their task before helping the robot
                        response = ResponseToHelpQuery.DID_PLAYER_TASK_FIRST
                    else:
                        if not didHumanSayStopFollowing:
                            print("Did not say stop following but should have")
                        print("robotTaskPlanWhenTheHumanSaidStopFollowing", len(robotTaskPlanWhenTheHumanSaidStopFollowing), robotTaskPlanWhenTheHumanSaidStopFollowing, "robotTaskPlanWhenTheHumanSaidYes", len(robotTaskPlanWhenTheHumanSaidYes), robotTaskPlanWhenTheHumanSaidYes)
                        if len(robotTaskPlanWhenTheHumanSaidStopFollowing) >= 0.9*len(robotTaskPlanWhenTheHumanSaidYes):
                            response = ResponseToHelpQuery.HELPED_MISTAKENLY
                        else:
                            response = ResponseToHelpQuery.HELPED_INACCURATELY
            else:
                if (didHumanSayCantHelp):
                    response = ResponseToHelpQuery.CANT_HELP
                elif didRobotAppear:
                    response = ResponseToHelpQuery.AVOIDED
                else:
                    response = ResponseToHelpQuery.IGNORED
                print("response", response.name)
            if (playerTaskI > afterTaskI): # skip the first round of help-seeking
                humanHelpSequence[busyness].append(response)
                humanHelpSequence["overall"].append(response)
            humanHelpSequence["robot interaction sequence"][robotActionI] = (busyness, response)
            isRobotHelpQueryActive = False


        if currentRobotState == RobotState.APPROACH_HUMAN.value:
            robotX = int(logEntry["robot"]["currentTile"]["x"])
            robotY = int(logEntry["robot"]["currentTile"]["y"])
            playerX = int(logEntry["player"]["currentTile"]["x"])
            playerY = int(logEntry["player"]["currentTile"]["y"])
            if (abs(playerX-robotX) <= 6 and abs(playerY-robotY) <= 5):
                didRobotAppear = True
        else:
            didRobotAppear = False

        previousLogEntry = logEntry

    print("humanHelpSequence", humanHelpSequence)

    return {descriptor : getAverageHelpRate(humanHelpSequence[descriptor]) for descriptor in humanHelpSequence}, humanHelpSequence, slownessesPerTask

def getAverageHelpRate(sequence):
    total, num = 0, 0
    for response in sequence:
        if response is not None and type(response) != tuple:
            num += 1
            total += response.toNumber()
    return total/num if num != 0 else None

def processSurveyData(filepath):
    # Columns from the CSV
    timeFormat = "%m/%d/%Y %H:%M:%S"
    timeCol = 0
    uuidCol = 1
    nasaTLXCols = {
        "Mental Demand": 2,
        "Physical Demand": 3,
        "Temporal Demand": 4,
        "Performance": 5,
        "Effort": 6,
        "Frustration": 7,
    }
    rosasRawCols = {
        "Reliable": 8,
        "Competent": 9,
        "Knowledgeable": 10,
        "Interactive": 11,
        "Responsive": 12,
        "Capable": 13,
        "Organic": 14,
        "Sociable": 15,
        "Emotional": 16,
        "Compassionate": 17,
        "Happy": 18,
        "Feeling": 19,
        "Awkward": 20,
        "Scary": 21,
        "Strange": 22,
        "Awful": 23,
        "Dangerous": 24,
        "Aggressive": 25,
        "Investigative": 26,
        "Inquisitive": 27,
        "Curious": 28,
    }
    rosasCols = {
        "Competence" : range(8,14),
        "Warmth" : range(14,20),
        "Discomfort" : range(20,26),
        "Curiosity" : range(26,29),
    }
    openEndedCols = {
        "In instances when the robot asked for help, why did you help or not help it?" : 29,
        "In what scenarios would it be acceptable for a real-world robot to ask people for help?" : 30,
        "Did you think the robot was curious? Why or why not?" : 31,
        "Is there anything else you would like us to know?" : 32,
        "In your own words, describe what the robot was doing." : 60,
    }
    demographicCols = {
        "Prosociality" : range(33,49),
        "Navigational Ability" : range(49,56),
        "Video Game Experience" : 56,
        "Age" : 57,
        "Gender" : 58,
    }
    # Likert Scale Mappings
    rosasMapping = {
        "Definitely unassociated" : 1,
        "Moderately unassociated" : 2,
        "Neutral" : 3,
        "Moderately associated" : 4,
        "Definitely associated" : 5,
    }
    prosocialityMapping = {
        "Never / Almost Never True" : 1,
        "Occasionally True" : 2,
        "Sometimes True" : 3,
        "Often True" : 4,
        "Always / Almost Always True" : 5,
    }
    navigationalAbilityMapping = {
        "Not applicable to me" : 1,
        "Seldom applicable to me" : 2,
        "Sometimes applicable to me" : 3,
        "Often applicable to me" : 4,
        "Totally applicable to me" : 5,
    }

    processedData = {}

    with open(filepath, "r") as f:
        reader = csv.reader(f)
        # rowI = 0 # If the header row is 1, the second 501 is row 229
        header = None
        for row in reader:
            # rowI += 1
            if header is None:
                header = row
                continue
            # if rowI == 229: # If the header row is 1, the second 501 is row 229
            #     row[uuidCol] = 505 # replace 501 with 505
            if "8/2/2020 12:15:07" in row[timeCol]:
                row[uuidCol] = 505
            surveyCompletionTime = datetime.datetime.strptime(row[timeCol], "%m/%d/%Y %H:%M:%S").timestamp()
            uuid = int(row[uuidCol])
            if uuid in processedData:
                raise Exception("ERROR: UUID %d has multiple rows rowI %d" % (uuid, rowI))
            processedData[uuid] = {
                "surveyCompletionTime" : surveyCompletionTime,
                "NASA-TLX" : {},
                "RoSAS" : {},
                "RoSAS Raw" : {},
                "Demography" : {},
            }
            for nasaTLXHeading in nasaTLXCols:
                processedData[uuid]["NASA-TLX"][nasaTLXHeading] = int(row[nasaTLXCols[nasaTLXHeading]])
            for rosasHeadingRaw, col in rosasRawCols.items():
                processedData[uuid]["RoSAS Raw"][rosasHeadingRaw] = rosasMapping[row[col]]
            for rosasHeading in rosasCols:
                total, num = 0, 0
                for col in rosasCols[rosasHeading]:
                    total += rosasMapping[row[col]]
                    num += 1
                processedData[uuid]["RoSAS"][rosasHeading] = total/num
            openEndedLengths = []
            for openEndedQ, openEndedCol in openEndedCols.items():
                processedData[uuid][openEndedQ] = row[openEndedCol]
                if openEndedCol != 32: # only count the required Qs
                    openEndedLengths.append(len(row[openEndedCol]))
            # Median
            if (len(openEndedLengths) % 2 == 0):
                openEndedLength = (openEndedLengths[(len(openEndedLengths)//2)-1]+openEndedLengths[(len(openEndedLengths)//2)])/2
            else:
                openEndedLength = openEndedLengths[(len(openEndedLengths)//2)]
            # # Mean
            # openEndedLength = sum(openEndedLengths)/len(openEndedLengths)
            # # Max
            # openEndedLength = max(openEndedLengths)
            processedData[uuid]["Demography"]["Open Ended Length"] = openEndedLength
            rosasMean = sum(processedData[uuid]["RoSAS Raw"].values())/len(processedData[uuid]["RoSAS Raw"])
            rosasVariance = sum([(rosasMean-rosasVal)**2.0 for rosasVal in processedData[uuid]["RoSAS Raw"].values()])/len(processedData[uuid]["RoSAS Raw"])
            processedData[uuid]["Demography"]["RoSAS Variance"] = rosasVariance
            for demographicHeading, demographicCol in demographicCols.items():
                if demographicHeading == "Prosociality":
                    total, num = 0, 0
                    for col in demographicCol:
                        total += prosocialityMapping[row[col]]
                        num += 1
                    processedData[uuid]["Demography"][demographicHeading] = total/num
                elif demographicHeading == "Navigational Ability":
                    total, num = 0, 0
                    for col in demographicCol:
                        total += navigationalAbilityMapping[row[col]]
                        num += 1
                    processedData[uuid]["Demography"][demographicHeading] = total/num
                else:
                    try:
                        val = int(row[demographicCol])
                    except:
                        val = row[demographicCol]
                    processedData[uuid]["Demography"][demographicHeading] = val

    return processedData

def getTimes(surveyData, uuid, baseDir):
    for filename in ["startTime.txt", "tutorialTime.txt", "gameTime.txt", "surveyTime.txt", "endTime.txt"]:
        try:
            with open(baseDir+"{}/".format(uuid)+filename, "r") as f:
                timeFloat = float(f.read().strip())
                surveyData[uuid][filename[:-4]] = timeFloat
        except Exception as e:
            print(e)
            print(traceback.print_exc())
    surveyElapsedSecs = surveyData[uuid]["surveyCompletionTime"]-surveyData[uuid]["surveyTime"]
    surveyData[uuid]["Demography"]["Survey Duration"] = surveyElapsedSecs
    return

def makeGraphs(surveyData, descriptor=""):
    # Partition UUID by Prosociality
    allUUIDs = [uuid for uuid in surveyData]
    allUUIDs.sort(key = lambda uuid: surveyData[uuid]["Demography"]["Prosociality"])
    if (len(allUUIDs) % 2 == 0):
        prosocialityMedian = (surveyData[allUUIDs[len(allUUIDs)//2-1]]["Demography"]["Prosociality"]+surveyData[allUUIDs[len(allUUIDs)//2]]["Demography"]["Prosociality"])/2
    else:
        prosocialityMedian = surveyData[allUUIDs[(len(allUUIDs)-1)//2]]["Demography"]["Prosociality"]
    prosocialityLow = allUUIDs[0:len(allUUIDs)//2]
    prosocialityHigh = allUUIDs[len(allUUIDs)//2:]

    # Generate Graphs
    freqs = []
    gids = []
    gidCount = {i : 0 for i in range(5)}
    rosasFactorsOrder = ["Competence", "Discomfort", "Warmth", "Curiosity"]
    rosas = {factor : [] for factor in rosasFactorsOrder}
    nasaTLXFactorOrder = ["Mental Demand", "Physical Demand", "Temporal Demand", "Performance", "Effort", "Frustration"]
    nasaTLX = {factor : [] for factor in nasaTLXFactorOrder}
    busynessFactorOrder = ["high", "medium", "free time"]
    busyness = {factor : [] for factor in busynessFactorOrder}
    busynessToGIDToWillingnessToHelp = {factor : {i : [] for i in range(5)} for factor in busynessFactorOrder}
    prosociality = {"low: < {} (median)".format(prosocialityMedian) : ([], []), "high: >= {} (median)".format(prosocialityMedian) : ([], [])}
    busynessToProsocialityToWillingnessToHelp = {factor : {factor2 : [] for factor2 in prosociality} for factor in busynessFactorOrder}
    demographicFactors = ["Prosociality", "Navigational Ability", "Video Game Experience", "Age", "Gender", "Survey Duration", "Open Ended Length", "RoSAS Variance", "tutorialOverallHelping", "Slowness"]
    demography = {factor : [] for factor in demographicFactors}
    perPersonWillingenessToHelp = {i : [] for i in range(5)} # {GID -> [list of {busyness -> (willingnessToHelp, slowness)}] }
    frequencyToSequence = {(i+1)/5.0 : [[(i, surveyData[uuid]['humanHelpSequence']['robot interaction sequence'][i]) for i in range(len(surveyData[uuid]['humanHelpSequence']['robot interaction sequence'])) if surveyData[uuid]['humanHelpSequence']['robot interaction sequence'][i] is not None] for uuid in surveyData if surveyData[uuid]["gid"] == i] for i in range(5)}
    surveyDurations = []
    openEndedLengths = []
    rosasVariances = []
    tutorialOverallHelpings = []
    for uuid in surveyData:
        gid = surveyData[uuid]["gid"]
        gids.append(gid)
        gidCount[gid] += 1
        freq = (gid+1)/5.0
        freqs.append(freq)
        perPersonWillingenessToHelp[gid].append({})
        # RoSAS
        for factor in rosasFactorsOrder:
            rosas[factor].append(surveyData[uuid]["RoSAS"][factor])
        # NASA-TLX
        for factor in nasaTLXFactorOrder:
            nasaTLX[factor].append(surveyData[uuid]["NASA-TLX"][factor])
        # Busyness Factors
        for factor in busynessFactorOrder:
            busyness[factor].append(surveyData[uuid]["helpGivingData"][factor])
            busynessToGIDToWillingnessToHelp[factor][gid].append(surveyData[uuid]["helpGivingData"][factor])
            perPersonWillingenessToHelp[gid][-1][factor] = (surveyData[uuid]["helpGivingData"][factor], surveyData[uuid]["Demography"]['Slowness'], surveyData[uuid]["Demography"]['Prosociality'])
        # prosociality
        factor = "overall"
        if uuid in prosocialityLow:
            key = "low: < {} (median)".format(prosocialityMedian)
            prosociality[key][0].append(freq)
            prosociality[key][1].append(surveyData[uuid]["helpGivingData"][factor])
            for factor2 in busynessFactorOrder:
                busynessToProsocialityToWillingnessToHelp[factor2][key].append(surveyData[uuid]["helpGivingData"][factor])
        else:
            key = "high: >= {} (median)".format(prosocialityMedian)
            prosociality[key][0].append(freq)
            prosociality[key][1].append(surveyData[uuid]["helpGivingData"][factor])
            for factor2 in busynessFactorOrder:
                busynessToProsocialityToWillingnessToHelp[factor2][key].append(surveyData[uuid]["helpGivingData"][factor])
        # Demographic Factors
        for factor in demographicFactors:
            if factor in surveyData[uuid]["Demography"]:
                demography[factor].append(surveyData[uuid]["Demography"][factor])
            else:
                demography[factor].append(-100.0) # I am setting this at an absurd value so I remember that it is an easy fix and should be changed if I want proper graphs
        if "Survey Duration" in surveyData[uuid]["Demography"]:
            surveyDurations.append((surveyData[uuid]["Demography"]["Survey Duration"], uuid))
        else:
            surveyDurations.append((-100, uuid))
        openEndedLengths.append((surveyData[uuid]["Demography"]["Open Ended Length"], uuid))
        rosasVariances.append((surveyData[uuid]["Demography"]["RoSAS Variance"], uuid))
        tutorialOverallHelpings.append((surveyData[uuid]["Demography"]["tutorialOverallHelping"], uuid))
        if surveyData[uuid]["Demography"]["tutorialOverallHelping"] is None:
            print("uuid", uuid)
            pprint.pprint(surveyData[uuid])
            raise Exception("tutoriaOverallHelping None")

    print("gidCount", gidCount, len(gids))
    surveyDurations.sort()
    print("surveyDurations", surveyDurations)
    openEndedLengths.sort()
    print("Open Ended Length", openEndedLengths)
    rosasVariances.sort()
    print("RoSAS Variances", rosasVariances)
    tutorialOverallHelpings.sort()
    print("tutorialOverallHelpings", tutorialOverallHelpings)

    colors = ["b", "r", "g", "m", "k"]

    # RoSAS
    fig = plt.figure(figsize=(8,8))
    axes = fig.subplots(len(rosasFactorsOrder), 1)
    fig.suptitle('RoSAS Results By Frequency')
    for i in range(len(axes)):
        factor = rosasFactorsOrder[i]

        # axes[i].scatter(freqs, rosas[factor], c=colors[i%len(colors)])
        # axes[i].set_xlim([0,1.1])

        boxplotData = [[] for k in range(numGIDs)]
        for k in range(len(freqs)):
            gid = int(freqs[k]*5.0)-1
            boxplotData[gid].append(rosas[factor][k])
        axes[i].boxplot(boxplotData, showmeans=True)
        axes[i].set_xticklabels(["0.2", "0.4", "0.6", "0.8", "1.0"])

        axes[i].set_ylim([1,5.5])
        axes[i].set_yticks(range(1,6))
        axes[i].set_xlabel("Frequency")
        axes[i].set_ylabel(factor)

    # plt.show()
    plt.savefig(baseDir + "rosas{}.png".format(descriptor))
    plt.clf()

    # NASA-TLX
    fig = plt.figure(figsize=(8,12))
    axes = fig.subplots(len(nasaTLXFactorOrder), 1)
    fig.suptitle('NASA-TLX Results By Frequency')
    for i in range(len(axes)):
        factor = nasaTLXFactorOrder[i]

        # axes[i].scatter(freqs, nasaTLX[factor], c=colors[i%len(colors)])
        # axes[i].set_xlim([0,1.1])

        boxplotData = [[] for k in range(numGIDs)]
        for k in range(len(freqs)):
            gid = int(freqs[k]*5.0)-1
            boxplotData[gid].append(nasaTLX[factor][k])
        axes[i].boxplot(boxplotData, showmeans=True)
        axes[i].set_xticklabels(["0.2", "0.4", "0.6", "0.8", "1.0"])

        axes[i].set_ylim([1,10.5])
        axes[i].set_yticks(range(1,11))
        axes[i].set_xlabel("Frequency")
        axes[i].set_ylabel(factor)
    # plt.show()
    plt.savefig(baseDir + "nasaTLX{}.png".format(descriptor))
    plt.clf()

    # Busyness
    fig = plt.figure(figsize=(8,10))
    axes = fig.subplots(len(busynessFactorOrder), 1)
    fig.suptitle('Willingness To Help vs. Frequency')
    for i in range(len(axes)):
        factor = busynessFactorOrder[i]

        # axes[i].scatter(freqs, busyness[factor], c=colors[i%len(colors)])
        # axes[i].set_xlim([0,1.1])

        boxplotData = [[] for k in range(numGIDs)]
        for k in range(len(freqs)):
            gid = int(freqs[k]*5.0)-1
            if (busyness[factor][k] is None): continue
            boxplotData[gid].append(busyness[factor][k])
        axes[i].boxplot(boxplotData, showmeans=True)
        axes[i].set_xticklabels(["0.2", "0.4", "0.6", "0.8", "1.0"])

        axes[i].set_ylim([-0.1,1.1])
        axes[i].set_title("Busyness: %s" % factor)
        axes[i].set_xlabel("Frequency")
        axes[i].set_ylabel("Willingness to Help")
    # plt.show()
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(baseDir + "willingnessToHelpBusyness{}.png".format(descriptor))
    plt.clf()

    # Prosociality
    fig = plt.figure(figsize=(8,10))
    axes = fig.subplots(len(prosociality), 1)
    fig.suptitle('Willingness To Help vs. Frequency')
    i = 0
    for factor in prosociality:

        # axes[i].scatter(prosociality[factor][0], prosociality[factor][1], c=colors[i%len(colors)])
        # axes[i].set_xlim([0,1.1])

        boxplotData = [[] for k in range(numGIDs)]
        for k in range(len(prosociality[factor][0])):
            gid = int(prosociality[factor][0][k]*5.0)-1
            boxplotData[gid].append(prosociality[factor][1][k])
        axes[i].boxplot(boxplotData, showmeans=True)
        axes[i].set_xticklabels(["0.2", "0.4", "0.6", "0.8", "1.0"])

        axes[i].set_ylim([-0.1,1.1])
        axes[i].set_title("Prosociality: %s" % factor)
        axes[i].set_xlabel("Frequency")
        axes[i].set_ylabel("Willingness to Help")
        i += 1
    # plt.show()
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(baseDir + "willingnessToHelpProsociality{}.png".format(descriptor))
    plt.clf()

    # Busyness and Freq Histograms
    fig = plt.figure(figsize=(16,10))
    axes = fig.subplots(len(busynessFactorOrder), 5)
    fig.suptitle('Willingness To Help By Busyness and Frequency')
    for i in range(len(axes)):
        factor = busynessFactorOrder[i]
        for k in range(len(axes[i])):
            freq = (k+1)/5.0
            axes[i][k].hist(busynessToGIDToWillingnessToHelp[factor][k])
            axes[i][k].set_xlim([0,1])
            axes[i][k].set_ylim([0,30])
            axes[i][k].set_title("Busyness: %s, Freq: %.01f" % (factor, freq))
            axes[i][k].set_xlabel("Willingness To Help")
            axes[i][k].set_ylabel("Count")
    # plt.show()
    fig.align_ylabels(axes)
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(baseDir + "willingnessToHelpBusynessHistograms{}.png".format(descriptor))
    plt.clf()

    # Busyness and Prosociality Histograms
    fig = plt.figure(figsize=(16,10))
    axes = fig.subplots(len(busynessFactorOrder), 2)
    fig.suptitle('Willingness To Help By Busyness and Prosociality')
    for i in range(len(axes)):
        factor = busynessFactorOrder[i]
        k = -1
        for prosocialityFactor in busynessToProsocialityToWillingnessToHelp[factor]:
            k += 1
            axes[i][k].hist(busynessToProsocialityToWillingnessToHelp[factor][prosocialityFactor])
            axes[i][k].set_xlim([0,1])
            axes[i][k].set_ylim([0,30])
            axes[i][k].set_title("Busyness: %s, Prosociality: %s" % (factor, prosocialityFactor))
            axes[i][k].set_xlabel("Willingness To Help")
            axes[i][k].set_ylabel("Count")
    # plt.show()
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(baseDir + "willingnessToHelpProsocialityHistograms{}.png".format(descriptor))
    plt.clf()

    # Demographic Factors
    for factor in demographicFactors:
        fig = plt.figure()
        ax = fig.subplots(1,2)
        fig.suptitle('Demographic Makeup: '+factor)
        ax[0].hist(demography[factor])
        ax[0].set_xlabel(factor)
        ax[0].set_ylabel("Count")
        if factor in ["Prosociality", "Navigational Ability", "Video Game Experience"]:
            ax[0].set_xlim([0,5.5])
        try:
            ax[1].boxplot(demography[factor], showmeans=True)
            ax[1].set_ylabel(factor)
        except Exception as err:
            pass
        plt.savefig(baseDir + "%s%s.png" % (factor, descriptor))
        plt.clf()

    # GIDs
    fig = plt.figure()
    ax = fig.subplots()
    fig.suptitle('GIDs')
    ax.hist(gids)
    ax.set_xlabel("Game ID")
    ax.set_ylabel("Count")
    plt.savefig(baseDir + "gids{}.png".format(descriptor))
    plt.clf()

    # 3D scatterplot
    markers = ["o", "^", "s", "+", "X"]
    markerToXYZ = {marker : [[], [], [], ""] for marker in markers}
    markerToFreq = {}
    freqToXYZ = {freq : [] for freq in freqs}
    for uuid in surveyData:
        gid = surveyData[uuid]["gid"]
        freq = (gid+1)/5.0
        marker = markers[gid]
        markerToFreq[marker] = freq
        x = surveyData[uuid]['helpGivingData']['high']
        y = surveyData[uuid]['helpGivingData']['medium']
        z = surveyData[uuid]['helpGivingData']['free time']
        markerToXYZ[marker][0].append(x)
        markerToXYZ[marker][1].append(y)
        markerToXYZ[marker][2].append(z)
        markerToXYZ[marker][3] = "Freq: %.1f" % (freq)
        freqToXYZ[freq].append([x,y,z])
    freqToAvgXVY = {freq : np.mean(freqToXYZ[freq], axis=0) for freq in freqToXYZ}

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    for marker in markerToXYZ:
        if marker in markerToFreq:
            ax.scatter(
                markerToXYZ[marker][0]+[freqToAvgXVY[markerToFreq[marker]][0]],
                markerToXYZ[marker][1]+[freqToAvgXVY[markerToFreq[marker]][1]],
                markerToXYZ[marker][2]+[freqToAvgXVY[markerToFreq[marker]][2]],
                label=markerToXYZ[marker][3],
                marker=marker,
            )
    freqOrder = [(gid+1)/5.0 for gid in range(5)]
    xs = [freqToAvgXVY[freq][0] for freq in freqOrder]
    ys = [freqToAvgXVY[freq][1] for freq in freqOrder]
    zs = [freqToAvgXVY[freq][2] for freq in freqOrder]
    ax.plot(
        xs,
        ys,
        zs,
        linestyle='-',
    )

    ax.set_xlabel('Willingness to Help for High')
    ax.set_ylabel('Willingness to Help for Medium')
    ax.set_zlabel('Willingness to Help for Free Time')
    ax.legend()

    plt.savefig(baseDir + "fullScatter{}.png".format(descriptor))
    # plt.show()
    plt.clf()

    # 3D scatterplot by count
    uniqueXYZToCount = {}
    for uuid in surveyData:
        gid = surveyData[uuid]["gid"]
        x = surveyData[uuid]['helpGivingData']['high']
        y = surveyData[uuid]['helpGivingData']['medium']
        z = surveyData[uuid]['helpGivingData']['free time']
        if (x,y,z) not in uniqueXYZToCount:
            uniqueXYZToCount[(x,y,z)] = 0
        uniqueXYZToCount[(x,y,z)] += 1

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    xs, ys, zs, cs = [], [], [], []
    for x,y,z in uniqueXYZToCount:
        xs.append(x)
        ys.append(y)
        zs.append(z)
        cs.append(uniqueXYZToCount[(x,y,z)])
    im = ax.scatter(
        xs,
        ys,
        zs,
        c=cs,
    )

    ax.set_xlabel('Willingness to Help for High')
    ax.set_ylabel('Willingness to Help for Medium')
    ax.set_zlabel('Willingness to Help for Free Time')
    ax.legend()
    fig.colorbar(im, ax=ax)

    plt.savefig(baseDir + "fullScatterByCount{}.png".format(descriptor))
    plt.clf()

    # 3D Histogram
    high = []
    medium = []
    freeTime = []
    for uuid in surveyData:
        high.append(surveyData[uuid]['helpGivingData']['high'])
        medium.append(surveyData[uuid]['helpGivingData']['medium'])
        freeTime.append(surveyData[uuid]['helpGivingData']['free time'])

    fig = plt.figure(figsize=(16,8))

    i = 0
    for x, xlabel, y, ylabel in [[high, "High", medium, "Medium"], [high, "High", freeTime, "Free Time"], [medium, "Medium", freeTime, "Free Time"]]:
        i += 1
        ax = fig.add_subplot(130+i, title='Willingness To Help Histogram')
        hist, xedges, yedges = np.histogram2d(x, y, bins=10)#, range=[[0, 1], [0, 1]])
        X, Y = np.meshgrid(xedges, yedges)
        im = ax.pcolormesh(X, Y, hist.T)
        ax.set_xlabel("Willingness to Help for "+xlabel)
        ax.set_ylabel("Willingness to Help for "+ylabel)
        fig.colorbar(im, ax=ax)

    fig.tight_layout()
    plt.savefig(baseDir + "busynessHistogram{}.png".format(descriptor))
    plt.clf()

    # perPersonWillingenessToHelp with busyness on x axis
    fig = plt.figure(figsize=(8,10))
    axes = fig.subplots(len(perPersonWillingenessToHelp), 1)
    fig.suptitle('Willingness To Help vs. Busyness')
    for gid in range(len(axes)):
        for onePersonsData in perPersonWillingenessToHelp[gid]:
            xs, ys = [], []
            for busyness in onePersonsData:
                xs.append(busynessNumericRepresentation[busyness])
                ys.append(onePersonsData[busyness][0])
            axes[gid].plot(xs, ys)
        axes[gid].set_ylim([-0.1,1.1])
        axes[gid].set_title("Frequency: %1.1f" % ((gid+1)/5.0))
        axes[gid].set_xlabel("Busyness")
        axes[gid].set_ylabel("Willingness to Help")
    # plt.show()
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(baseDir + "perPersonWillingnessToHelpBusyness{}.png".format(descriptor))
    plt.clf()

    # perPersonWillingenessToHelp3D with busyness on x axis and slowness on y axis
    for gid in perPersonWillingenessToHelp:
        freq = (gid+1)/5.0
        fig = plt.figure(figsize=(8,10))
        axes = fig.add_subplot(111, projection='3d')
        fig.suptitle('Willingness To Help vs. Busyness and Slowness, Freq {}'.format(freq))
        for onePersonsData in perPersonWillingenessToHelp[gid]:
            xs, ys, zs = [], [], []
            for busyness in onePersonsData:
                xs.append(busynessNumericRepresentation[busyness])
                ys.append(onePersonsData[busyness][1])
                zs.append(onePersonsData[busyness][0])
            axes.plot(xs, ys, zs)
        axes.set_zlim([-0.1,1.1])
        # axes.set_title("Frequency: %1.1f" % ((gid+1)/5.0))
        axes.set_xlabel("Busyness")
        axes.set_ylabel("Slowness")
        axes.set_zlabel("Willingness to Help")
        # plt.show()
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.savefig(baseDir + "perPersonWillingnessToHelp3DBusynessSlowness_Freq{}_{}.png".format(freq, descriptor))
        plt.clf()

    # perPersonWillingenessToHelp3D with busyness on x axis and prosociality on y axis
    for gid in perPersonWillingenessToHelp:
        freq = (gid+1)/5.0
        fig = plt.figure(figsize=(8,10))
        axes = fig.add_subplot(111, projection='3d')
        fig.suptitle('Willingness To Help vs. Busyness and Slowness, Freq {}'.format(freq))
        for onePersonsData in perPersonWillingenessToHelp[gid]:
            xs, ys, zs = [], [], []
            for busyness in onePersonsData:
                xs.append(busynessNumericRepresentation[busyness])
                ys.append(onePersonsData[busyness][2])
                zs.append(onePersonsData[busyness][0])
            axes.plot(xs, ys, zs)
        axes.set_zlim([-0.1,1.1])
        # axes.set_title("Frequency: %1.1f" % ((gid+1)/5.0))
        axes.set_xlabel("Busyness")
        axes.set_ylabel("Prosociality")
        axes.set_zlabel("Willingness to Help")
        # plt.show()
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.savefig(baseDir + "perPersonWillingnessToHelp3DBusynessProsociality_Freq{}_{}.png".format(freq, descriptor))
        plt.clf()

    # Frequency to Sequence
    busynessToColor = {"high":"r", "medium":"b", "free time":"g"}
    for freq in frequencyToSequence:
        fig = plt.figure(figsize=(28,16))
        axes = fig.subplots(4, 7)
        i = -1
        for responseSequence in frequencyToSequence[freq]:
            i += 1
            rowI = i // 7
            colI = i % 7
            xs = []
            ys = []
            xsByBusyness = {}
            ysByBusyness = {}
            for seqI, (busyness, response) in responseSequence:
                x = robotAppearsTaskI[seqI]
                y = response.toNumber()
                xs.append(x)
                ys.append(y)
                if busyness not in xsByBusyness: xsByBusyness[busyness] = []
                xsByBusyness[busyness].append(x)
                if busyness not in ysByBusyness: ysByBusyness[busyness] = []
                ysByBusyness[busyness].append(y)
            # Add the human response line
            axes[rowI][colI].plot(xs, ys, c="k")
            # Add busyness data
            for busyness in xsByBusyness:
                axes[rowI][colI].scatter(xsByBusyness[busyness], ysByBusyness[busyness], c=busynessToColor[busyness])
            # Add vertical lines where the robot walked past
            for taskI in robotAppearsTaskI:
                if taskI not in xs:
                    axes[rowI][colI].axvline(taskI, c=[1.0,0.0,0.0,0.5], linestyle="--")
            # Add vertical lines for when there was no robot
            for taskI in noRobotTaskI:
                axes[rowI][colI].axvline(taskI, c=[0.0,1.0,0.0,0.5], linestyle="--")
            axes[rowI][colI].set_ylim([-0.1,1.1])
            axes[rowI][colI].set_xlabel("Task I")
            axes[rowI][colI].set_ylabel("Did Human Help?")
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.savefig(baseDir + "everyPersonData_freq_{}_{}.png".format(freq, descriptor))
        plt.clf()

    # (freqOfAsking, willingnessToHelp) to count
    # Busyness and Freq Histograms
    fig = plt.figure(figsize=(16,10))
    axes = fig.subplots(1, len(busynessFactorOrder))
    fig.suptitle('Proportion People at each (Frequency, WillingnessToHelp) tuple')
    for i in range(len(axes)):
        factor = busynessFactorOrder[i]
        xyToCount = {}
        freqToCount = {}
        for gid in range(len(busynessToGIDToWillingnessToHelp[factor])):
            freq = (gid+1)/5.0
            freqToCount[freq] = 0
            for willingnessToHelp in busynessToGIDToWillingnessToHelp[factor][gid]:
                freqToCount[freq] += 1
                if (freq, willingnessToHelp) not in xyToCount:
                    xyToCount[(freq, willingnessToHelp)] = 0
                xyToCount[(freq, willingnessToHelp)] += 1
        xs, ys, cs = [], [], []
        for freq, willingnessToHelp in xyToCount:
            xs.append(freq)
            ys.append(willingnessToHelp)
            cs.append(xyToCount[(freq, willingnessToHelp)]/freqToCount[freq])

        # # add a fake datapoint to get the complete colorbar range
        # xs.append(-1)
        # ys.append(-1)
        # cs.append(1.0)

        scatterplot = axes[i].scatter(xs, ys, c=cs)
        axes[i].set_xlim([0.1,1.1])
        axes[i].set_ylim([-0.1,1.1])
        axes[i].set_title("Busyness: %s" % (factor))
        axes[i].set_xlabel("Frequency of Asking")
        axes[i].set_ylabel("Willingness To Help")
        fig.colorbar(scatterplot, cmap=cm.cool, ax=axes[i])
    # plt.show()
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(baseDir + "freqWillingnessToHelpDistribution{}.png".format(descriptor))
    plt.clf()

    # # Construct arrays for the anchor positions of the 16 bars.
    # fig = plt.figure()
    # ax = fig.add_subplot(111, projection='3d')
    # xpos, ypos = np.meshgrid(xedges[:-1] + 0.25, yedges[:-1] + 0.25, indexing="ij")
    # xpos = xpos.ravel()
    # ypos = ypos.ravel()
    # zpos = 0
    #
    # # Construct arrays with the dimensions for the 16 bars.
    # dx = dy = 0.5 * np.ones_like(zpos)
    # dz = hist.ravel()
    #
    # ax.bar3d(xpos, ypos, zpos, dx, dy, dz, zsort='average')
    # ax.set_xlabel('Willingness to Help for High')
    # ax.set_ylabel('Willingness to Help for Medium / Free Time')
    # ax.set_zlabel('Count')
    #
    # plt.show()

def writeCSV(surveyData, taskDefinitions, filepath, numericFilepath, separatedByTaskIFilepath):
    header = [
        "User ID",
        "Frequency",
        "High Busyness Willingness To Help",
        "Medium Busyness Willingness To Help",
        "Free Time Busyness Willingness To Help",
        "Overall Willingness To Help",
        "RoSAS Competence",
        "RoSAS Discomfort",
        "RoSAS Warmth",
        "RoSAS Curiosity",
        "NASA-TLX Effort",
        "NASA-TLX Frustration",
        "NASA-TLX Mental Demand",
        "NASA-TLX Performance",
        "NASA-TLX Physical Demand",
        "NASA-TLX Temporal Demand",
        "In your own words, describe what the robot was doing.",
        "In instances when the robot asked for help, why did you help or not help it?",
        "In what scenarios would it be acceptable for a real-world robot to ask people for help?",
        "Did you think the robot was curious? Why or why not?",
        "Is there anything else you would like us to know?",
        "Age",
        "Gender",
        "Navigational Ability",
        "Prosociality",
        "Video Game Experience",
        "Survey Duration",
        "Slowness",
        "RoSAS Raw Reliable",
        "RoSAS Raw Competent",
        "RoSAS Raw Knowledgeable",
        "RoSAS Raw Interactive",
        "RoSAS Raw Responsive",
        "RoSAS Raw Capable",
        "RoSAS Raw Organic",
        "RoSAS Raw Sociable",
        "RoSAS Raw Emotional",
        "RoSAS Raw Compassionate",
        "RoSAS Raw Happy",
        "RoSAS Raw Feeling",
        "RoSAS Raw Awkward",
        "RoSAS Raw Scary",
        "RoSAS Raw Strange",
        "RoSAS Raw Awful",
        "RoSAS Raw Dangerous",
        "RoSAS Raw Aggressive",
        "RoSAS Raw Investigative",
        "RoSAS Raw Inquisitive",
        "RoSAS Raw Curious",
        "Tutorial Overall Willingness to Help"
    ] + ["Human Response %d" % i for i in range(len(taskDefinitions[0]["robotActions"]))]
    with open(filepath, "w") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow(header)
        i = 0
        for uuid in surveyData:
            row = [uuid]
            row.append((surveyData[uuid]["gid"]+1)/5.0)
            row.append(surveyData[uuid]['helpGivingData']['high'])
            row.append(surveyData[uuid]['helpGivingData']['medium'])
            row.append(surveyData[uuid]['helpGivingData']['free time'])
            row.append(surveyData[uuid]['helpGivingData']['overall'])
            row.append(surveyData[uuid]['RoSAS']['Competence'])
            row.append(surveyData[uuid]['RoSAS']['Curiosity'])
            row.append(surveyData[uuid]['RoSAS']['Discomfort'])
            row.append(surveyData[uuid]['RoSAS']['Warmth'])
            row.append(surveyData[uuid]['NASA-TLX']['Effort'])
            row.append(surveyData[uuid]['NASA-TLX']['Frustration'])
            row.append(surveyData[uuid]['NASA-TLX']['Mental Demand'])
            row.append(surveyData[uuid]['NASA-TLX']['Performance'])
            row.append(surveyData[uuid]['NASA-TLX']['Physical Demand'])
            row.append(surveyData[uuid]['NASA-TLX']['Temporal Demand'])
            row.append(surveyData[uuid]['In your own words, describe what the robot was doing.'].replace("\n", "\\n"))
            row.append(surveyData[uuid]['In instances when the robot asked for help, why did you help or not help it?'].replace("\n", "\\n"))
            row.append(surveyData[uuid]['In what scenarios would it be acceptable for a real-world robot to ask people for help?'].replace("\n", "\\n"))
            row.append(surveyData[uuid]['Did you think the robot was curious? Why or why not?'].replace("\n", "\\n"))
            row.append(surveyData[uuid]['Is there anything else you would like us to know?'].replace("\n", "\\n"))
            row.append(surveyData[uuid]['Demography']['Age'])
            row.append(surveyData[uuid]['Demography']['Gender'])
            row.append(surveyData[uuid]['Demography']['Navigational Ability'])
            row.append(surveyData[uuid]['Demography']['Prosociality'])
            row.append(surveyData[uuid]['Demography']['Video Game Experience'])
            row.append(surveyData[uuid]['Demography']['Survey Duration'] if 'Survey Duration' in surveyData[uuid]['Demography'] else "")
            row.append(surveyData[uuid]['Demography']['Slowness'])
            row.append(surveyData[uuid]['RoSAS Raw']['Reliable'])
            row.append(surveyData[uuid]['RoSAS Raw']['Competent'])
            row.append(surveyData[uuid]['RoSAS Raw']['Knowledgeable'])
            row.append(surveyData[uuid]['RoSAS Raw']['Interactive'])
            row.append(surveyData[uuid]['RoSAS Raw']['Responsive'])
            row.append(surveyData[uuid]['RoSAS Raw']['Capable'])
            row.append(surveyData[uuid]['RoSAS Raw']['Organic'])
            row.append(surveyData[uuid]['RoSAS Raw']['Sociable'])
            row.append(surveyData[uuid]['RoSAS Raw']['Emotional'])
            row.append(surveyData[uuid]['RoSAS Raw']['Compassionate'])
            row.append(surveyData[uuid]['RoSAS Raw']['Happy'])
            row.append(surveyData[uuid]['RoSAS Raw']['Feeling'])
            row.append(surveyData[uuid]['RoSAS Raw']['Awkward'])
            row.append(surveyData[uuid]['RoSAS Raw']['Scary'])
            row.append(surveyData[uuid]['RoSAS Raw']['Strange'])
            row.append(surveyData[uuid]['RoSAS Raw']['Awful'])
            row.append(surveyData[uuid]['RoSAS Raw']['Dangerous'])
            row.append(surveyData[uuid]['RoSAS Raw']['Aggressive'])
            row.append(surveyData[uuid]['RoSAS Raw']['Investigative'])
            row.append(surveyData[uuid]['RoSAS Raw']['Inquisitive'])
            row.append(surveyData[uuid]['RoSAS Raw']['Curious'])
            row.append(surveyData[uuid]['Demography']['tutorialOverallHelping'])
            for i in range(len(taskDefinitions[0]["robotActions"])):
                if surveyData[uuid]['humanHelpSequence']['robot interaction sequence'][i] is None:
                    response = None
                else:
                    _, response = surveyData[uuid]['humanHelpSequence']['robot interaction sequence'][i]
                if response is None:
                    if taskDefinitions[surveyData[uuid]["gid"]]["robotActions"][i]["robotAction"]["query"] == "walkPast":
                        row.append("ROBOT_NOT_ASK_CONDITION")
                    else:
                        row.append("NEVER_SAW_ROBOT")
                        print("Response none on not walkPast, uuid {}, i {}".format(uuid, i))
                else:
                    row.append(response.name)

            writer.writerow(row)
            i += 1
        print("wrote {} data rows".format(i))

        for gid in range(5):
            # freq = (gid+1)/5.0
            with open(separatedByTaskIFilepath % gid, "w") as f:
                writer = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)
                writer.writerow(header)
                i = 0
                for uuid in surveyData:
                    if int(surveyData[uuid]["gid"]) < gid:
                        if (gid == 0):
                            raise Exception("Rejecting UUID {} from gid {} for data gid {}".format(uuid, gid, surveyData[uuid]["gid"]))
                        continue
                    responsesToConsider = [surveyData[uuid]['humanHelpSequence']['robot interaction sequence'][i] for i in lowestGIDToSharedRobotInteractionSeqI[gid]]
                    responsesHigh = [responceToConsider[1].toNumber() for responceToConsider in responsesToConsider if responceToConsider[0] == "high"]
                    responsesMedium = [responceToConsider[1].toNumber() for responceToConsider in responsesToConsider if responceToConsider[0] == "medium"]
                    responsesFreeTime = [responceToConsider[1].toNumber() for responceToConsider in responsesToConsider if responceToConsider[0] == "free time"]
                    responsesOverall = [responceToConsider[1].toNumber() for responceToConsider in responsesToConsider]

                    row = [uuid]
                    row.append((surveyData[uuid]["gid"]+1)/5.0)
                    row.append(np.mean(responsesHigh))
                    row.append(np.mean(responsesMedium))
                    row.append(np.mean(responsesFreeTime))
                    row.append(np.mean(responsesOverall))
                    row.append(surveyData[uuid]['RoSAS']['Competence'])
                    row.append(surveyData[uuid]['RoSAS']['Curiosity'])
                    row.append(surveyData[uuid]['RoSAS']['Discomfort'])
                    row.append(surveyData[uuid]['RoSAS']['Warmth'])
                    row.append(surveyData[uuid]['NASA-TLX']['Effort'])
                    row.append(surveyData[uuid]['NASA-TLX']['Frustration'])
                    row.append(surveyData[uuid]['NASA-TLX']['Mental Demand'])
                    row.append(surveyData[uuid]['NASA-TLX']['Performance'])
                    row.append(surveyData[uuid]['NASA-TLX']['Physical Demand'])
                    row.append(surveyData[uuid]['NASA-TLX']['Temporal Demand'])
                    row.append(surveyData[uuid]['In your own words, describe what the robot was doing.'].replace("\n", "\\n"))
                    row.append(surveyData[uuid]['In instances when the robot asked for help, why did you help or not help it?'].replace("\n", "\\n"))
                    row.append(surveyData[uuid]['In what scenarios would it be acceptable for a real-world robot to ask people for help?'].replace("\n", "\\n"))
                    row.append(surveyData[uuid]['Did you think the robot was curious? Why or why not?'].replace("\n", "\\n"))
                    row.append(surveyData[uuid]['Is there anything else you would like us to know?'].replace("\n", "\\n"))
                    row.append(surveyData[uuid]['Demography']['Age'])
                    row.append(surveyData[uuid]['Demography']['Gender'])
                    row.append(surveyData[uuid]['Demography']['Navigational Ability'])
                    row.append(surveyData[uuid]['Demography']['Prosociality'])
                    row.append(surveyData[uuid]['Demography']['Video Game Experience'])
                    row.append(surveyData[uuid]['Demography']['Survey Duration'] if 'Survey Duration' in surveyData[uuid]['Demography'] else "")
                    row.append(surveyData[uuid]['Demography']['Slowness'])
                    row.append(surveyData[uuid]['RoSAS Raw']['Reliable'])
                    row.append(surveyData[uuid]['RoSAS Raw']['Competent'])
                    row.append(surveyData[uuid]['RoSAS Raw']['Knowledgeable'])
                    row.append(surveyData[uuid]['RoSAS Raw']['Interactive'])
                    row.append(surveyData[uuid]['RoSAS Raw']['Responsive'])
                    row.append(surveyData[uuid]['RoSAS Raw']['Capable'])
                    row.append(surveyData[uuid]['RoSAS Raw']['Organic'])
                    row.append(surveyData[uuid]['RoSAS Raw']['Sociable'])
                    row.append(surveyData[uuid]['RoSAS Raw']['Emotional'])
                    row.append(surveyData[uuid]['RoSAS Raw']['Compassionate'])
                    row.append(surveyData[uuid]['RoSAS Raw']['Happy'])
                    row.append(surveyData[uuid]['RoSAS Raw']['Feeling'])
                    row.append(surveyData[uuid]['RoSAS Raw']['Awkward'])
                    row.append(surveyData[uuid]['RoSAS Raw']['Scary'])
                    row.append(surveyData[uuid]['RoSAS Raw']['Strange'])
                    row.append(surveyData[uuid]['RoSAS Raw']['Awful'])
                    row.append(surveyData[uuid]['RoSAS Raw']['Dangerous'])
                    row.append(surveyData[uuid]['RoSAS Raw']['Aggressive'])
                    row.append(surveyData[uuid]['RoSAS Raw']['Investigative'])
                    row.append(surveyData[uuid]['RoSAS Raw']['Inquisitive'])
                    row.append(surveyData[uuid]['RoSAS Raw']['Curious'])
                    row.append(surveyData[uuid]['Demography']['tutorialOverallHelping'])
                    for i in range(len(taskDefinitions[0]["robotActions"])):
                        if surveyData[uuid]['humanHelpSequence']['robot interaction sequence'][i] is None:
                            response = None
                        else:
                            _, response = surveyData[uuid]['humanHelpSequence']['robot interaction sequence'][i]
                        if response is None:
                            if taskDefinitions[surveyData[uuid]["gid"]]["robotActions"][i]["robotAction"]["query"] == "walkPast":
                                row.append("ROBOT_NOT_ASK_CONDITION")
                            else:
                                row.append("NEVER_SAW_ROBOT")
                                print("Response none on not walkPast, uuid {}, i {}".format(uuid, i))
                        else:
                            row.append(response.name)

                    writer.writerow(row)
                    i += 1

        numericHeader = ["Busyness", "Frequency", "Prosociality", "Willingness To Help"]
        with open(numericFilepath, "w") as f:
            writer = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)
            writer.writerow(numericHeader)
            i = 0
            for uuid in surveyData:
                for busyness in surveyData[uuid]['helpGivingData']:
                    if busyness == "overall" or busyness == "robot interaction sequence": continue
                    # print("saving numeric CSV UUID {} busyness {} surveyData[uuid]['helpGivingData'] {}".format(uuid, busyness, surveyData[uuid]['helpGivingData']))
                    row = [
                        busyness,
                        (surveyData[uuid]["gid"]+1)/5.0, float(surveyData[uuid]['Demography']['Prosociality']),
                        float(surveyData[uuid]['helpGivingData'][busyness]),
                    ]
                    writer.writerow(row)

def responseCountByType(surveyData):
    responsesToCount = {response : 0 for response in ResponseToHelpQuery}
    for uuid in surveyData:
        responseSequence = surveyData[uuid]["humanHelpSequence"]["overall"]
        for response in responseSequence:
            responsesToCount[response] += 1
    return responsesToCount

def process501GameLogs(surveyData, baseDir, taskDefinitions, tutorialTaskDefinition):
    # Two users started the game at the same time and were assigned UUID 501.
    # The person who finished the tutorial first (at gameStateID 3119) was
    # assigned GID 3. Then the person who finished the tutorial next was assigned
    # GID 1. Therefore, the tutorial file has both the first and second person's
    # tutorial logs. Then, the 3 file has the 3's game logs and the second's tutorial
    # logs. Finally, the 1 file has the latter part of 3's game log and the whole of
    # 1's game log.
    #
    # To fix this, I will let the first person (GID 3) keep 501, and assign the
    # second person (GID 1) to the unused GID 505.

    tutorialLog = loadGameLog(baseDir + "501/0_tutorial_data.json", sort=False)
    firstTutorialLog, firstTutorialLogI = [], set()
    lastGameStateID = None
    for i in range(len(tutorialLog)):
        logEntry = tutorialLog[i]
        if lastGameStateID is not None:
            currGameStateID = int(logEntry["gameStateID"])
            if lastGameStateID-100 > currGameStateID:
                continue
            if int(firstTutorialLog[-1]["gameStateID"]) == 3119:
                break
        firstTutorialLog.append(logEntry)
        firstTutorialLogI.add(i)
        lastGameStateID = int(logEntry["gameStateID"])

    secondTutorialLog = []
    for i in range(len(tutorialLog)):
        if i not in firstTutorialLogI:
            secondTutorialLog.append(tutorialLog[i])

    game3LogRaw = loadGameLog(baseDir + "501/3_data.json".format(uuid), sort=False)
    game3Log = []
    for logEntry in game3LogRaw:
        if int(logEntry["gid"]) == 0:
            secondTutorialLog.append(logEntry)
        elif int(logEntry["gid"]) == 3:
            game3Log.append(logEntry)
        else:
            raise Exception("501/3_data.json logEntry not GID 0 or 3 {}".format(logEntry))

    game1LogRaw = loadGameLog(baseDir + "501/1_data.json".format(uuid), sort=False)
    game1Log = []
    for logEntry in game1LogRaw:
        if int(logEntry["gid"]) == 3:
            game3Log.append(logEntry)
        elif int(logEntry["gid"]) == 1:
            game1Log.append(logEntry)
        else:
            raise Exception("501/1_data.json logEntry not GID 3 or 1 {}".format(logEntry))

    # Sort every log by gameStateID
    firstTutorialLog.sort(key=lambda x : int(x['gameStateID']))
    secondTutorialLog.sort(key=lambda x : int(x['gameStateID']))
    game3Log.sort(key=lambda x : int(x['gameStateID']))
    game1Log.sort(key=lambda x : int(x['gameStateID']))

    # First player -- UUID 501
    tutorialHelpGivingData, tutorialHumanHelpSequence, _ = processGameLog(firstTutorialLog, tutorialTaskDefinition)
    surveyData[501]["Demography"]["tutorialOverallHelping"] = tutorialHelpGivingData["overall"]
    surveyData[501]["helpGivingData"], surveyData[501]["humanHelpSequence"], surveyData[501]["slownessesPerTask"] = processGameLog(game3Log, taskDefinitions[3], afterTaskI=6)
    assert len(surveyData[501]["slownessesPerTask"]) == 28
    surveyData[501]["Demography"]["Slowness"] = 0.0
    for taskI in taskIForSlowness:
        surveyData[501]["Demography"]["Slowness"] += surveyData[501]["slownessesPerTask"][taskI]
    surveyData[501]["Demography"]["Slowness"] /= len(taskIForSlowness)
    # getTimes(surveyData, 501, baseDir) # times aren't reliable
    surveyData[501]["completionCode"] = uuidToCompletionID[str(501)] if str(501) in uuidToCompletionID else None
    surveyData[501]["gid"] = 3

    # Second Player -- UUID 505
    tutorialHelpGivingData, tutorialHumanHelpSequence, _ = processGameLog(secondTutorialLog, tutorialTaskDefinition)
    surveyData[505]["Demography"]["tutorialOverallHelping"] = tutorialHelpGivingData["overall"]
    surveyData[505]["helpGivingData"], surveyData[505]["humanHelpSequence"], surveyData[505]["slownessesPerTask"] = processGameLog(game1Log, taskDefinitions[1], afterTaskI=6)
    assert len(surveyData[505]["slownessesPerTask"]) == 28
    surveyData[505]["Demography"]["Slowness"] = 0.0
    for taskI in taskIForSlowness:
        surveyData[505]["Demography"]["Slowness"] += surveyData[505]["slownessesPerTask"][taskI]
    surveyData[505]["Demography"]["Slowness"] /= len(taskIForSlowness)
    # getTimes(surveyData, 505, baseDir) # times aren't reliable
    surveyData[505]["completionCode"] = uuidToCompletionID[str(505)] if str(505) in uuidToCompletionID else None
    surveyData[505]["gid"] = 1

    return

def mean(l):
    """
    Get the mean of a list
    """
    return sum(l)/len(l)

def makePerResponseDataset(surveyData):
    dataset = [] # list of (uuid, busyness, freqOfAsking, freqOfHelpingAccurately, responseNumber) tuples
    for uuid in surveyData:
        freq = (int(surveyData[uuid]["gid"])+1)/5.0
        numRecentTimesDidNotHelp = 0
        for i in range(len(surveyData[uuid]["humanHelpSequence"]["robot interaction sequence"])):
            if surveyData[uuid]["humanHelpSequence"]["robot interaction sequence"][i] is not None:
                if i >= 5:
                    responseSequence = surveyData[uuid]["humanHelpSequence"]["robot interaction sequence"][i-5:i]
                    freqOfAsking = mean([0 if response is None else 1 for response in responseSequence])
                    if freq != freqOfAsking:
                        raise Exception("freq != freqOfAsking UUID {} i {} freq {} freqOfAsking {}".format(uuid, i, freq, freqOfAsking))
                    freqOfHelpingAccurately = mean([response[1].toNumber() for response in responseSequence if response is not None])
                    busyness, response = surveyData[uuid]["humanHelpSequence"]["robot interaction sequence"][i]
                    responseNumber = response.toNumber()
                    dataset.append((uuid, robotAppearsTaskI[i], busyness, freqOfAsking, freqOfHelpingAccurately, responseNumber, numRecentTimesDidNotHelp))
                if surveyData[uuid]["humanHelpSequence"]["robot interaction sequence"][i][1].toNumber() == 0:
                    numRecentTimesDidNotHelp += 1
                else:
                    numRecentTimesDidNotHelp = 0
    return dataset

def makePerResponseDatasetGraph(perResponseDataset, descriptor):
    freqOfAskingToNumRecentTimesDidNotHelp = {} # freqOfAsking -> [list of numRecentTimesDidNotHelp if responseNumber is 1]
    taskIToFreqOfAskingToWillingnessAndBusyness = {} # taskI -> freqOfAsking -> [[list of responseNumber], busyness]
    dataToGraph = {} # busyness -> freqOfAsking -> freqOfHelpingAccurately -> [list of responseNumber]
    partitionKeys = []
    for _, taskI, busyness, freqOfAsking, freqOfHelpingAccurately, responseNumber, numRecentTimesDidNotHelp in perResponseDataset:
        if busyness not in dataToGraph:
            dataToGraph[busyness] = {}
        if freqOfAsking not in dataToGraph[busyness]:
            dataToGraph[busyness][freqOfAsking] = {}
        if freqOfHelpingAccurately not in dataToGraph[busyness][freqOfAsking]:
            dataToGraph[busyness][freqOfAsking][freqOfHelpingAccurately] = []
        dataToGraph[busyness][freqOfAsking][freqOfHelpingAccurately].append(responseNumber)
        if busyness not in partitionKeys: partitionKeys.append(busyness)
        if freqOfAsking not in freqOfAskingToNumRecentTimesDidNotHelp:
            freqOfAskingToNumRecentTimesDidNotHelp[freqOfAsking] = []
        if responseNumber == 1: freqOfAskingToNumRecentTimesDidNotHelp[freqOfAsking].append(numRecentTimesDidNotHelp)
        if taskI not in taskIToFreqOfAskingToWillingnessAndBusyness:
            taskIToFreqOfAskingToWillingnessAndBusyness[taskI] = {}
        if freqOfAsking not in taskIToFreqOfAskingToWillingnessAndBusyness[taskI]:
            taskIToFreqOfAskingToWillingnessAndBusyness[taskI][freqOfAsking] = [[], busyness]
        taskIToFreqOfAskingToWillingnessAndBusyness[taskI][freqOfAsking][0].append(responseNumber)

    # Overall per person response
    fig = plt.figure(figsize=(16,8))
    axes = fig.subplots(1, len(dataToGraph))
    fig.suptitle('Count for Likelihood of Helping Based on Past Behavior')

    for i in range(len(axes)):
        partitionKey = partitionKeys[i]

        xs, ys, cs = [], [], []
        for x in dataToGraph[partitionKey]:
            for y in dataToGraph[partitionKey][x]:
                xs.append(x)
                ys.append(y)
                cs.append(mean(dataToGraph[partitionKey][x][y]))

        if partitionKey == "high":
            # add a fake datapoint to get the complete colorbar range
            xs.append(-1)
            ys.append(-1)
            cs.append(1.0)

        scatterplot = axes[i].scatter(xs, ys, c=cs)
        axes[i].set_xlim([0.1,1.1])
        axes[i].set_ylim([-0.1,1.1])
        # try:
        #     fig.clim(0.0, 1.0)
        # except Exception as e:
        #     print(e)
        #     traceback.print_exc()
        fig.colorbar(scatterplot, cmap=cm.cool, ax=axes[i])
        axes[i].set_title("Busyness: %s" % (partitionKey))
        axes[i].set_xlabel("Past Frequency of Asking for Help")
        axes[i].set_ylabel("Past Frequency of Receiving Accurate Help")
    # plt.show()
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(baseDir + "perPersonResponse{}.png".format(descriptor))
    plt.clf()

    fig = plt.figure(figsize=(16,16))
    ax = fig.add_subplot(111, projection='3d')
    # surfaceX = np.linspace(0,1,10)
    # surfaceY = np.linspace(0,1,10)
    # surfaceX, surfaceY = np.meshgrid(surfaceX, surfaceY)
    # surfaceZ = surfaceY
    # ax.plot_surface(surfaceX, surfaceY, surfaceZ)
    busynessToColor = {"high":[1.0, 0.0, 0.0], "medium":[0.0, 1.0, 0.0], "free time":[0.0, 0.0, 1.0]}
    for busyness in partitionKeys:
        for freqOfAsking in dataToGraph[busyness]: # x
            xs = []
            ys = []
            zs = []
            for freqOfHelping in sorted(list(dataToGraph[busyness][freqOfAsking].keys())): # y
                humanResponseAvg = mean(dataToGraph[busyness][freqOfAsking][freqOfHelping]) # z
                xs.append(freqOfAsking)
                ys.append(freqOfHelping)
                zs.append(humanResponseAvg)
            ax.plot(xs, ys, zs, c=tuple(busynessToColor[busyness]+[freqOfAsking]), label="Busy %s FreqOfAsking %1.1f" % (busyness, freqOfAsking))
    ax.set_xlabel('Frequency of Asking for Help')
    ax.set_ylabel('Frequency of Helping')
    ax.set_zlabel('Likelihood of Helping')
    ax.legend()
    plt.savefig(baseDir + "perPersonResponseComplete{}.png".format(descriptor))
    # plt.show()
    plt.clf()

    fig = plt.figure()#figsize=(16,8))
    ax = fig.add_subplot()
    # surfaceX = np.linspace(0,1,10)
    # surfaceY = np.linspace(0,1,10)
    # surfaceX, surfaceY = np.meshgrid(surfaceX, surfaceY)
    # surfaceZ = surfaceY
    # ax.plot_surface(surfaceX, surfaceY, surfaceZ)
    busynessToColor = {"high":[1.0, 0.0, 0.0], "medium":[0.0, 1.0, 0.0], "free time":[0.0, 0.0, 1.0]}
    for freqOfAsking in dataToGraph["high"]: # x
        humanResponses = {}
        for busyness in partitionKeys:
            for freqOfHelping in sorted(list(dataToGraph[busyness][freqOfAsking].keys())): # y
                if freqOfHelping not in humanResponses:
                    humanResponses[freqOfHelping] = []
                humanResponses[freqOfHelping] += dataToGraph[busyness][freqOfAsking][freqOfHelping]
        xs = sorted(list(dataToGraph[busyness][freqOfAsking].keys()))
        ys = [mean(humanResponses[freqOfHelping]) for freqOfHelping in xs]
        ax.plot(xs, ys, label="FreqOfAsking %1.1f" % (freqOfAsking))
    ax.set_xlabel('Frequency of Helping')
    ax.set_ylabel('Likelihood of Helping')
    ax.set_title('Past Freq of Helping vs. Current Likelihood of Helping, Partitioned by Freq of Asking')
    ax.legend()
    plt.savefig(baseDir + "perPersonResponseByFreqOfAsking{}.png".format(descriptor))
    # plt.show()
    plt.clf()

    # Frequency to numRecentTimesDidNotHelp histograms
    fig = plt.figure(figsize=(16,8))
    axes = fig.subplots(1, 5)
    for gid in range(len(axes)):
        freq = (gid+1.0)/5.0
        numRecentTimesDidNotHelp = freqOfAskingToNumRecentTimesDidNotHelp[freq]
        axes[gid].hist(numRecentTimesDidNotHelp)
        axes[gid].set_ylim([0,200])
        axes[gid].set_title("Freq: %.01f" % (freq))
        axes[gid].set_xlabel("Num Recent Times Did Not Help")
        axes[gid].set_ylabel("Count")
    plt.savefig(baseDir + "perPersonResponsenumRecentTimesDidNotHelp{}.png".format(descriptor))
    # plt.show()
    plt.clf()

    # Make the graph that shows responses as a binary random variable, weighted
    # so that each person has the same influence
    busynessFreqOfAskingToNoYes = {} # busyness -> freqOfAsking -> [# people who responded No, # people who responded Yes]
    for _, _, busyness, freqOfAsking, _, responseNumber, _ in perResponseDataset:
        if busyness not in busynessFreqOfAskingToNoYes:
            busynessFreqOfAskingToNoYes[busyness] = {}
        if freqOfAsking not in busynessFreqOfAskingToNoYes[busyness]:
            busynessFreqOfAskingToNoYes[busyness][freqOfAsking] = [0.0,0.0]
        if responseNumber == 1:
            addI = 1
        else:
            addI = 0
        busynessFreqOfAskingToNoYes[busyness][freqOfAsking][addI] += 1.0/(5*freqOfAsking) # Inversely weighted by the number of times that person got asked

    # Graph the human responses as a Bernoulli RV, inversely weighted for num people, with error bars
    fig = plt.figure(figsize=(16,8))
    axes = fig.subplots(1, len(busynessFreqOfAskingToNoYes))
    fig.suptitle('Human Responses by Busyness and Frequency, Inversely Weighted by Num Requests Per Person')

    # Constant for the Wilson Confidence Interval for Bernoulli random variables
    # https://brainder.org/2012/04/21/confidence-intervals-for-bernoulli-trials/
    alpha = 0.05
    k = scipy.stats.norm.ppf(1-alpha/2)

    busynessOrder = ["free time", "medium", "high"]
    freqOrder = [(gid+1)/5.0 for gid in range(5)]
    for i in range(len(axes)):
        busyness = busynessOrder[i]
        noNum = []
        yesNum = []
        errorBars = [[], []]
        for freqOfAsking in freqOrder:
            n = sum(busynessFreqOfAskingToNoYes[busyness][freqOfAsking])
            noNum.append(busynessFreqOfAskingToNoYes[busyness][freqOfAsking][0]/n)
            yesNum.append(busynessFreqOfAskingToNoYes[busyness][freqOfAsking][1]/n)
            x = busynessFreqOfAskingToNoYes[busyness][freqOfAsking][1]
            p = x/n
            q = 1.0-p
            print("busyness {}, freqOfAsking {}, p {}, q {}, confWidth {}".format(busyness, freqOfAsking, p, q, k*(p*q/n)**0.5))

            # # Wald Confidence Intervals
            # errorBars[0].append(k*(p*q/n)**0.5)
            # errorBars[1].append(k*(p*q/n)**0.5)

            # Wilson Confidence Intervals
            xBar = x + k**2.0/2.0
            nBar = n + k**2.0
            pBar = xBar/nBar
            errorBars[0].append(p-(pBar-(k/nBar)*(n*p*q+k**2.0/4.0)**0.5))
            errorBars[1].append((pBar+(k/nBar)*(n*p*q+k**2.0/4.0)**0.5)-p)
        print("perPersonResponse_numTimesHelped", "k", k, "errorBars", errorBars)
        p1 = axes[i].bar(freqOrder, yesNum, width=0.1, color=[1.0,0.5,0.0])
        axes[i].errorbar(freqOrder, yesNum, yerr=errorBars, color=[0.0,0.0,0.0], ecolor=[0.0,0.0,0.0])
        p2 = axes[i].bar(freqOrder, noNum, width=0.1, bottom=yesNum, color=[0.0,0.5,1.0])
        axes[i].set_title("Busyness: %s" % (busyness))
        axes[i].set_xlabel("Frequency of Asking")
        axes[i].set_ylabel("Proportion")
        axes[i].legend((p1[0], p2[0]), ('Helped Acurately', 'Didn\'t Help Accurately'))
    # plt.show()
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(baseDir + "perPersonResponse_numTimesHelped{}.png".format(descriptor))
    plt.clf()

    # Make the graph with respect to taskI
    fig = plt.figure(figsize=(16,16))
    ax = fig.add_subplot(111, projection='3d')

    for taskI in taskIToFreqOfAskingToWillingnessAndBusyness:
        xs, ys, zs = [], [], []
        for freqOfAsking in freqOrder:
            if freqOfAsking not in taskIToFreqOfAskingToWillingnessAndBusyness[taskI]: continue
            likelihoodOfHelping = np.mean(taskIToFreqOfAskingToWillingnessAndBusyness[taskI][freqOfAsking][0])
            busyness = taskIToFreqOfAskingToWillingnessAndBusyness[taskI][freqOfAsking][1]
            xs.append(taskI)
            ys.append(freqOfAsking)
            zs.append(likelihoodOfHelping)
        ax.plot(xs, ys, zs, c=tuple(busynessToColor[busyness]), marker="o")

    ax.set_xlabel('TaskI')
    ax.set_ylabel('Frequency of Asking')
    ax.set_zlabel('Likelihood of Helping')
    ax.legend()
    plt.savefig(baseDir + "perPersonResponseWithTaskI{}.png".format(descriptor))
    # plt.show()
    plt.clf()

    # Make the graph with respect to taskI
    fig = plt.figure(figsize=(16,16))
    ax = fig.add_subplot()

    for taskI in taskIToFreqOfAskingToWillingnessAndBusyness:
        xs, ys, zs = [], [], []
        for freqOfAsking in freqOrder:
            if freqOfAsking not in taskIToFreqOfAskingToWillingnessAndBusyness[taskI]: continue
            likelihoodOfHelping = np.mean(taskIToFreqOfAskingToWillingnessAndBusyness[taskI][freqOfAsking][0])
            busyness = taskIToFreqOfAskingToWillingnessAndBusyness[taskI][freqOfAsking][1]
            # xs.append(taskI)
            ys.append(freqOfAsking)
            zs.append(likelihoodOfHelping)
        # ax.plot(xs, ys, zs, c=tuple(busynessToColor[busyness]), marker="o")
        ax.plot(ys, zs, c=tuple(busynessToColor[busyness]), marker="o")
    # ax.set_xlabel('TaskI')
    ax.set_xlabel('Frequency of Asking')
    ax.set_ylabel('Likelihood of Helping')
    # ax.legend()
    plt.savefig(baseDir + "perPersonResponse2DWithTaskI{}.png".format(descriptor))
    # plt.show()
    plt.clf()



def writePerResponseCSV(perResponseDataset, filepath, surveyData, aboveGIDFilepath=None):
    print("writePerResponseCSV", filepath)
    header = ["UUID", "TaskI", "Busyness", "Past Frequency of Asking", "Past Frequency of Helping Accurately", "Human Response", "Prosociality", "Slowness", "Busyness Numeric", "Num Recent Times Did Not Help", "Age", "Gender", "Navigational Ability"]
    with open(filepath, "w") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow(header)
        i = 0
        for uuid, taskI, busyness, freqOfAsking, freqOfHelpingAccurately, responseNumber, numRecentTimesDidNotHelp in perResponseDataset:
            row = [uuid, taskI, busyness, freqOfAsking, freqOfHelpingAccurately, responseNumber, surveyData[uuid]["Demography"]["Prosociality"], surveyData[uuid]["Demography"]["Slowness"], busynessNumericRepresentation[busyness], numRecentTimesDidNotHelp, surveyData[uuid]["Demography"]["Age"], surveyData[uuid]["Demography"]["Gender"], surveyData[uuid]["Demography"]["Navigational Ability"]]
            writer.writerow(row)

    # for gid in range(5):
    #     with open(aboveGIDFilepath%gid, "w") as f:
    #         writer = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)
    #         writer.writerow(header)
    #         i = 0
    #         for uuid, taskI, busyness, freqOfAsking, freqOfHelpingAccurately, responseNumber, numRecentTimesDidNotHelp in perResponseDataset:
    #             if freqOfAsking*5.0-1.0 < gid: continue
    #             if taskI not in lowestGIDToSharedTaskI[gid]: continue
    #             row = [uuid, taskI, busyness, freqOfAsking, freqOfHelpingAccurately, responseNumber, surveyData[uuid]["Demography"]["Prosociality"], surveyData[uuid]["Demography"]["Slowness"], busynessNumericRepresentation[busyness], numRecentTimesDidNotHelp, surveyData[uuid]["Demography"]["Age"]]
    #             writer.writerow(row)

def generatePerResponseTrainingTestingData(perResponseDataset, filepath, partitions, surveyData):
    """
    Generates every training/testing set given the number of partitions
    """
    # Check that the num partitions is valid
    uuids = set()
    frequencies = []
    freqToUUIDs = {}
    uuidToI = {}
    for i in range(len(perResponseDataset)):
        data = perResponseDataset[i]
        uuid = data[0]
        freq = data[3]
        uuids.add(uuid)
        if freq not in freqToUUIDs:
            freqToUUIDs[freq] = []
            frequencies.append(freq)
        if uuid not in uuidToI:
            freqToUUIDs[freq].append(uuid)
            uuidToI[uuid] = []
        uuidToI[uuid].append(i)
    if len(uuids) % partitions != 0:
        raise Exception("Num partitions {} does not evenly divide num users {}".format(partitions, len(uuids)))

    # Shuffle the order of users, balanced by frequency
    random.seed(time.time())
    random.shuffle(frequencies)
    usersPerFrequency = None
    for freq in frequencies:
        random.shuffle(freqToUUIDs[freq])
        usersPerFrequency = len(freqToUUIDs[freq])
    print("freqToUUIDs", freqToUUIDs, {freq : len(freqToUUIDs[freq]) for freq in freqToUUIDs}, frequencies)
    finalUUIDOrder = []
    for i in range(usersPerFrequency):
        for freq in frequencies:
            finalUUIDOrder.append(freqToUUIDs[freq][i])

    # Generate the training and test sets
    sizeOfTestSet = len(finalUUIDOrder)//partitions
    partitionI = -1
    for startI in range(0, len(finalUUIDOrder), sizeOfTestSet):
        partitionI += 1
        testSetUUIDs = []
        for i in range(startI, startI+sizeOfTestSet, 1):
            testSetUUIDs.append(finalUUIDOrder[i])
        trainSet, testSet = [], []
        for uuid in uuidToI:
            if uuid in testSetUUIDs:
                for i in uuidToI[uuid]:
                    testSet.append(perResponseDataset[i])
            else:
                for i in uuidToI[uuid]:
                    trainSet.append(perResponseDataset[i])
        # Save the CSVs
        writePerResponseCSV(trainSet, filepath % (partitionI, "train"), surveyData)
        writePerResponseCSV(testSet, filepath % (partitionI, "test"), surveyData)

def copyDataOver(surveyData, baseDir, copyDir):
    for uuid in surveyData:
        shutil.copytree(baseDir+str(uuid), copyDir+str(uuid))

def makeEntrieHistoryDataset(surveyData):
    dataset = [] # list of (uuid, busyness, freq, numTimesAsked, numTimesHelpedAccurately, responseNumber) tuples
    for uuid in surveyData:
        freq = (int(surveyData[uuid]["gid"])+1)/5.0
        numTimesAsked = 0
        numTimesHelpedAccurately = 0
        for i in range(0, len(surveyData[uuid]["humanHelpSequence"]["robot interaction sequence"])):
            if surveyData[uuid]["humanHelpSequence"]["robot interaction sequence"][i] is not None:
                busyness, response = surveyData[uuid]["humanHelpSequence"]["robot interaction sequence"][i]
                responseNumber = response.toNumber()
                dataset.append((uuid, busyness, freq, numTimesAsked, numTimesHelpedAccurately, responseNumber))
                numTimesAsked += 1
                if responseNumber == 1:
                    numTimesHelpedAccurately += 1
    return dataset

def makeEntireHistoryDatasetGraph(entireHistoryDataset, descriptor):
    dataToGraph = {} # busyness -> freq -> numTimesAsked -> numTimesHelped -> [list of humanResponses]
    partitionKeys = []
    for _, busyness, freq, numTimesAsked, numTimesHelped, humanResponses in entireHistoryDataset:
        if busyness not in dataToGraph:
            dataToGraph[busyness] = {}
        if freq not in dataToGraph[busyness]:
            dataToGraph[busyness][freq] = {}
        if numTimesAsked not in dataToGraph[busyness][freq]:
            dataToGraph[busyness][freq][numTimesAsked] = {}
        if numTimesHelped not in dataToGraph[busyness][freq][numTimesAsked]:
            dataToGraph[busyness][freq][numTimesAsked][numTimesHelped] = []
        dataToGraph[busyness][freq][numTimesAsked][numTimesHelped].append(humanResponses)
        if busyness not in partitionKeys: partitionKeys.append(busyness)

    fig = plt.figure(figsize=(16,16))
    ax = fig.add_subplot(111, projection='3d')
    # surfaceX = np.linspace(0,1,10)
    # surfaceY = np.linspace(0,1,10)
    # surfaceX, surfaceY = np.meshgrid(surfaceX, surfaceY)
    # surfaceZ = surfaceY
    # ax.plot_surface(surfaceX, surfaceY, surfaceZ)
    colors = ["b", "r", "g", "m", "k"]
    busynessToColor = {"high":[1.0, 0.0, 0.0], "medium":[0.0, 1.0, 0.0], "free time":[0.0, 0.0, 1.0]}
    i = -1
    for busyness in ["free time"]:#partitionKeys:
        for freq in dataToGraph[busyness]: # x
            i += 1
            xs = []
            ys = []
            zs = []
            for numTimesAsked in dataToGraph[busyness][freq]:
                for numTimesHelped in sorted(list(dataToGraph[busyness][freq][numTimesAsked].keys())): # y
                    humanResponseAvg = mean(dataToGraph[busyness][freq][numTimesAsked][numTimesHelped]) # z
                    xs.append(numTimesAsked)
                    ys.append(numTimesHelped)
                    zs.append(humanResponseAvg)
            ax.plot(xs, ys, zs, c=tuple(busynessToColor[busyness]+[freq]), label="Busy %s Freq %1.1f" % (busyness, freq))
    ax.set_xlabel('Num Times Asked for Help')
    ax.set_ylabel('Num Times Helped')
    ax.set_zlabel('Likelihood of Helping')

    handles, labels = plt.gca().get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    plt.legend(by_label.values(), by_label.keys())
    # ax.legend()

    plt.savefig(baseDir + "entireHistoryResponseComplete{}.png".format(descriptor))
    # plt.show()
    plt.clf()

if __name__ == "__main__":
    numGIDs = 5

    baseDir = "../flask/ec2_outputs/"
    # baseDir = "../flask/finalData/friendsData/"
    # baseDir = "../flask/finalData/pilot3/"

    completionCodesToUUIDFilename = "completionCodesToUUID.json"
    with open(baseDir+completionCodesToUUIDFilename, "rb") as f:
        completionCodes = json.load(f)
    print("completionCodes", completionCodes)
    uuidToCompletionID = {completionCodes[x] : x for x in completionCodes}
    print("uuidToCompletionID", uuidToCompletionID)

    completedGIDsFilename = "completedGIDs.json"
    with open(baseDir+completedGIDsFilename, "r") as f:
        completedGameIDs = json.load(f)
    print("completedGameIDs", completedGameIDs)
    uuidToGID = {}
    for gid in completedGameIDs:
        for uuid in completedGameIDs[gid]:
            uuidToGID[int(uuid)] = int(gid)

    # raise Exception()

    surveyData = processSurveyData(baseDir + "Human Help User Study Survey (Responses) - Form Responses 1.csv")
    taskDefinitions = {}
    for gid in range(numGIDs):
        filepath = "../flask/assets/tasks/{}.json".format(gid)
        taskDefinitions[gid] = loadTaskDefinitionFile(filepath)
    addMinTaskTime(taskDefinitions, "../flask/assets/min_task_time.json")

    print("taskDefinitions")
    pprint.pprint(taskDefinitions)

    tutorialTaskDefinition = loadTaskDefinitionFile("../flask/assets/tasks/tutorial.json")

    uuidsToKeep = []
    # uuidsToKeep = [100, 103, 104, 108, 110, 122] # pilot1
    # uuidsToKeep = [133] # friendsData

    uuidsToKeep += [136, 137, 138, 140, 141, 142, 143, 144, 146, 147, 149, 151, 152, 153, 155, 156, 157, 159, 166, 167, 170, 179] # pilot 2
    uuidsToKeep += [184, 185, 186, 187, 189, 190, 191, 193, 196, 197, 201, 202, 203, 205, 209] # pilot 3 # removed 188,
    uuidsToKeep += [228, 232, 233, 234, 236, 238, 239, 240, 242, 243, 244, 247, 248, 251, 253, 259, 260, 263] # batch 4
    uuidsToKeep += [264, 266, 267, 269, 271, 272] # batch 5
    uuidsToKeep += [279, 276, 277, 278, 280, 281, 283, 284] # batch 6
    uuidsToKeep += [288, 286, 287, 285, 289, 292, 291, 293, 294] # batch 7
    uuidsToKeep += [300, 298, 297, 296, 301, 304, 306] # batch 8
    uuidsToKeep += [310, 312, 317, 315, 318, 321, 324] # batch 9
    uuidsToKeep += [325, 327, 329, 332, 333, 334, 335, 336, 343] # batch 10
    uuidsToKeep += [346, 352, 353, 359, 365, 367, 374, 380] # batch 11
    uuidsToKeep += [403, 406, 418, 412, 411, 416, 417, 386] # batch 12
    uuidsToKeep += [401, 395, 405, 392, 421, 422, 419, 424] # batch 13
    uuidsToKeep += [391, 400, 393, 397, 390, 413, 414, 425] # batch 14
    uuidsToKeep += [444, 429, 462, 467, 473, 487] # batch 15
    uuidsToKeep += [450, 453, 432, 471, 472, 475, 477, 478] # batch 16
    uuidsToKeep += [449, 446, 435, 440, 452, 461, 463, 437, 470] # batch 17
    uuidsToKeep += [439, 448, 442, 455, 457, 466, 469] # batch 18
    uuidsToKeep += [428, 430, 434, 456, 458, 464, 476, 496] # batch 19
    uuidsToKeep += [499, 524, 517, 527, 528, 532, 536, 539, 541] # batch 20
    uuidsToKeep += [508, 506, 512, 526, 507, 519, 522, 537, 538] # batch 21
    uuidsToKeep += [513, 504, 525, 502, 529, 501, 505, 540, 542] # batch 22, with 505 being the second 501
    uuidsToKeep += [515, 511, 503, 500, 520, 518, 533, 535, 545] # batch 23
    uuidsToKeep += [547, 546, 548, 550, 554] # batch 24
    uuidsToKeep += [560, 558, 559, 557] # batch 25
    uuidsToKeep += [567, 572] # batch 26
    uuidsToKeep += [575] # batch 27

    # uuidsToKeep += [501, 505]

    # Remove the UUIDs of people who filled out the survey but are not actual datapoints
    uuidsToDel = []
    for uuid in surveyData:
        if uuid not in uuidsToKeep:
            uuidsToDel.append(uuid)
    for uuid in uuidsToDel:
        del surveyData[uuid]

    if len(uuidsToKeep) != len(surveyData):
        raise Exception("len(uuidsToKeep) = %d, len(surveyData) = %d" % (len(uuidsToKeep), len(surveyData)))

    # For each UUID, get the corresponding GID and gameLog
    hasProcessed501GameLogs = False
    for uuid in surveyData:
        print("UUID", uuid)
        if (uuid == 501 or uuid == 505):
            if not hasProcessed501GameLogs: # process for whichever uuid comes first, 501 or 505
                print("processing UUID 501 game logs separately")
                process501GameLogs(surveyData, baseDir, taskDefinitions, tutorialTaskDefinition)
                hasProcessed501GameLogs = True
            continue
        try:
            gid = uuidToGID[uuid]
        except Exception as err:
            for filename in os.listdir(baseDir + "{}/".format(uuid)):
                if "_data" in filename and "tutorial" not in filename:
                    gid = int(filename[0])

        filename = "{}_data.json".format(gid)
        surveyData[uuid]["gid"] = gid

        tutorialLog = loadGameLog(baseDir + "{}/0_tutorial_data.json".format(uuid))
        tutorialHelpGivingData, tutorialHumanHelpSequence, _ = processGameLog(tutorialLog, tutorialTaskDefinition)

        surveyData[uuid]["Demography"]["tutorialOverallHelping"] = tutorialHelpGivingData["overall"]
        gameLog = loadGameLog(baseDir + "{}/{}".format(uuid, filename))

        surveyData[uuid]["helpGivingData"], surveyData[uuid]["humanHelpSequence"], surveyData[uuid]["slownessesPerTask"] = processGameLog(gameLog, taskDefinitions[gid], afterTaskI=6)
        assert len(surveyData[uuid]["slownessesPerTask"]) == 28
        surveyData[uuid]["Demography"]["Slowness"] = 0.0
        for taskI in taskIForSlowness:
            print("uuid", uuid, "taskI", taskI, surveyData[uuid]["slownessesPerTask"], len(surveyData[uuid]["slownessesPerTask"]))
            surveyData[uuid]["Demography"]["Slowness"] += surveyData[uuid]["slownessesPerTask"][taskI]
        surveyData[uuid]["Demography"]["Slowness"] /= len(taskIForSlowness)
        getTimes(surveyData, uuid, baseDir)
        surveyData[uuid]["completionCode"] = uuidToCompletionID[str(uuid)] if str(uuid) in uuidToCompletionID else None

    pprint.pprint(surveyData)

    # print("responseCountByType", responseCountByType(surveyData))

    # writeCSV(surveyData, taskDefinitions, baseDir+"humanHelpUserStudyDataComplete.csv", baseDir+"humanHelpUserStudyDataCompleteNumeric.csv")
    #
    # makeGraphs(surveyData)

    # # Remove the users who do not meet the inclusion critereon
    # surveyDataNoStraightlining = {}
    # uuidsToDel = []
    # for uuid in surveyData:
    #     if surveyData[uuid]["Demography"]["RoSAS Variance"] >= 0.67:
    #         surveyDataNoStraightlining[uuid] = surveyData[uuid]
    #
    # print("len(surveyDataNoStraightlining)", len(surveyDataNoStraightlining), "len(surveyData)", len(surveyData))
    #
    # makeGraphs(surveyDataNoStraightlining, "_noStraightlining")

    # # Remove the users who do not meet the inclusion critereon
    # surveyDataNoLowSurveyTime = {}
    # uuidsToDel = []
    # for uuid in surveyData:
    #     if "Survey Duration" in surveyData[uuid]["Demography"] and surveyData[uuid]["Demography"]["Survey Duration"] >= 180:
    #         surveyDataNoLowSurveyTime[uuid] = surveyData[uuid]
    #
    # print("len(surveyDataNoLowSurveyTime)", len(surveyDataNoLowSurveyTime), "len(surveyData)", len(surveyData))
    #
    # makeGraphs(surveyDataNoLowSurveyTime, "_noLowSurveyTime")

    # # Remove the users who do not meet the inclusion critereon
    # surveyDataBriefOpenEndedResponses = {}
    # uuidsToDel = []
    # for uuid in surveyData:
    #     if surveyData[uuid]["Demography"]["Open Ended Length"] >= 20:
    #         surveyDataBriefOpenEndedResponses[uuid] = surveyData[uuid]
    #
    # print("len(surveyDataBriefOpenEndedResponses)", len(surveyDataBriefOpenEndedResponses), "len(surveyData)", len(surveyData))
    #
    # makeGraphs(surveyDataBriefOpenEndedResponses, "_briefOpenEndedResponses")

    # Remove the users who do not meet the inclusion critereon
    surveyDataTutorialOnlyHelping = {}
    surveyTutorialNoHelpingAndLowSurveyTime = {}
    uuidsToDel = []
    for uuid in surveyData:
        if surveyData[uuid]["Demography"]["tutorialOverallHelping"] > 0.0:
            surveyDataTutorialOnlyHelping[uuid] = surveyData[uuid]
        elif surveyData[uuid]["Demography"]["Survey Duration"] < 180:
            surveyTutorialNoHelpingAndLowSurveyTime[uuid] = surveyData[uuid]

    print("len(surveyDataTutorialOnlyHelping)", len(surveyDataTutorialOnlyHelping), "len(surveyTutorialNoHelpingAndLowSurveyTime)", len(surveyTutorialNoHelpingAndLowSurveyTime), "len(surveyData)", len(surveyData))
    print("responseCountByType", responseCountByType(surveyDataTutorialOnlyHelping))

    gidListForTutorialOnlyHelping = {str(i) : [] for i in range(5)}
    for uuid in surveyDataTutorialOnlyHelping:
        gid = surveyDataTutorialOnlyHelping[uuid]["gid"]
        gidListForTutorialOnlyHelping[str(gid)].append(str(uuid))

    print("gidListForTutorialOnlyHelping", gidListForTutorialOnlyHelping, repr(gidListForTutorialOnlyHelping))

    writeCSV(surveyDataTutorialOnlyHelping, taskDefinitions, baseDir+"humanHelpUserStudyDataWithExclusion.csv", baseDir+"humanHelpUserStudyDataWithExclusionNumeric.csv", baseDir+"humanHelpUserStudyDataWithExclusion%d.csv")

    makeGraphs(surveyDataTutorialOnlyHelping, "_tutorialOnlyHelping")

    # Make the per response dataset
    perResponseDataset = makePerResponseDataset(surveyDataTutorialOnlyHelping)
    # print("perResponseDataset")
    # pprint.pprint(perResponseDataset)
    makePerResponseDatasetGraph(perResponseDataset, "_tutorialOnlyHelping")
    writePerResponseCSV(perResponseDataset, baseDir+"humanHelpUserStudyPerResponseData.csv", surveyDataTutorialOnlyHelping, baseDir+"humanHelpUserStudyPerResponseData%d.csv")
    generatePerResponseTrainingTestingData(perResponseDataset, baseDir+"processedData/80-20/%d_%s.csv", partitions=5, surveyData=surveyData) # 80-20 split
    generatePerResponseTrainingTestingData(perResponseDataset, baseDir+"processedData/hold-one-out/%d_%s.csv", partitions=140, surveyData=surveyData)

    # Make the entire history dataset
    entireHistoryDataset = makeEntrieHistoryDataset(surveyDataTutorialOnlyHelping)
    makeEntireHistoryDatasetGraph(entireHistoryDataset, "_tutorialOnlyHelping")

    # surveyDataOnlyZeros = {}
    # surveyDataNoZeros = {}
    # surveyDataOnlyZeroesAndTutorialNoHelping = {}
    # surveyDataOnlyZeroesAndTooBriefSurvey = {}
    # surveyDataOnlyZeroesAndTooBriefSurveyAndTutorialNoHelping = {}
    # for uuid in surveyData:
    #     high = surveyData[uuid]["helpGivingData"]["high"]
    #     medium = surveyData[uuid]["helpGivingData"]["medium"]
    #     freeTime = surveyData[uuid]["helpGivingData"]["free time"]
    #     if not (high == 0.0 and medium == 0.0 and freeTime == 0.0):
    #         surveyDataNoZeros[uuid] = surveyData[uuid]
    #     else:
    #         surveyDataOnlyZeros[uuid] = surveyData[uuid]
    #         if surveyData[uuid]["Demography"]["tutorialOverallHelping"] == 0.0:
    #             surveyDataOnlyZeroesAndTutorialNoHelping[uuid] = surveyData[uuid]
    #             if surveyData[uuid]["Demography"]["Survey Duration"] < 180:
    #                 surveyDataOnlyZeroesAndTooBriefSurveyAndTutorialNoHelping[uuid] = surveyData[uuid]
    #         if surveyData[uuid]["Demography"]["Survey Duration"] < 180:
    #             surveyDataOnlyZeroesAndTooBriefSurvey[uuid] = surveyData[uuid]
    #
    # print("len(surveyDataNoZeros)", len(surveyDataNoZeros), "len(surveyDataOnlyZeroesAndTutorialNoHelping)", len(surveyDataOnlyZeroesAndTutorialNoHelping), "len(surveyDataOnlyZeroesAndTooBriefSurvey)", len(surveyDataOnlyZeroesAndTooBriefSurvey), "len(surveyDataOnlyZeroesAndTooBriefSurveyAndTutorialNoHelping)", len(surveyDataOnlyZeroesAndTooBriefSurveyAndTutorialNoHelping), "len(surveyData)", len(surveyData))
    #
    # makeGraphs(surveyDataNoZeros, "_noZeros")

    # print("surveyDataOnlyZeros")
    # pprint.pprint(surveyDataOnlyZeros)

    # # Remove the users that never help the robot
    # surveyDataTutorialOnlyHelpingAndNoZeros = {}
    # uuidsToDel = []
    # for uuid in surveyDataTutorialOnlyHelping:
    #     if surveyDataTutorialOnlyHelping[uuid]["helpGivingData"]["overall"] > 0.0:
    #         surveyDataTutorialOnlyHelpingAndNoZeros[uuid] = surveyDataTutorialOnlyHelping[uuid]
    #
    # print("len(surveyDataTutorialOnlyHelpingAndNoZeros)", len(surveyDataTutorialOnlyHelpingAndNoZeros), "len(surveyDataTutorialOnlyHelping)", len(surveyDataTutorialOnlyHelping), "len(surveyData)", len(surveyData))
    # print("responseCountByType", responseCountByType(surveyDataTutorialOnlyHelpingAndNoZeros))
    #
    # writeCSV(surveyDataTutorialOnlyHelpingAndNoZeros, taskDefinitions, baseDir+"humanHelpUserStudyDataWithExclusionNoZeros.csv", baseDir+"humanHelpUserStudyDataWithExclusionNoZerosNumeric.csv", baseDir+"humanHelpUserStudyDataWithExclusionNoZeros%d.csv")
    #
    # makeGraphs(surveyDataTutorialOnlyHelpingAndNoZeros, "_tutorialOnlyHelpingNoZeros")
    #
    # # Make the per response dataset
    # perResponseDataset = makePerResponseDataset(surveyDataTutorialOnlyHelpingAndNoZeros)
    # # print("perResponseDataset")
    # # pprint.pprint(perResponseDataset)
    # makePerResponseDatasetGraph(perResponseDataset, "_tutorialOnlyHelpingNoZeros")
    # writePerResponseCSV(perResponseDataset, baseDir+"humanHelpUserStudyPerResponseDataNoZeros.csv", surveyDataTutorialOnlyHelpingAndNoZeros, baseDir+"humanHelpUserStudyPerResponseDataNoZeros%d.csv")
    #
    # # Make the entire history dataset
    # entireHistoryDataset = makeEntrieHistoryDataset(surveyDataTutorialOnlyHelpingAndNoZeros)
    # makeEntireHistoryDatasetGraph(entireHistoryDataset, "_tutorialOnlyHelpingNoZeros")
    #
    # # print("Copying data over to the final dataset folder")
    # # copyDataOver(surveyDataTutorialOnlyHelping, baseDir, copyDir="../flask/finalData/finalDataset/")
