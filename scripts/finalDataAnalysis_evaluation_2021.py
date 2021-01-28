import csv, pprint, os, json, pickle
import matplotlib as mpl
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

import pandas as pd
import seaborn as sns
sns.set(style="darkgrid", font="Palatino")
# mpl.rcParams['text.color'] = 'white'
# sns.set(style="whitegrid")
# sns.set_style("white")
# sns.set(style="whitegrid",font_scale=2)
import ptitprince as pt

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

def loadPolicyLog(filepath):
    """
    Input:
      - a filepath that points to a log file

    Output:
      - a list of policy logs as dictionaries, ordered by time
    """
    policyLog = []
    with open(filepath, "r") as f:
        for i, line in enumerate(f):
            # print("Row", i, line)
            if len(line.strip()) == 0:
                break
            logEntry = json.loads(line)
            policyLog.append(logEntry)
    return policyLog

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
    humanHelpSequence = {"overall":[], "robot interaction sequence":[None for i in range(len(taskDefinition["robotActions"]))]}
    didSayYesInRecentPast = False

    print("UUID %s, GID %s" % (gameLog[0]["uuid"], gameLog[0]["gid"]))
    # print("humanHelpSequence", humanHelpSequence)
    # print("taskDefinition", taskDefinition)

    dtimeAtBeginningOfTask = None
    breakTimeDuringTask = 0.0 # Time the user spent away from the tab
    breakTimeThreshold = 30000 # if consecutive dtimes jump by more than this, view it as a break. To account for the 10 sec pressing space
    hasPressedSpaceForThisTaskI = False
    hasScoreDecreasedForThisTaskI = False
    humanDidArriveOnTime = []
    userTookBreak = False

    slownessesPerTask = []
    gidFirstEntry = int(gameLog[0]["gid"])

    for logEntry in gameLog:
        if int(logEntry["gid"]) != gidFirstEntry:
            print("ERROR, multiple GIDs %d and %d in game log, ignoring %d" % (int(logEntry["gid"]), gidFirstEntry, int(logEntry["gid"])))
            continue
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
            userTookBreak = True

        if "taskI" in logEntry["player"]:
            playerTaskI = int(logEntry["player"]["taskI"])
        else:
            if (int(previousLogEntry["player"]["currentState"]) == PlayerState.DISTRACTION_TASK.value and
                int(logEntry["player"]["currentState"]) == PlayerState.NAVIGATION_TASK.value):
                playerTaskI += 1
                isRobotHelpQueryActive = False
                print("taskI changed", playerTaskI, logEntry["dtime"])

        if playerTaskI == int(previousLogEntry["player"]["taskI"]):
            if int(logEntry["player"]["score"]) < int(previousLogEntry["player"]["score"]):
                hasScoreDecreasedForThisTaskI = True
        else:
            humanDidArriveOnTime.append(not hasScoreDecreasedForThisTaskI)
            hasScoreDecreasedForThisTaskI = False

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
            (didHumanSayStopFollowing and previousRobotState == RobotState.APPROACH_HUMAN.value and currentRobotState == RobotState.GO_TOWARDS_GOAL.value)))):# or  # Bug where the robot goes briefly into approach human for a few steps before walk past -- should be fixed
            # didRobotAppear and previousRobotState == RobotState.APPROACH_HUMAN.value and currentRobotState == RobotState.WALK_PAST_HUMAN.value):
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
                # humanHelpSequence[busyness].append(response)
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

    score = gameLog[-1]["player"]["score"]

    print("humanHelpSequence", humanHelpSequence)

    return {descriptor : getAverageHelpRate(humanHelpSequence[descriptor]) for descriptor in humanHelpSequence}, humanHelpSequence, slownessesPerTask, score, humanDidArriveOnTime, userTookBreak

