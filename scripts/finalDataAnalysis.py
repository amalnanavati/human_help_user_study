import csv, pprint, os, json, pickle
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from enum import Enum
import numpy as np
import datetime

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

def loadGameLog(filepath):
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
            gameLog.append(json.loads(line))
        # Sometimes, the data arrives a few ms out of order
        if "gameStateID" in gameLog[0]:
            gameLog.sort(key=lambda x : int(x['gameStateID']))
        else:
            gameLog.sort(key=lambda x : int(x['dtime']))
    return gameLog

def loadTaskDefinitionFile(filepath):
    with open(filepath, "r") as f:
        taskDefinition = json.load(f)
    return taskDefinition

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

    for logEntry in gameLog:
        if previousLogEntry is None:
            previousLogEntry = logEntry
            continue

        if "robot" not in previousLogEntry or "robot" not in logEntry:
            previousLogEntry = logEntry
            continue

        if "taskI" in logEntry["player"]:
            playerTaskI = int(logEntry["player"]["taskI"])
        else:
            if (int(previousLogEntry["player"]["currentState"]) == PlayerState.DISTRACTION_TASK.value and
                int(logEntry["player"]["currentState"]) == PlayerState.NAVIGATION_TASK.value):
                playerTaskI += 1
                isRobotHelpQueryActive = False
                print("taskI changed", playerTaskI, logEntry["dtime"])

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
            humanHelpSequence["robot interaction sequence"][robotActionI] = response
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

    return {descriptor : getAverageHelpRate(humanHelpSequence[descriptor]) for descriptor in humanHelpSequence}, humanHelpSequence

def getAverageHelpRate(sequence):
    total, num = 0, 0
    for response in sequence:
        num += 1
        if response == ResponseToHelpQuery.HELPED_ACCURATELY:
            total += 1
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
        header = None
        for row in reader:
            if header is None:
                header = row
                continue
            surveyCompletionTime = datetime.datetime.strptime(row[timeCol], "%m/%d/%Y %H:%M:%S").timestamp()
            uuid = int(row[uuidCol])
            if uuid in processedData:
                raise Exception("UUID %d has multiple rows" % uuid)
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
        with open(baseDir+"{}/".format(uuid)+filename, "r") as f:
            timeFloat = float(f.read().strip())
            surveyData[uuid][filename[:-4]] = timeFloat
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
    demographicFactors = ["Prosociality", "Navigational Ability", "Video Game Experience", "Age", "Gender", "Survey Duration", "Open Ended Length", "RoSAS Variance", "tutorialOverallHelping"]
    demography = {factor : [] for factor in demographicFactors}
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
            demography[factor].append(surveyData[uuid]["Demography"][factor])
        surveyDurations.append((surveyData[uuid]["Demography"]["Survey Duration"], uuid))
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
            axes[i][k].set_ylim([0,15])
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
            axes[i][k].set_ylim([0,15])
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
    for uuid in surveyData:
        gid = surveyData[uuid]["gid"]
        marker = markers[gid]
        x = surveyData[uuid]['helpGivingData']['high']
        y = surveyData[uuid]['helpGivingData']['medium']
        z = surveyData[uuid]['helpGivingData']['free time']
        markerToXYZ[marker][0].append(x)
        markerToXYZ[marker][1].append(y)
        markerToXYZ[marker][2].append(z)
        markerToXYZ[marker][3] = "Freq: %.1f" % ((gid+1)/5.0)

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    for marker in markerToXYZ:
        ax.scatter(
            markerToXYZ[marker][0],
            markerToXYZ[marker][1],
            markerToXYZ[marker][2],
            label=markerToXYZ[marker][3],
            marker=marker,
        )

    ax.set_xlabel('Willingness to Help for High')
    ax.set_ylabel('Willingness to Help for Medium')
    ax.set_zlabel('Willingness to Help for Free Time')
    ax.legend()

    plt.savefig(baseDir + "fullScatter{}.png".format(descriptor))
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