def processPolicyLog(policyLog):
    """
    Returns: 1) a dictionary of our 4 metrics for this user; 2) The raw b, a, o, r
    data, where b is a list, a is a string, r is a float, and o is a dict; and
    3) a list of the variances of the random effect belief, length num_asks + 1

    The metrics are:
        1) cumulative reward
        2) num correct rooms
        3) num asking
        4) num help received
        5) num help rejected
    """
    rawData = []
    randomEffectsVariances = []
    askingHelpingByBusyness = {i : {"asking":[], "helping":[], "correctRooms":[]} for i in range(1,7)}
    lastAction = None
    cumulativeReward = 0.0
    numCorrectRooms = 0
    numAsks = 0
    numHelps = 0
    numHelpsRejected = 0
    episodeLength = 0
    lastBusyness = None # although the first is always free time, I shouldn't include it because the policy doesn't get to observe the busyness before acting
    askData = []
    for logEntry in policyLog:
        if logEntry["type"] == "action":
            if len(rawData) == 0 or type(rawData[-1]) != list:
                raise Exception("action doesn't come after a belief", logEntry, rawData)
            if logEntry["data"]["action"] == "ask":
                numAsks += 1
                if lastBusyness is not None:
                    askingHelpingByBusyness[lastBusyness]["asking"].append(1)
            else:
                if lastBusyness is not None:
                    askingHelpingByBusyness[lastBusyness]["asking"].append(0)
                # if episodeLength == 18:
                #     # This is a problem for the first few people, when I didn't return the last observation to the server
                #     raise Exception("Asked at the last timestep", rawData)
            lastAction = logEntry["data"]["action"]
            rawData.append(lastAction)
        elif logEntry["type"] == "received_observation":
            episodeLength += 1
            if len(rawData) == 0 or type(rawData[-1]) != str:
                raise Exception("observation doesn't come after an action", logEntry, rawData)
            if logEntry["data"]["obs"]["robot_room_obs"] in ["obs_human_helped", "obs_correct_room"]:
                numCorrectRooms += 1
                if lastBusyness is not None:
                    askingHelpingByBusyness[lastBusyness]["correctRooms"].append(1)
                if logEntry["data"]["obs"]["robot_room_obs"] == "obs_human_helped":
                    numHelps += 1
                    if lastBusyness is not None:
                        askingHelpingByBusyness[lastBusyness]["helping"].append(1)
                else:
                    if lastBusyness is not None:
                        askingHelpingByBusyness[lastBusyness]["helping"].append(0)
            else:
                if lastBusyness is not None:
                    askingHelpingByBusyness[lastBusyness]["helping"].append(0)
                    askingHelpingByBusyness[lastBusyness]["correctRooms"].append(0)
            if lastAction == "ask" and logEntry["data"]["obs"]["robot_room_obs"] != "obs_human_helped":
                numHelpsRejected += 1
            if lastAction == "ask":
                askData.append((int(1 if lastBusyness is None else lastBusyness), sum([1 if logEntry["data"]["obs"]["robot_did_ask_obs"][i] else 0 for i in range(5)])/5.0, 1 if logEntry["data"]["obs"]["robot_room_obs"] == "obs_human_helped" else 0))
            lastBusyness = logEntry["data"]["obs"]["human_busyness_obs"]
            rawData.append(logEntry["data"]["obs"])
        elif logEntry["type"] == "reward":
            if len(rawData) == 0 or type(rawData[-1]) != dict:
                raise Exception("reward doesn't come after an observation", logEntry, rawData)
            cumulativeReward += logEntry["data"]["reward"]
            rawData.append(logEntry["data"]["reward"])
            if episodeLength == 20: # end of episode
                break
        elif logEntry["type"] == "belief":
            randomEffectProbs = logEntry["data"]["human_random_effect_distribution"]["probs"]
            if len(randomEffectsVariances) == 0 or lastAction == "ask":
                randomEffects = logEntry["data"]["human_random_effect_distribution"]["vals"]
                meanRandomEffect = sum([randomEffects[i]*randomEffectProbs[i] for i in range(len(randomEffects))])
                variance = sum([randomEffectProbs[i]*(randomEffects[i]-meanRandomEffect)**2.0 for i in range(len(randomEffects))])
                randomEffectsVariances.append(variance)
            if len(rawData) > 0 and type(rawData[-1]) != float:
                raise Exception("belief doesn't come after a reward", logEntry, rawData)
            rawData.append(randomEffectProbs)

    # if episodeLength == 19:
    #     # The last action must be walk_past, else it would have raised an exception before
    #     if random.random() < 1.0/31: # correct room
    #         old_obs = rawData[-4]
    #         new_obs = {
    #             "human_busyness_obs" : old_obs["human_busyness_obs"],
    #             "robot_did_ask_obs" : [old_obs["human_busyness_obs"][i] for i in range(1,len(old_obs["human_busyness_obs"]))]+[False],
    #             "robot_room_obs":"obs_correct_room",
    #         }
    #         episodeLength += 1
    #         numCorrectRooms += 1
    #         rawData.append(new_obs)
    #
    #         reward = 1.0
    #         cumulativeReward += reward
    #         rawData.append(reward)
    #     else:
    #         old_obs = rawData[-4]
    #         new_obs = {
    #             "human_busyness_obs" : old_obs["human_busyness_obs"],
    #             "robot_did_ask_obs" : [old_obs["human_busyness_obs"][i] for i in range(1,len(old_obs["human_busyness_obs"]))]+[False],
    #             "robot_room_obs":"obs_wrong_room",
    #         }
    #         episodeLength += 1
    #         rawData.append(new_obs)
    #
    #         reward = 0.0
    #         cumulativeReward += reward
    #         rawData.append(reward)
    # else:
    if episodeLength != 20:
        raise Exception("episodeLength != 20", episodeLength, rawData)

    metricsRetval = {
        "cumulativeReward" : cumulativeReward,
        "numCorrectRooms" : numCorrectRooms,
        "numAsking" : numAsks,
        "numHelping" : numHelps,
        "numHelpingRejected" : numHelpsRejected,
    }

    return metricsRetval, rawData, randomEffectsVariances, askingHelpingByBusyness, askData


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
    attentionCheckCols = {
        "Somewhat disagree": 29,
        "Strongly agree": 30,
        "Definitely Robot #1 (Orange)": 44,
        "Definitely Robot #2 (Purple)": 45,
    }
    robotComparisonCols = {
        "Which robot asked for help more times?": 31,
        "Which robot asked for help at more appropriate times?": 32,
        "Which robot respected your time?": 33,
        "Which robot did you prefer interacting with?": 34,
        "Which robot would you be more willing to help?": 35,
        "Which robot was more annoying?": 36,
        "Which robot was more likeable?": 37,
        "Which robot was more competent?": 38,
        "Which robot was more stubborn?": 39,
        "Which robot was more curious?": 40,
        "Which robot was more polite?": 41,
        "Which robot inconvenienced you more?": 42,
        "Which robot would you be more willing to help in the future?": 43,
        "Which robot was better at adapting its behavior to you as an individual?": 46,
        "Which robot was better at adapting its behavior to the situation(s) you were in?": 47,
        "Which robot did you help more?": 48,
        "Which robot did you not help more (e.g. saying \"Can't Help\" or ignoring it)?": 49,
    }

    openEndedCols = {
        "In instances when the robot asked for help, why did you help or not help it?" : 50,
        "What differences were there between Robot #1 (Orange) and Robot #2 (Purple)?" : 51,
        "What do you think this study was about?" : 52,
        "Are there any other thoughts you’d like to share with us? If so, please add them here." : 53,
    }
    demographicCols = {
        "Video Game Experience" : 54,
        "Age" : 55,
        "Gender" : 56,
    }
    # Likert Scale Mappings
    likertQuestionsMapping = {
        "Strongly agree" : 2,
        "Somewhat agree" : 1,
        "Neither agree nor disagree" : 0,
        "Somewhat disagree" : -1,
        "Strongly disagree" : -2,
    }
    robotComparisonMapping = {
        "Definitely Robot #1 (Orange)" : -2,
        "Somewhat Robot #1 (Orange)" : -1,
        "Somewhat Robot #2 (Purple)" : 1,
        "Definitely Robot #2 (Purple)" : 2,
    }

    processedData = {}

    for surveyI in range(1,3):
        with open(filepath%surveyI, "r") as f:
            reader = csv.reader(f)
            rowI = 0 # If the header row is 1
            header = None
            for row in reader:
                rowI += 1
                if header is None:
                    header = row
                    continue
                # if "9/11/2020 22:21:17" in row[timeCol]:
                #     row[uuidCol] = 599
                surveyCompletionTime = datetime.datetime.strptime(row[timeCol], "%m/%d/%Y %H:%M:%S").timestamp()
                uuid = int(row[uuidCol])
                # if uuid == 1228:
                #     continue
                if uuid in processedData and "Survey%d"%surveyI in processedData[uuid]:
                    raise Exception("ERROR: UUID %d has multiple rows rowI %d" % (uuid, rowI))
                elif uuid not in processedData:
                    processedData[uuid] = {}
                processedData[uuid]["Survey%d"%surveyI] = {
                    "surveyCompletionTime" : surveyCompletionTime,
                    "NASA-TLX" : {},
                    "RoSAS" : {},
                    "RoSAS Raw" : {},
                    "Attention Check": {},
                }
                for nasaTLXHeading in nasaTLXCols:
                    processedData[uuid]["Survey%d"%surveyI]["NASA-TLX"][nasaTLXHeading] = int(row[nasaTLXCols[nasaTLXHeading]])
                for rosasHeadingRaw, col in rosasRawCols.items():
                    processedData[uuid]["Survey%d"%surveyI]["RoSAS Raw"][rosasHeadingRaw] = likertQuestionsMapping[row[col]]
                for rosasHeading in rosasCols:
                    total, num = 0, 0
                    for col in rosasCols[rosasHeading]:
                        total += likertQuestionsMapping[row[col]]
                        num += 1
                    processedData[uuid]["Survey%d"%surveyI]["RoSAS"][rosasHeading] = total/num
                numCorrectAttentionChecks, numTotalAttentionChecks = 0, 0
                for attentionCheckAnswer, col in attentionCheckCols.items():
                    if col < len(row):
                        processedData[uuid]["Survey%d"%surveyI]["Attention Check"][attentionCheckAnswer] = row[col]
                        numCorrectAttentionChecks += (1 if row[col] == attentionCheckAnswer else 0)
                        numTotalAttentionChecks += 1
                    processedData[uuid]["Survey%d"%surveyI]["Attention Check Total"] = numCorrectAttentionChecks/numTotalAttentionChecks
                if surveyI == 2:
                    processedData[uuid]["Survey%d"%surveyI]["Robot Comparison"] = {}
                    for robotComparisonQ, col in robotComparisonCols.items():
                        processedData[uuid]["Survey%d"%surveyI]["Robot Comparison"][robotComparisonQ] = robotComparisonMapping[row[col]]
                    for openEndedQ, openEndedCol in openEndedCols.items():
                        processedData[uuid]["Survey%d"%surveyI][openEndedQ] = row[openEndedCol]
                    processedData[uuid]["Demography"] = {}
                    for demographicHeading, demographicCol in demographicCols.items():
                        try:
                            val = int(row[demographicCol])
                        except:
                            val = row[demographicCol]
                        processedData[uuid]["Demography"][demographicHeading] = val

    return processedData

def getTimes(surveyData, uuid, baseDir):
    for filename in ["startTime.txt", "tutorialTime.txt", "gameTime_a.txt", "gameTime_b.txt", "surveyTime_a.txt", "surveyTime_b.txt", "endTime.txt"]:
        try:
            with open(baseDir+"{}/".format(uuid)+filename, "r") as f:
                timeFloat = float(f.read().strip())
                surveyData[uuid][filename[:-4]] = timeFloat
        except Exception as e:
            print(e)
            print(traceback.print_exc())
    survey1ElapsedSecs = surveyData[uuid]["Survey1"]["surveyCompletionTime"]-surveyData[uuid]["surveyTime_a"]
    survey2ElapsedSecs = surveyData[uuid]["Survey2"]["surveyCompletionTime"]-surveyData[uuid]["surveyTime_b"]
    surveyData[uuid]["Demography"]["Survey1 Duration"] = survey1ElapsedSecs
    surveyData[uuid]["Demography"]["Survey2 Duration"] = survey2ElapsedSecs
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

def makePolicyGraphs(surveyData, descriptor=""):
    gid_to_policy_descriptor = ["Hybrid", "Contextual", "Individual"]

    metricToYLabel = {
        "cumulativeReward" : "Cumulative Reward",
        "numCorrectRooms" : "Num Correct Rooms",
        "numAsking" : "Num Asks",
        "numHelping" : "Num Help",
        "numHelpingRejected" : "Num Refused Help",
    }

    metricToTitle = {
        "cumulativeReward" : "Cumulative Reward Across Policies",
        "numCorrectRooms" : "Num Correct Rooms Across Policies",
        "numAsking" : "Num Asks Across Policies",
        "numHelping" : "Num Help Across Policies",
        "numHelpingRejected" : "Num Refused Help Across Policies",
    }

    metricsToData = {
        "cumulativeReward" : [],
        "numCorrectRooms" : [],
        "numAsking" : [],
        "numHelping" : [],
        "numHelpingRejected" : [],
    }

    metricsToDataPaired = {
        "cumulativeReward" : [],
        "numCorrectRooms" : [],
        "numAsking" : [],
        "numHelping" : [],
        "numHelpingRejected" : [],
    }

    metricsToDataDifference = {
        "cumulativeReward" : [],
        "numCorrectRooms" : [],
        "numAsking" : [],
        "numHelping" : [],
        "numHelpingRejected" : [],
    }

    forcedChoiceQData = []

    rosasData = []
    rosasDifferencesData = []

    rosasRawData = {}
    rosasRawDifferencesData = []

    nasaTLXData = []
    nasaTLXDifferencesData = []

    policy0 = gid_to_policy_descriptor[gidsInComparison[0]]
    policy1 = gid_to_policy_descriptor[gidsInComparison[1]]

    askingData = []
    numAskingHelpingJitter = []
    jitterNoiseStd = 0.5
    gids = []
    for uuid in surveyData:
        firstGID = surveyData[uuid]["firstGID"]
        gids.append(firstGID)

        for metric in metricsToData:
            metricsToData[metric].append([policy0, surveyData[uuid][gidsInComparison[0]]["policyResults"]["metrics"][metric]])
            metricsToData[metric].append([policy1, surveyData[uuid][gidsInComparison[1]]["policyResults"]["metrics"][metric]])

            metricsToDataPaired[metric].append([surveyData[uuid][gidsInComparison[0]]["policyResults"]["metrics"][metric]+(random.random()-0.5)*jitterNoiseStd, surveyData[uuid][gidsInComparison[1]]["policyResults"]["metrics"][metric]+(random.random()-0.5)*jitterNoiseStd])

        for metric in metricsToDataDifference:
            metricsToDataDifference[metric].append([surveyData[uuid][gidsInComparison[0]]["policyResults"]["metrics"][metric] - surveyData[uuid][gidsInComparison[1]]["policyResults"]["metrics"][metric]])

        numAskingHelpingJitter.append([policy0, surveyData[uuid][gidsInComparison[0]]["policyResults"]["metrics"]["numAsking"]+(random.random()-0.5)*jitterNoiseStd, surveyData[uuid][gidsInComparison[0]]["policyResults"]["metrics"]["numHelping"]+(random.random()-0.5)*jitterNoiseStd])
        numAskingHelpingJitter.append([policy1, surveyData[uuid][gidsInComparison[1]]["policyResults"]["metrics"]["numAsking"]+(random.random()-0.5)*jitterNoiseStd, surveyData[uuid][gidsInComparison[1]]["policyResults"]["metrics"]["numHelping"]+(random.random()-0.5)*jitterNoiseStd])

        for busyness in surveyData[uuid][gidsInComparison[0]]["policyResults"]["metricsByBusyness"]:
            type = "asking"
            for gid in gidsInComparison:
                policy = gid_to_policy_descriptor[gid]
                if len(surveyData[uuid][gid]["policyResults"]["metricsByBusyness"][busyness][type]) > 0:
                    p = sum(surveyData[uuid][gid]["policyResults"]["metricsByBusyness"][busyness][type])/len(surveyData[uuid][gid]["policyResults"]["metricsByBusyness"][busyness][type])
                    busynessFloat = (busyness-1)/5.0*0.4
                    askingData.append([policy, busynessFloat, p])

        for forcedChoiceQ in surveyData[uuid][surveyData[uuid]["secondGID"]]['Survey']['Robot Comparison']:
            forcedChoiceQData.append([forcedChoiceQ, surveyData[uuid][surveyData[uuid]["secondGID"]]['Survey']['Robot Comparison'][forcedChoiceQ]])


        for rosasCategory in surveyData[uuid][0]['Survey']['RoSAS']:
            for gid in gidsInComparison:
                policy = gid_to_policy_descriptor[gid]
                rosasData.append([policy+" "+rosasCategory, surveyData[uuid][gid]['Survey']['RoSAS'][rosasCategory]])
            rosasDifferencesData.append([rosasCategory, surveyData[uuid][gidsInComparison[0]]['Survey']['RoSAS'][rosasCategory]-surveyData[uuid][gidsInComparison[1]]['Survey']['RoSAS'][rosasCategory]])

        for rosasRawCategory in surveyData[uuid][0]['Survey']['RoSAS Raw']:
            if rosasRawCategory not in rosasRawData:
                rosasRawData[rosasRawCategory] = []
            for gid in gidsInComparison:
                policy = gid_to_policy_descriptor[gid]
                rosasRawData[rosasRawCategory].append([policy, surveyData[uuid][gid]['Survey']['RoSAS Raw'][rosasRawCategory]])
            rosasRawDifferencesData.append([rosasRawCategory, surveyData[uuid][gidsInComparison[0]]['Survey']['RoSAS Raw'][rosasRawCategory]-surveyData[uuid][gidsInComparison[1]]['Survey']['RoSAS Raw'][rosasRawCategory]])

        for nasaTLXCategory in surveyData[uuid][0]['Survey']['NASA-TLX']:
            for gid in gidsInComparison:
                policy = gid_to_policy_descriptor[gid]
                nasaTLXData.append([policy+" "+nasaTLXCategory, surveyData[uuid][gid]['Survey']['NASA-TLX'][nasaTLXCategory]])
            nasaTLXDifferencesData.append([nasaTLXCategory, surveyData[uuid][gidsInComparison[0]]['Survey']['NASA-TLX'][nasaTLXCategory]-surveyData[uuid][gidsInComparison[1]]['Survey']['NASA-TLX'][nasaTLXCategory]])

    for metric in metricsToData:
        metricsToData[metric].sort(key=lambda x: gid_to_policy_descriptor.index(x[0]))
        metricsToData[metric] = pd.DataFrame(metricsToData[metric], columns = ['Policy', metric])
        metricsToDataPaired[metric] = pd.DataFrame(metricsToDataPaired[metric], columns = [policy0+" "+metric, policy1+" "+metric])
        metricsToDataDifference[metric] = pd.DataFrame(metricsToDataDifference[metric], columns = [policy0+" - "+policy1+" "+metric])
    numAskingHelpingJitter = pd.DataFrame(numAskingHelpingJitter, columns = ['Policy', 'Num Asking', 'Num Helping'])
    askingData = pd.DataFrame(askingData, columns = ['Policy', 'Busyness', 'Proportion'])
    forcedChoiceQData = pd.DataFrame(forcedChoiceQData, columns = ['Question', 'Value'])
    rosasData = pd.DataFrame(rosasData, columns = ['Policy And RoSAS Category', 'Value'])
    rosasDifferencesData = pd.DataFrame(rosasDifferencesData, columns = ['RoSAS Category', policy0+' - '+policy1])
    for rosasRawCategory in rosasRawData:
        rosasRawData[rosasRawCategory] = pd.DataFrame(rosasRawData[rosasRawCategory], columns = ['Policy', 'Value'])
    rosasRawDifferencesData = pd.DataFrame(rosasRawDifferencesData, columns = ['RoSAS Raw Category', policy0+' - '+policy1])
    nasaTLXData = pd.DataFrame(nasaTLXData, columns = ['Policy And NASA-TLX Category', 'Value'])
    nasaTLXDifferencesData = pd.DataFrame(nasaTLXDifferencesData, columns = ['NASA-TLX Category', policy0+' - '+policy1])

    # Generate boxplots for each of the four metrics
    pal = [(77/255,175/255,74/255),(55/255,126/255,184/255),(228/255,26/255,28/255)]#sns.color_palette()#"tab10") # sns.color_palette(n_colors=3) # "colorblind" # "Set2"
    # pal = [pal[9], pal[3], pal[8]]
    sigma = 0.2
    for metric in metricsToData:
        # Metrics By Policy RainCloud
        fig = plt.figure(figsize=(8,8))
        ax = fig.subplots(1, 1)
        fig.suptitle(metricToTitle[metric])
        pt.RainCloud(x = "Policy", y = metric, data = metricsToData[metric], palette = pal, bw = sigma,
                         width_viol = .6, ax = ax, orient = "h", order=gid_to_policy_descriptor)
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.savefig(baseDir + "policy_{}_{}.png".format(metric, descriptor))
        plt.clf()

        # Metrics Difference RainCloud
        fig = plt.figure(figsize=(8,8))
        ax = fig.subplots(1, 1)
        fig.suptitle(metricToTitle[metric])
        pt.RainCloud(y = policy0+" - "+policy1+" "+metric, data = metricsToDataDifference[metric], palette = pal, bw = sigma,
                         width_viol = .6, ax = ax, orient = "h")
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.savefig(baseDir + "policy_difference_{}_{}.png".format(metric, descriptor))
        plt.clf()

        # Metrics Paired Scatterplot
        fig = plt.figure(figsize=(8,8))
        ax = fig.subplots(1, 1)
        fig.suptitle(metricToTitle[metric])
        sns.scatterplot(x = policy0+" "+metric, y = policy1+" "+metric, data = metricsToDataPaired[metric], palette = pal, alpha=1,
                         ax = ax)
        minXYLim = min(ax.get_xlim()[0], ax.get_ylim()[0])
        maxXYLim = max(ax.get_xlim()[1], ax.get_ylim()[1])
        ax.plot([minXYLim,maxXYLim], [minXYLim,maxXYLim], linewidth=2, linestyle='--', alpha=0.5)
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.savefig(baseDir + "policy_paired_{}_{}.png".format(metric, descriptor))
        plt.clf()

    # Num Times Asked Helped Scatterplot
    fig = plt.figure(figsize=(4,4))
    # fig.patch.set_facecolor('k')
    ax = fig.subplots(1, 1)
    fig.suptitle("Num Times Asked / Helped Across Policies")
    sns.scatterplot(x = "Num Asking", y = "Num Helping", data = numAskingHelpingJitter, palette = pal, hue="Policy", style="Policy", style_order=['Contextual', 'Individual', 'Hybrid'], alpha=1,
                     ax = ax, hue_order=gid_to_policy_descriptor)
    handles, labels = ax.get_legend_handles_labels()
    l = ax.legend(handles=handles[0:], labels=labels[0:])#, facecolor='k', edgecolor='darkgrey')
    # for text in l.get_texts():
    #     text.set_color("k")
    ax.set_xlabel('Number of Times the Robot Asked')
    ax.set_ylabel('Number of Times the Human Helped')
    ax.plot([0,20], [0,20], linewidth=2, linestyle='--', alpha=0.5)
    # ax.xaxis.label.set_color('white')
    # ax.yaxis.label.set_color('white')
    # ax.tick_params(axis='x', colors='white')
    # ax.tick_params(axis='y', colors='white')
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(baseDir + "policy_num_asking_helping_jitter_{}.png".format(descriptor))
    plt.clf()

    # Proportion of Times Asked By Busyness
    fig, ax = plt.subplots(1, 1, figsize=(4,4))
    # fig.patch.set_facecolor('k')
    sns.lineplot(data=askingData, x="Busyness", y="Proportion", hue="Policy", ax=ax, palette = pal, hue_order=gid_to_policy_descriptor)
    fig.suptitle("Proportion of Times Asked By Busyness")
    ax.set_xlabel("Human Busyness")
    ax.set_ylabel("Proportion of Times the Robot Asked")
    handles, labels = ax.get_legend_handles_labels()
    l = ax.legend(handles=handles[0:], labels=labels[0:], loc='lower left')#, facecolor='k', edgecolor='darkgrey')
    # for text in l.get_texts():
    #     text.set_color("k")
    # ax.xaxis.label.set_color('white')
    # ax.yaxis.label.set_color('white')
    # ax.tick_params(axis='x', colors='white')
    # ax.tick_params(axis='y', colors='white')
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(baseDir + "policies_pct_asking{}.png".format(descriptor))

    # Forced Choice Qs
    fig = plt.figure(figsize=(16,8))
    ax = fig.subplots(1, 1)
    fig.suptitle("Forced Choice Questions")
    pt.RainCloud(x = "Question", y = "Value", data = forcedChoiceQData, bw = sigma,
                     width_viol = .6, ax = ax, orient = "h")
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(baseDir + "forced_choice_qs_{}.png".format(descriptor))
    plt.clf()

    # RoSAS Data
    fig = plt.figure(figsize=(12,8))
    ax = fig.subplots(1, 1)
    fig.suptitle("RoSAS Results")
    pt.RainCloud(x = "Policy And RoSAS Category", y = "Value", data = rosasData, bw = sigma,
                     width_viol = .6, ax = ax, orient = "h")
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(baseDir + "rosas_data_{}.png".format(descriptor))
    plt.clf()

    # RoSAS Differences Data
    fig = plt.figure(figsize=(12,8))
    ax = fig.subplots(1, 1)
    fig.suptitle("RoSAS Differences")
    pt.RainCloud(x = "RoSAS Category", y = policy0+" - "+policy1, data = rosasDifferencesData, bw = sigma,
                     width_viol = .6, ax = ax, orient = "h")
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(baseDir + "rosas_differences_data_{}.png".format(descriptor))
    plt.clf()

    # RoSAS Raw Data
    for rosasRawCategory in rosasRawData:
        fig = plt.figure(figsize=(12,8))
        ax = fig.subplots(1, 1)
        fig.suptitle("RoSAS Results")
        pt.RainCloud(x = "Policy", y = "Value", data = rosasRawData[rosasRawCategory], bw = sigma,
                         width_viol = .6, ax = ax, orient = "h")
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.savefig(baseDir + "rosas_raw_data+{}_{}.png".format(rosasRawCategory, descriptor))
        plt.clf()

    # RoSAS Raw Differences Data
    fig = plt.figure(figsize=(12,8))
    ax = fig.subplots(1, 1)
    fig.suptitle("RoSAS Differences")
    pt.RainCloud(x = "RoSAS Raw Category", y = policy0+" - "+policy1, data = rosasRawDifferencesData, bw = sigma,
                     width_viol = .6, ax = ax, orient = "h")
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(baseDir + "rosas_raw_differences_data_{}.png".format(descriptor))
    plt.clf()

    # NASA-TLX Data
    fig = plt.figure(figsize=(12,8))
    ax = fig.subplots(1, 1)
    fig.suptitle("NASA-TLX Results")
    pt.RainCloud(x = "Policy And NASA-TLX Category", y = "Value", data = nasaTLXData, bw = sigma,
                     width_viol = .6, ax = ax, orient = "h")
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(baseDir + "nasa_tlx_data_{}.png".format(descriptor))
    plt.clf()

    # NASA-TLX Differences Data
    fig = plt.figure(figsize=(12,8))
    ax = fig.subplots(1, 1)
    fig.suptitle("NASA-TLX Differences")
    pt.RainCloud(x = "NASA-TLX Category", y = policy0+" - "+policy1, data = nasaTLXDifferencesData, bw = sigma,
                     width_viol = .6, ax = ax, orient = "h")
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(baseDir + "nasa_tlx_differences_data_{}.png".format(descriptor))
    plt.clf()

    # GIDs
    fig = plt.figure()
    ax = fig.subplots()
    fig.suptitle('GIDs')
    ax.hist(gids)
    ax.set_xlabel("Game ID")
    ax.set_ylabel("Count")
    plt.savefig(baseDir + "gids_{}.png".format(descriptor))
    plt.clf()