def writeCSV(surveyData, taskDefinitions, filepath, numericFilepath):
    header = [
        "User ID",
        "Frequency",
        "High Busyness Willingness To Help",
        "Medium Busyness Willingness To Help",
        "Free Time Busyness Willingness To Help",
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
            row.append(surveyData[uuid]['Demography']['Survey Duration'])
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
                response = surveyData[uuid]['humanHelpSequence']['robot interaction sequence'][i]
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
        numericHeader = ["Busyness", "Frequency", "Prosociality", "Willingness To Help"]
        with open(numericFilepath, "w") as f:
            writer = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)
            writer.writerow(numericHeader)
            i = 0
            for uuid in surveyData:
                for busyness in surveyData[uuid]['helpGivingData']:
                    if busyness == "overall": continue
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

    uuidsToKeep = []
    # uuidsToKeep = [100, 103, 104, 108, 110, 122] # pilot1
    # uuidsToKeep = [133] # friendsData

    uuidsToKeep += [136, 137, 138, 140, 141, 142, 143, 144, 146, 147, 149, 151, 152, 153, 155, 156, 157, 159, 166, 167, 170, 179] # pilot 2
    uuidsToKeep += [184, 185, 186, 187, 188, 189, 190, 191, 193, 196, 197, 201, 202, 203, 205, 209] # pilot 3
    uuidsToKeep += [228, 232, 233, 234, 236, 238, 239, 240, 242, 243, 244, 247, 248, 251, 253, 259, 260, 263] # batch 4
    uuidsToKeep += [264, 266, 267, 269, 271, 272] # batch 5
    uuidsToKeep += [279, 276, 277, 278, 280, 281, 283, 284] # batch 6
    uuidsToKeep += [288, 286, 287, 285, 289, 292, 291, 293, 294] # batch 7
    uuidsToKeep += [300, 298, 297, 296, 301, 304, 306] # batch 8
    uuidsToKeep += [310, 312, 317, 315, 318, 321, 324] # batch 9
    uuidsToKeep += [325, 327, 329, 332, 333, 334, 335, 336, 343] # batch 10
    uuidsToKeep += [346, 352, 353, 359, 365, 367, 374, 380] # batch 11

    # uuidsToKeep += [264]

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
    for uuid in surveyData:
        print("UUID", uuid)
        try:
            gid = uuidToGID[uuid]
        except Exception as err:
            for filename in os.listdir(baseDir + "{}/".format(uuid)):
                if "_data" in filename and "tutorial" not in filename:
                    gid = int(filename[0])
        # if uuid == 299:
        #     gid = 4
        # else:
        #     gid = uuidToGID[uuid]
        filename = "{}_data.json".format(gid)
        surveyData[uuid]["gid"] = gid

        tutorialLog = loadGameLog(baseDir + "{}/0_tutorial_data.json".format(uuid))
        tutorialHelpGivingData, tutorialHumanHelpSequence = processGameLog(tutorialLog, loadTaskDefinitionFile("../flask/assets/tasks/tutorial.json"))

        surveyData[uuid]["Demography"]["tutorialOverallHelping"] = tutorialHelpGivingData["overall"]
        gameLog = loadGameLog(baseDir + "{}/{}".format(uuid, filename))

        surveyData[uuid]["helpGivingData"], surveyData[uuid]["humanHelpSequence"] = processGameLog(gameLog, taskDefinitions[gid], afterTaskI=6)
        getTimes(surveyData, uuid, baseDir)
        surveyData[uuid]["completionCode"] = uuidToCompletionID[str(uuid)] if str(uuid) in uuidToCompletionID else None

    pprint.pprint(surveyData)

    print("responseCountByType", responseCountByType(surveyData))

    writeCSV(surveyData, taskDefinitions, baseDir+"humanHelpUserStudyDataComplete.csv", baseDir+"humanHelpUserStudyDataCompleteNumeric.csv")

    makeGraphs(surveyData)

    # Remove the users who do not meet the inclusion critereon
    surveyDataNoStraightlining = {}
    uuidsToDel = []
    for uuid in surveyData:
        if surveyData[uuid]["Demography"]["RoSAS Variance"] >= 0.67:
            surveyDataNoStraightlining[uuid] = surveyData[uuid]

    print("len(surveyDataNoStraightlining)", len(surveyDataNoStraightlining), "len(surveyData)", len(surveyData))

    makeGraphs(surveyDataNoStraightlining, "_noStraightlining")

    # Remove the users who do not meet the inclusion critereon
    surveyDataNoLowSurveyTime = {}
    uuidsToDel = []
    for uuid in surveyData:
        if surveyData[uuid]["Demography"]["Survey Duration"] >= 180:
            surveyDataNoLowSurveyTime[uuid] = surveyData[uuid]

    print("len(surveyDataNoLowSurveyTime)", len(surveyDataNoLowSurveyTime), "len(surveyData)", len(surveyData))

    makeGraphs(surveyDataNoLowSurveyTime, "_noLowSurveyTime")

    # Remove the users who do not meet the inclusion critereon
    surveyDataBriefOpenEndedResponses = {}
    uuidsToDel = []
    for uuid in surveyData:
        if surveyData[uuid]["Demography"]["Open Ended Length"] >= 20:
            surveyDataBriefOpenEndedResponses[uuid] = surveyData[uuid]

    print("len(surveyDataBriefOpenEndedResponses)", len(surveyDataBriefOpenEndedResponses), "len(surveyData)", len(surveyData))

    makeGraphs(surveyDataBriefOpenEndedResponses, "_briefOpenEndedResponses")

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

    writeCSV(surveyDataTutorialOnlyHelping, taskDefinitions, baseDir+"humanHelpUserStudyDataWithExclusion.csv", baseDir+"humanHelpUserStudyDataWithExclusionNumeric.csv")

    makeGraphs(surveyDataTutorialOnlyHelping, "_tutorialOnlyHelping")

    surveyDataOnlyZeros = {}
    surveyDataNoZeros = {}
    surveyDataOnlyZeroesAndTutorialNoHelping = {}
    surveyDataOnlyZeroesAndTooBriefSurvey = {}
    surveyDataOnlyZeroesAndTooBriefSurveyAndTutorialNoHelping = {}
    for uuid in surveyData:
        high = surveyData[uuid]["helpGivingData"]["high"]
        medium = surveyData[uuid]["helpGivingData"]["medium"]
        freeTime = surveyData[uuid]["helpGivingData"]["free time"]
        if not (high == 0.0 and medium == 0.0 and freeTime == 0.0):
            surveyDataNoZeros[uuid] = surveyData[uuid]
        else:
            surveyDataOnlyZeros[uuid] = surveyData[uuid]
            if surveyData[uuid]["Demography"]["tutorialOverallHelping"] == 0.0:
                surveyDataOnlyZeroesAndTutorialNoHelping[uuid] = surveyData[uuid]
                if surveyData[uuid]["Demography"]["Survey Duration"] < 180:
                    surveyDataOnlyZeroesAndTooBriefSurveyAndTutorialNoHelping[uuid] = surveyData[uuid]
            if surveyData[uuid]["Demography"]["Survey Duration"] < 180:
                surveyDataOnlyZeroesAndTooBriefSurvey[uuid] = surveyData[uuid]

    print("len(surveyDataNoZeros)", len(surveyDataNoZeros), "len(surveyDataOnlyZeroesAndTutorialNoHelping)", len(surveyDataOnlyZeroesAndTutorialNoHelping), "len(surveyDataOnlyZeroesAndTooBriefSurvey)", len(surveyDataOnlyZeroesAndTooBriefSurvey), "len(surveyDataOnlyZeroesAndTooBriefSurveyAndTutorialNoHelping)", len(surveyDataOnlyZeroesAndTooBriefSurveyAndTutorialNoHelping), "len(surveyData)", len(surveyData))

    makeGraphs(surveyDataNoZeros, "_noZeros")

    # print("surveyDataOnlyZeros")
    # pprint.pprint(surveyDataOnlyZeros)