def writeCSV(surveyData, taskDefinitions, filepath):
    gid_to_policy_descriptor = ["Hybrid", "Contextual", "Individual"]
    header = [
        "User ID",
        "First GID",
        "Hybrid Cumulative Reward",
        "Hybrid Num Correct Rooms",
        "Hybrid Num Asking",
        "Hybrid Num Helping",
        "Hybrid Num Helping Rejected",
        "Individual Cumulative Reward",
        "Individual Num Correct Rooms",
        "Individual Num Asking",
        "Individual Num Helping",
        "Individual Num Helping Rejected",

        "Hybrid NASA TLX Mental Demand",
        "Hybrid NASA TLX Physical Demand",
        "Hybrid NASA TLX Temporal Demand",
        "Hybrid NASA TLX Performance",
        "Hybrid NASA TLX Effort",
        "Hybrid NASA TLX Frustration",
        "Individual NASA TLX Mental Demand",
        "Individual NASA TLX Physical Demand",
        "Individual NASA TLX Temporal Demand",
        "Individual NASA TLX Performance",
        "Individual NASA TLX Effort",
        "Individual NASA TLX Frustration",

        "Hybrid RoSAS Competence",
        "Hybrid RoSAS Warmth",
        "Hybrid RoSAS Discomfort",
        "Hybrid RoSAS Curiosity",
        "Individual RoSAS Competence",
        "Individual RoSAS Warmth",
        "Individual RoSAS Discomfort",
        "Individual RoSAS Curiosity",

        "Hybrid RoSAS Raw Reliable",
        "Hybrid RoSAS Raw Competent",
        "Hybrid RoSAS Raw Knowledgeable",
        "Hybrid RoSAS Raw Interactive",
        "Hybrid RoSAS Raw Responsive",
        "Hybrid RoSAS Raw Capable",
        "Hybrid RoSAS Raw Organic",
        "Hybrid RoSAS Raw Sociable",
        "Hybrid RoSAS Raw Emotional",
        "Hybrid RoSAS Raw Compassionate",
        "Hybrid RoSAS Raw Happy",
        "Hybrid RoSAS Raw Feeling",
        "Hybrid RoSAS Raw Awkward",
        "Hybrid RoSAS Raw Scary",
        "Hybrid RoSAS Raw Strange",
        "Hybrid RoSAS Raw Awful",
        "Hybrid RoSAS Raw Dangerous",
        "Hybrid RoSAS Raw Aggressive",
        "Hybrid RoSAS Raw Investigative",
        "Hybrid RoSAS Raw Inquisitive",
        "Hybrid RoSAS Raw Curious",
        "Individual RoSAS Raw Reliable",
        "Individual RoSAS Raw Competent",
        "Individual RoSAS Raw Knowledgeable",
        "Individual RoSAS Raw Interactive",
        "Individual RoSAS Raw Responsive",
        "Individual RoSAS Raw Capable",
        "Individual RoSAS Raw Organic",
        "Individual RoSAS Raw Sociable",
        "Individual RoSAS Raw Emotional",
        "Individual RoSAS Raw Compassionate",
        "Individual RoSAS Raw Happy",
        "Individual RoSAS Raw Feeling",
        "Individual RoSAS Raw Awkward",
        "Individual RoSAS Raw Scary",
        "Individual RoSAS Raw Strange",
        "Individual RoSAS Raw Awful",
        "Individual RoSAS Raw Dangerous",
        "Individual RoSAS Raw Aggressive",
        "Individual RoSAS Raw Investigative",
        "Individual RoSAS Raw Inquisitive",
        "Individual RoSAS Raw Curious",

        "Which robot asked for help more times?",
        "Which robot asked for help at more appropriate times?",
        "Which robot respected your time?",
        "Which robot did you prefer interacting with?",
        "Which robot would you be more willing to help?",
        "Which robot was more annoying?",
        "Which robot was more likeable?",
        "Which robot was more competent?",
        "Which robot was more stubborn?",
        "Which robot was more curious?",
        "Which robot was more polite?",
        "Which robot inconvenienced you more?",
        "Which robot would you be more willing to help in the future?",
        "Which robot was better at adapting its behavior to you as an individual?",
        "Which robot was better at adapting its behavior to the situation(s) you were in?",
        "Which robot did you help more?",
        "Which robot did you not help more (e.g. saying \"Can't Help\" or ignoring it)?",

        "In instances when the robot asked for help, why did you help or not help it?",
        "What differences were there between Robot #1 (Orange) and Robot #2 (Purple)?",
        "What do you think this study was about?",
        "Are there any other thoughts you’d like to share with us? If so, please add them here.",

        "Age",
        "Gender",
        "Video Game Experience",
        "Survey1 Duration",
        "Survey2 Duration",
        "Hybrid Average Busyness",
        "Individual Average Busyness",
        "Hybrid Score",
        "Individual Score",

        "First Attention Check Total",
        "Second Attention Check Total",
    ]
    with open(filepath, "w") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow(header)
        i = 0
        for uuid in surveyData:
            row = [uuid]
            row.append(surveyData[uuid]["firstGID"])

            row.append(surveyData[uuid][0]['policyResults']['metrics']['cumulativeReward'])
            row.append(surveyData[uuid][0]['policyResults']['metrics']['numCorrectRooms'])
            row.append(surveyData[uuid][0]['policyResults']['metrics']['numAsking'])
            row.append(surveyData[uuid][0]['policyResults']['metrics']['numHelping'])
            row.append(surveyData[uuid][0]['policyResults']['metrics']['numHelpingRejected'])
            row.append(surveyData[uuid][2]['policyResults']['metrics']['cumulativeReward'])
            row.append(surveyData[uuid][2]['policyResults']['metrics']['numCorrectRooms'])
            row.append(surveyData[uuid][2]['policyResults']['metrics']['numAsking'])
            row.append(surveyData[uuid][2]['policyResults']['metrics']['numHelping'])
            row.append(surveyData[uuid][2]['policyResults']['metrics']['numHelpingRejected'])

            row.append(surveyData[uuid][0]['Survey']['NASA-TLX']['Mental Demand'])
            row.append(surveyData[uuid][0]['Survey']['NASA-TLX']['Physical Demand'])
            row.append(surveyData[uuid][0]['Survey']['NASA-TLX']['Temporal Demand'])
            row.append(surveyData[uuid][0]['Survey']['NASA-TLX']['Performance'])
            row.append(surveyData[uuid][0]['Survey']['NASA-TLX']['Effort'])
            row.append(surveyData[uuid][0]['Survey']['NASA-TLX']['Frustration'])
            row.append(surveyData[uuid][2]['Survey']['NASA-TLX']['Mental Demand'])
            row.append(surveyData[uuid][2]['Survey']['NASA-TLX']['Physical Demand'])
            row.append(surveyData[uuid][2]['Survey']['NASA-TLX']['Temporal Demand'])
            row.append(surveyData[uuid][2]['Survey']['NASA-TLX']['Performance'])
            row.append(surveyData[uuid][2]['Survey']['NASA-TLX']['Effort'])
            row.append(surveyData[uuid][2]['Survey']['NASA-TLX']['Frustration'])

            row.append(surveyData[uuid][0]['Survey']['RoSAS']['Competence'])
            row.append(surveyData[uuid][0]['Survey']['RoSAS']['Warmth'])
            row.append(surveyData[uuid][0]['Survey']['RoSAS']['Discomfort'])
            row.append(surveyData[uuid][0]['Survey']['RoSAS']['Curiosity'])
            row.append(surveyData[uuid][2]['Survey']['RoSAS']['Competence'])
            row.append(surveyData[uuid][2]['Survey']['RoSAS']['Warmth'])
            row.append(surveyData[uuid][2]['Survey']['RoSAS']['Discomfort'])
            row.append(surveyData[uuid][2]['Survey']['RoSAS']['Curiosity'])

            row.append(surveyData[uuid][0]['Survey']['RoSAS Raw']['Reliable'])
            row.append(surveyData[uuid][0]['Survey']['RoSAS Raw']['Competent'])
            row.append(surveyData[uuid][0]['Survey']['RoSAS Raw']['Knowledgeable'])
            row.append(surveyData[uuid][0]['Survey']['RoSAS Raw']['Interactive'])
            row.append(surveyData[uuid][0]['Survey']['RoSAS Raw']['Responsive'])
            row.append(surveyData[uuid][0]['Survey']['RoSAS Raw']['Capable'])
            row.append(surveyData[uuid][0]['Survey']['RoSAS Raw']['Organic'])
            row.append(surveyData[uuid][0]['Survey']['RoSAS Raw']['Sociable'])
            row.append(surveyData[uuid][0]['Survey']['RoSAS Raw']['Emotional'])
            row.append(surveyData[uuid][0]['Survey']['RoSAS Raw']['Compassionate'])
            row.append(surveyData[uuid][0]['Survey']['RoSAS Raw']['Happy'])
            row.append(surveyData[uuid][0]['Survey']['RoSAS Raw']['Feeling'])
            row.append(surveyData[uuid][0]['Survey']['RoSAS Raw']['Awkward'])
            row.append(surveyData[uuid][0]['Survey']['RoSAS Raw']['Scary'])
            row.append(surveyData[uuid][0]['Survey']['RoSAS Raw']['Strange'])
            row.append(surveyData[uuid][0]['Survey']['RoSAS Raw']['Awful'])
            row.append(surveyData[uuid][0]['Survey']['RoSAS Raw']['Dangerous'])
            row.append(surveyData[uuid][0]['Survey']['RoSAS Raw']['Aggressive'])
            row.append(surveyData[uuid][0]['Survey']['RoSAS Raw']['Investigative'])
            row.append(surveyData[uuid][0]['Survey']['RoSAS Raw']['Inquisitive'])
            row.append(surveyData[uuid][0]['Survey']['RoSAS Raw']['Curious'])
            row.append(surveyData[uuid][2]['Survey']['RoSAS Raw']['Reliable'])
            row.append(surveyData[uuid][2]['Survey']['RoSAS Raw']['Competent'])
            row.append(surveyData[uuid][2]['Survey']['RoSAS Raw']['Knowledgeable'])
            row.append(surveyData[uuid][2]['Survey']['RoSAS Raw']['Interactive'])
            row.append(surveyData[uuid][2]['Survey']['RoSAS Raw']['Responsive'])
            row.append(surveyData[uuid][2]['Survey']['RoSAS Raw']['Capable'])
            row.append(surveyData[uuid][2]['Survey']['RoSAS Raw']['Organic'])
            row.append(surveyData[uuid][2]['Survey']['RoSAS Raw']['Sociable'])
            row.append(surveyData[uuid][2]['Survey']['RoSAS Raw']['Emotional'])
            row.append(surveyData[uuid][2]['Survey']['RoSAS Raw']['Compassionate'])
            row.append(surveyData[uuid][2]['Survey']['RoSAS Raw']['Happy'])
            row.append(surveyData[uuid][2]['Survey']['RoSAS Raw']['Feeling'])
            row.append(surveyData[uuid][2]['Survey']['RoSAS Raw']['Awkward'])
            row.append(surveyData[uuid][2]['Survey']['RoSAS Raw']['Scary'])
            row.append(surveyData[uuid][2]['Survey']['RoSAS Raw']['Strange'])
            row.append(surveyData[uuid][2]['Survey']['RoSAS Raw']['Awful'])
            row.append(surveyData[uuid][2]['Survey']['RoSAS Raw']['Dangerous'])
            row.append(surveyData[uuid][2]['Survey']['RoSAS Raw']['Aggressive'])
            row.append(surveyData[uuid][2]['Survey']['RoSAS Raw']['Investigative'])
            row.append(surveyData[uuid][2]['Survey']['RoSAS Raw']['Inquisitive'])
            row.append(surveyData[uuid][2]['Survey']['RoSAS Raw']['Curious'])

            row.append(surveyData[uuid][surveyData[uuid]["secondGID"]]['Survey']['Robot Comparison']['Which robot asked for help more times?'])
            row.append(surveyData[uuid][surveyData[uuid]["secondGID"]]['Survey']['Robot Comparison']['Which robot asked for help at more appropriate times?'])
            row.append(surveyData[uuid][surveyData[uuid]["secondGID"]]['Survey']['Robot Comparison']['Which robot respected your time?'])
            row.append(surveyData[uuid][surveyData[uuid]["secondGID"]]['Survey']['Robot Comparison']['Which robot did you prefer interacting with?'])
            row.append(surveyData[uuid][surveyData[uuid]["secondGID"]]['Survey']['Robot Comparison']['Which robot would you be more willing to help?'])
            row.append(surveyData[uuid][surveyData[uuid]["secondGID"]]['Survey']['Robot Comparison']['Which robot was more annoying?'])
            row.append(surveyData[uuid][surveyData[uuid]["secondGID"]]['Survey']['Robot Comparison']['Which robot was more likeable?'])
            row.append(surveyData[uuid][surveyData[uuid]["secondGID"]]['Survey']['Robot Comparison']['Which robot was more competent?'])
            row.append(surveyData[uuid][surveyData[uuid]["secondGID"]]['Survey']['Robot Comparison']['Which robot was more stubborn?'])
            row.append(surveyData[uuid][surveyData[uuid]["secondGID"]]['Survey']['Robot Comparison']['Which robot was more curious?'])
            row.append(surveyData[uuid][surveyData[uuid]["secondGID"]]['Survey']['Robot Comparison']['Which robot was more polite?'])
            row.append(surveyData[uuid][surveyData[uuid]["secondGID"]]['Survey']['Robot Comparison']['Which robot inconvenienced you more?'])
            row.append(surveyData[uuid][surveyData[uuid]["secondGID"]]['Survey']['Robot Comparison']['Which robot would you be more willing to help in the future?'])
            row.append(surveyData[uuid][surveyData[uuid]["secondGID"]]['Survey']['Robot Comparison']['Which robot was better at adapting its behavior to you as an individual?'])
            row.append(surveyData[uuid][surveyData[uuid]["secondGID"]]['Survey']['Robot Comparison']['Which robot was better at adapting its behavior to the situation(s) you were in?'])
            row.append(surveyData[uuid][surveyData[uuid]["secondGID"]]['Survey']['Robot Comparison']['Which robot did you help more?'])
            row.append(surveyData[uuid][surveyData[uuid]["secondGID"]]['Survey']['Robot Comparison']["Which robot did you not help more (e.g. saying \"Can't Help\" or ignoring it)?"])

            row.append(surveyData[uuid][surveyData[uuid]["secondGID"]]['Survey']["In instances when the robot asked for help, why did you help or not help it?"])
            row.append(surveyData[uuid][surveyData[uuid]["secondGID"]]['Survey']["What differences were there between Robot #1 (Orange) and Robot #2 (Purple)?"])
            row.append(surveyData[uuid][surveyData[uuid]["secondGID"]]['Survey']["What do you think this study was about?"])
            row.append(surveyData[uuid][surveyData[uuid]["secondGID"]]['Survey']["Are there any other thoughts you’d like to share with us? If so, please add them here."])

            row.append(surveyData[uuid]['Demography']['Age'])
            row.append(surveyData[uuid]['Demography']['Gender'])
            row.append(surveyData[uuid]['Demography']['Video Game Experience'])
            row.append(surveyData[uuid]['Demography']['Survey1 Duration'])
            row.append(surveyData[uuid]['Demography']['Survey2 Duration'])
            row.append(surveyData[uuid][0]["averageBusyness"])
            row.append(surveyData[uuid][2]["averageBusyness"])
            row.append(surveyData[uuid][0]["score"])
            row.append(surveyData[uuid][2]["score"])

            row.append(surveyData[uuid][surveyData[uuid]["firstGID"]]['Survey']["Attention Check Total"])
            row.append(surveyData[uuid][surveyData[uuid]["secondGID"]]['Survey']["Attention Check Total"])

            writer.writerow(row)
            i += 1
        print("wrote {} data rows".format(i))

def responseCountByType(surveyData):
    responsesToCount = {response : 0 for response in ResponseToHelpQuery}
    for uuid in surveyData:
        responseSequence = surveyData[uuid]["humanHelpSequence"]["overall"]
        for response in responseSequence:
            responsesToCount[response] += 1
    return responsesToCount

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
    header = ["UUID", "TaskI", "Busyness", "Past Frequency of Asking", "Past Frequency of Helping Accurately", "Human Response", "Prosociality", "Slowness", "Busyness Numeric", "Num Recent Times Did Not Help", "Age"]
    with open(filepath, "w") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow(header)
        i = 0
        for uuid, taskI, busyness, freqOfAsking, freqOfHelpingAccurately, responseNumber, numRecentTimesDidNotHelp in perResponseDataset:
            row = [uuid, taskI, busyness, freqOfAsking, freqOfHelpingAccurately, responseNumber, surveyData[uuid]["Demography"]["Prosociality"], surveyData[uuid]["Demography"]["Slowness"], busynessNumericRepresentation[busyness], numRecentTimesDidNotHelp, surveyData[uuid]["Demography"]["Age"]]
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

def getHumanPerformance(humanDidArriveOnTime):
    assert(len(humanDidArriveOnTime) == 28)
    numTimesHumanArrivedOnTime = 0
    for robotIndex in [1,2,4,5,6,8,9,11,12,13,15,16,18,19,20,22,23,25,26,27]:
        if humanDidArriveOnTime[robotIndex]:
            numTimesHumanArrivedOnTime += 1
    return numTimesHumanArrivedOnTime

if __name__ == "__main__":
    numGIDs = 3

    baseDir = "../flask/ec2_outputs_evaluation_2021/"
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
    completedGameIDs["2"].append(2028)
    print("completedGameIDs", completedGameIDs)
    uuidToGID = {}
    for gid in completedGameIDs:
        for uuid in completedGameIDs[gid]:
            uuidToGID[int(uuid)] = int(gid)

    # raise Exception()

    surveyData = processSurveyData(baseDir + "Human Help Evaluation Study 2021 Survey#%d (Responses) - Form Responses 1.csv")
    # print("surveyData")
    # pprint.pprint(surveyData)
    # raise Exception()

    # NOTE: I don't believe this is still applicable now that the task sequence
    # is different for the evaluation
    taskDefinitions = {}
    for gid in range(numGIDs):
        filepath = "../flask/assets/tasks/{}.json".format(gid)
        taskDefinitions[gid] = loadTaskDefinitionFile(filepath)
    addMinTaskTime(taskDefinitions, "../flask/assets/min_task_time.json")

    # print("taskDefinitions")
    # pprint.pprint(taskDefinitions)

    tutorialTaskDefinition = loadTaskDefinitionFile("../flask/assets/tasks/tutorial.json")

    uuidsToKeep = []

    gidsInComparison = [0, 2] # 0 must be first, since in the difference I take the first GID minus the second
    comparisonDescriptor = "Hybrid_vs_Individual"
    # uuidsToKeep += [2004] # amal test
    uuidsToKeep += [2006, 2008, 2016, 2021, 2028, 2036] # eval 1
    uuidsToKeep += [2038, 2040] # eval 2
    uuidsToKeep += [2042, 2043, 2046, 2048, 2051, 2055, 2061, 2060, 2058] # need to categorize into evals

    # Remove the UUIDs of people who filled out the survey but are not actual datapoints
    uuidsToDel = []
    for uuid in surveyData:
        if uuid not in uuidsToKeep:
            uuidsToDel.append(uuid)
    # raise Exception(uuidsToDel)
    for uuid in uuidsToDel:
        del surveyData[uuid]

    if len(uuidsToKeep) != len(surveyData):
        for uuid in uuidsToKeep:
            if uuid not in surveyData:
                print("UUID {} did not fill out the survey".format(uuid))
        for uuid in surveyData:
            if uuid not in uuidsToKeep:
                print("UUID {} completed the survey but is not in uuidsToKeep".format(uuid))
        raise Exception("len(uuidsToKeep) = %d, len(surveyData) = %d" % (len(uuidsToKeep), len(surveyData)))

    gidToUUIDs = {}
    for uuid in surveyData:
        gid = uuidToGID[uuid]
        if gid not in gidToUUIDs:
            gidToUUIDs[gid] = []
        gidToUUIDs[gid].append(uuid)
    # raise Exception("gidToUUIDs", gidToUUIDs)

    # For each UUID, get the corresponding GID and gameLog
    consentDurations = []
    tutorialDurations = []
    game1Durations = []
    survey1Durations = []
    game2Durations = []
    survey2Durations = []
    firstGIDToUUIDs = {gid:[] for gid in gidsInComparison}
    for uuid in surveyData:
        print("UUID", uuid)

        firstGID = uuidToGID[uuid]
        firstGIDToUUIDs[firstGID].append(uuid)
        secondGID = gidsInComparison[1] if firstGID==gidsInComparison[0] else gidsInComparison[0]
        surveyData[uuid]["firstGID"] = firstGID
        surveyData[uuid]["secondGID"] = secondGID

        # Reverse the Robot Comparison Qs if firstGID is Hybrid (so Hybrid is always positive)
        if firstGID == 0:
            for robotComparisonQ in surveyData[uuid]["Survey2"]["Robot Comparison"]:
                surveyData[uuid]["Survey2"]["Robot Comparison"][robotComparisonQ] *= -1

        tutorialLog = loadGameLog(baseDir + "{}/0_tutorial_data.json".format(uuid))
        tutorialHelpGivingData, tutorialHumanHelpSequence, _, _, _, _ = processGameLog(tutorialLog, tutorialTaskDefinition)
        surveyData[uuid]["Demography"]["tutorialOverallHelping"] = tutorialHelpGivingData["overall"]

        for gid in gidsInComparison:
            surveyData[uuid][gid] = {}

            filename = "{}_data.json".format(gid)
            gameLog = loadGameLog(baseDir + "{}/{}".format(uuid, filename))

            policyFilepath = baseDir + "{}/{}_policy_output.json".format(uuid, gid)

            policyLog = loadPolicyLog(policyFilepath)
            surveyData[uuid][gid]["policyResults"] = {}
            surveyData[uuid][gid]["policyResults"]["metrics"], surveyData[uuid][gid]["policyResults"]["rawData"], surveyData[uuid][gid]["policyResults"]["randomEffectsVariances"], surveyData[uuid][gid]["policyResults"]["metricsByBusyness"], surveyData[uuid][gid]["policyResults"]["askData"] = processPolicyLog(policyLog)
            surveyData[uuid][gid]["averageBusyness"] = 0.0
            for busyness in surveyData[uuid][gid]["policyResults"]["metricsByBusyness"]:
                numTimesAtBusyness = len(surveyData[uuid][gid]["policyResults"]["metricsByBusyness"][busyness]['asking'])
                surveyData[uuid][gid]["averageBusyness"] += busyness*numTimesAtBusyness/20.0

            surveyData[uuid][gid]["helpGivingData"], surveyData[uuid][gid]["humanHelpSequence"], surveyData[uuid][gid]["slownessesPerTask"], surveyData[uuid][gid]["score"], surveyData[uuid][gid]["humanDidArriveOnTime"], surveyData[uuid][gid]["userTookBreak"] = processGameLog(gameLog, taskDefinitions[gid])#, afterTaskI=6)
            # surveyData[uuid][gid]["policyResults"]["metrics"]["humanPerformance"] = getHumanPerformance(surveyData[uuid][gid]["humanDidArriveOnTime"])/20 # surveyData[uuid][gid]["score"]/280
            # surveyData[uuid][gid]["policyResults"]["metrics"]["robotPerformance"] = surveyData[uuid][gid]['policyResults']['metrics']['numCorrectRooms']/20
            # surveyData[uuid][gid]["policyResults"]["metrics"]["averagePerformance"] = 0.5*surveyData[uuid][gid]["policyResults"]["metrics"]["humanPerformance"] + 0.5*surveyData[uuid][gid]["policyResults"]["metrics"]["robotPerformance"]
            # surveyData[uuid][gid]["policyResults"]["metrics"]["rewardAdjusted"] = surveyData[uuid][gid]["policyResults"]["metrics"]["numCorrectRooms"] - 0.5*surveyData[uuid][gid]['policyResults']['metrics']['pctAsking']*20

            surveyData[uuid][gid]["policyResults"]["robotAskedOnFirstRound"] = (surveyData[uuid][gid]["policyResults"]["rawData"][1] == 'ask')
            surveyData[uuid][gid]["policyResults"]["humanHelpedOnFirstRound"] = (surveyData[uuid][gid]["policyResults"]["rawData"][2]['robot_room_obs'] == 'obs_human_helped')

            lastBusynessFromRawData = -1
            surveyData[uuid][gid]["policyResults"]["humanBusynessAtRobotFirstAsk"] = lastBusynessFromRawData
            surveyData[uuid][gid]["policyResults"]["humanHelpedAtRobotFirstAsk"] = 0
            for i in range(len(surveyData[uuid][gid]["policyResults"]["rawData"])):
                if (i % 4) == 1: # action
                    if surveyData[uuid][gid]["policyResults"]["rawData"][i] == 'ask':
                        if lastBusynessFromRawData == -1:
                            lastBusynessFromRawData = 1 # first round
                        surveyData[uuid][gid]["policyResults"]["humanBusynessAtRobotFirstAsk"] = lastBusynessFromRawData
                        surveyData[uuid][gid]["policyResults"]["humanHelpedAtRobotFirstAsk"] = 1 if surveyData[uuid][gid]["policyResults"]["rawData"][i+1]['robot_room_obs'] == 'obs_human_helped' else 0
                        break
                elif (i % 4) == 2: # obs
                    lastBusynessFromRawData = int(surveyData[uuid][gid]["policyResults"]["rawData"][i]['human_busyness_obs'])

            assert len(surveyData[uuid][gid]["slownessesPerTask"]) == 28
            # surveyData[uuid]["Demography"]["Slowness"] = 0.0
            # for taskI in taskIForSlowness:
            #     print("uuid", uuid, "taskI", taskI, surveyData[uuid]["slownessesPerTask"], len(surveyData[uuid]["slownessesPerTask"]))
            #     surveyData[uuid]["Demography"]["Slowness"] += surveyData[uuid]["slownessesPerTask"][taskI]
            # surveyData[uuid]["Demography"]["Slowness"] /= len(taskIForSlowness)

        getTimes(surveyData, uuid, baseDir)
        consentDurations.append(surveyData[uuid]["tutorialTime"]-surveyData[uuid]["startTime"])
        tutorialDurations.append(surveyData[uuid]["gameTime_a"]-surveyData[uuid]["tutorialTime"])
        game1Durations.append(surveyData[uuid]["surveyTime_a"]-surveyData[uuid]["gameTime_a"])
        survey1Durations.append(surveyData[uuid]["Demography"]["Survey1 Duration"])
        game2Durations.append(surveyData[uuid]["surveyTime_b"]-surveyData[uuid]["gameTime_b"])
        survey2Durations.append(surveyData[uuid]["Demography"]["Survey2 Duration"])

        surveyData[uuid]["completionCode"] = uuidToCompletionID[str(uuid)] if str(uuid) in uuidToCompletionID else None

        surveyData[uuid][firstGID]["Survey"] = surveyData[uuid]["Survey1"]
        del surveyData[uuid]["Survey1"]
        surveyData[uuid][secondGID]["Survey"] = surveyData[uuid]["Survey2"]
        del surveyData[uuid]["Survey2"]

    pprint.pprint(surveyData)

    consentDurations = np.array(consentDurations)
    tutorialDurations = np.array(tutorialDurations)
    game1Durations = np.array(game1Durations)
    survey1Durations = np.array(survey1Durations)
    game2Durations = np.array(game2Durations)
    survey2Durations = np.array(survey2Durations)
    print("Consent mean, sd, min, max", np.mean(consentDurations), np.std(consentDurations), np.amin(consentDurations), np.amax(consentDurations))
    print("Tutorial mean, sd, min, max", np.mean(tutorialDurations), np.std(tutorialDurations), np.amin(tutorialDurations), np.amax(tutorialDurations))
    print("Game1 mean, sd, min, max", np.mean(game1Durations), np.std(game1Durations), np.amin(game1Durations), np.amax(game1Durations))
    print("Survey1 mean, sd, min, max", np.mean(survey1Durations), np.std(survey1Durations), np.amin(survey1Durations), np.amax(survey1Durations))
    print("Game2 mean, sd, min, max", np.mean(game2Durations), np.std(game2Durations), np.amin(game2Durations), np.amax(game2Durations))
    print("Survey2 mean, sd, min, max", np.mean(survey2Durations), np.std(survey2Durations), np.amin(survey2Durations), np.amax(survey2Durations))
    print("Consent quartiles", np.percentile(consentDurations, [0, 25, 50, 75, 100]))
    print("Tutorial quartiles", np.percentile(tutorialDurations, [0, 25, 50, 75, 100]))
    print("Game1 quartiles", np.percentile(game1Durations, [0, 25, 50, 75, 100]))
    print("Survey1 quartiles", np.percentile(survey1Durations, [0, 25, 50, 75, 100]))
    print("Game2 quartiles", np.percentile(game2Durations, [0, 25, 50, 75, 100]))
    print("Survey2 quartiles", np.percentile(survey2Durations, [0, 25, 50, 75, 100]))

    # raise Exception()

    writeCSV(surveyData, taskDefinitions, baseDir+"humanHelpUserStudyData"+comparisonDescriptor+".csv")
    makePolicyGraphs(surveyData, comparisonDescriptor)

    print("firstGIDToUUIDs", firstGIDToUUIDs)
