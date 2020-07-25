import csv, pprint, os, json, pickle
import matplotlib.pyplot as plt
from enum import Enum

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

class ResponseToHelpQuery(Enum):
    IGNORED = 0
    CANT_HELP = 1
    HELPED = 2
    HELPED_INACCURATELY = 3
    AVOIDED = 4 # The user saw the robot and then changed directions to avoid it

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

def processGameLog(gameLog, taskDefinition):
    previousLogEntry = None
    playerTaskI = 0
    isRobotHelpQueryActive = False
    didRobotAppear = False
    humanHelpSequence = {"high":[], "medium":[], "free time":[], "overall":[]}

    print("UUID %s, GID %s" % (gameLog[0]["uuid"], gameLog[0]["gid"]))

    for logEntry in gameLog:
        if previousLogEntry is None:
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

        if "buttonName" in logEntry and logEntry["buttonName"] == "Yes":
            didHumanSayYes = True
            didHumanSayStopFollowing = False
            wasHelpAccurate = False
            didHumanSayCantHelp = False
        elif "buttonName" in logEntry and logEntry["buttonName"] == "Stop Following":
            didHumanSayStopFollowing = True
            wasHelpAccurate = len(logEntry["robot"]["taskPlan"]) <= 5
            didHumanSayCantHelp = False
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
            elif "buttonName" in logEntry and logEntry["buttonName"] == "Stop Following":
                didHumanSayStopFollowing = True
                wasHelpAccurate = len(logEntry["robot"]["taskPlan"]) <= 5
                didHumanSayCantHelp = False
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
            if (playerTaskI > 6): # skip the first round of help-seeking
                busyness = taskDefinition["tasks"][playerTaskI]["busyness"]
                if (didHumanSayYes):
                    if (wasHelpAccurate):
                        response = ResponseToHelpQuery.HELPED
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
                humanHelpSequence[busyness].append(response)
                humanHelpSequence["overall"].append(response)
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
        if response == ResponseToHelpQuery.HELPED:
            total += 1
    return total/num if num != 0 else None

def processSurveyData(filepath):
    # Columns from the CSV
    uuidCol = 1
    nasaTLXCols = {
        "Mental Demand": 2,
        "Physical Demand": 3,
        "Temporal Demand": 4,
        "Performance": 5,
        "Effort": 6,
        "Frustration": 7,
    }
    rosasCols = {
        "Competence" : range(8,14),
        "Warmth" : range(14,21),
        "Discomfort" : range(21,27),
        "Curiosity" : range(27,29),
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
            uuid = int(row[uuidCol])
            if uuid in processedData:
                raise Exception("UUID %d has multiple rows" % uuid)
            processedData[uuid] = {
                "NASA-TLX" : {},
                "RoSAS" : {},
                "Demography" : {},
            }
            for nasaTLXHeading in nasaTLXCols:
                processedData[uuid]["NASA-TLX"][nasaTLXHeading] = int(row[nasaTLXCols[nasaTLXHeading]])
            for rosasHeading in rosasCols:
                total, num = 0, 0
                for col in rosasCols[rosasHeading]:
                    total += rosasMapping[row[col]]
                    num += 1
                processedData[uuid]["RoSAS"][rosasHeading] = total/num
            for openEndedQ, openEndedCol in openEndedCols.items():
                processedData[uuid][openEndedQ] = row[openEndedCol]
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

    # raise Exception()

    surveyData = processSurveyData(baseDir + "Human Help User Study Survey (Responses) - Form Responses 1.csv")
    taskDefintions = {}
    for gid in range(numGIDs):
        filepath = "../flask/assets/tasks/{}.json".format(gid)
        taskDefintions[gid] = loadTaskDefinitionFile(filepath)

    uuidsToKeep = []
    # uuidsToKeep = [100, 103, 104, 108, 110, 122] # pilot1
    # uuidsToKeep = [133] # friendsData
    uuidsToKeep += [136, 137, 138, 140, 141, 142, 143, 144, 147, 149, 152, 153, 155, 156, 157, 159, 146, 166, 167, 170, 179] # pilot2
    uuidsToKeep += [184, 185, 186, 187, 188, 189, 190, 191, 193, 196, 199, 201, 202, 203, 205, 209] # pilot3

    # uuidsToKeep += [202]
    uuidsToDel = []
    for uuid in surveyData:
        if uuid not in uuidsToKeep:
            uuidsToDel.append(uuid)
    for uuid in uuidsToDel:
        del surveyData[uuid]

    # For each UUID, get the corresponding GID and gameLog
    for uuid in surveyData:
        print("UUID", uuid)
        gotGID = False
        for filename in os.listdir(baseDir + "{}".format(uuid)):
            if "_data." in filename and "_tutorial_" not in filename:
                if gotGID:
                    raise Exception("UUID {} has multiple GIDs".format(uuid))
                gid = int(filename[0])
                surveyData[uuid]["gid"] = gid
                gameLog = loadGameLog(baseDir + "{}/{}".format(uuid, filename))
                surveyData[uuid]["helpGivingData"], surveyData[uuid]["humanHelpSequence"] = processGameLog(gameLog, taskDefintions[gid])
                surveyData[uuid]["completionCode"] = uuidToCompletionID[str(uuid)] if str(uuid) in uuidToCompletionID else None
                gotGID = True
        if not gotGID:
            raise Exception("UUID {} has no GIDs".format(uuid))

    pprint.pprint(surveyData)

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
    rosasFactorsOrder = ["Competence", "Discomfort", "Warmth", "Curiosity"]
    rosas = {factor : [] for factor in rosasFactorsOrder}
    nasaTLXFactorOrder = ["Mental Demand", "Physical Demand", "Temporal Demand", "Performance", "Effort", "Frustration"]
    nasaTLX = {factor : [] for factor in nasaTLXFactorOrder}
    busynessFactorOrder = ["high", "medium", "free time"]
    busyness = {factor : [] for factor in busynessFactorOrder}
    prosociality = {"low: < {} (median)".format(prosocialityMedian) : ([], []), "high: >= {} (median)".format(prosocialityMedian) : ([], [])}
    demographicFactors = ["Prosociality", "Navigational Ability", "Video Game Experience", "Age", "Gender"]
    demography = {factor : [] for factor in demographicFactors}
    for uuid in surveyData:
        gid = surveyData[uuid]["gid"]
        gids.append(gid)
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
        # prosociality
        factor = "overall"
        if uuid in prosocialityLow:
            key = "low: < {} (median)".format(prosocialityMedian)
            prosociality[key][0].append(freq)
            prosociality[key][1].append(surveyData[uuid]["helpGivingData"][factor])
        else:
            key = "high: >= {} (median)".format(prosocialityMedian)
            prosociality[key][0].append(freq)
            prosociality[key][1].append(surveyData[uuid]["helpGivingData"][factor])
        # Demographic Factors
        for factor in demographicFactors:
            demography[factor].append(surveyData[uuid]["Demography"][factor])

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
    plt.savefig(baseDir + "rosas.png")

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
    plt.savefig(baseDir + "nasaTLX.png")

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
    plt.savefig(baseDir + "willingnessToHelpBusyness.png")

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
    plt.savefig(baseDir + "willingnessToHelpProsociality.png")

    # Demographic Factors
    for factor in demographicFactors:
        fig = plt.figure()
        ax = fig.subplots()
        fig.suptitle('Demographic Makeup: '+factor)
        ax.hist(demography[factor])
        ax.set_xlabel(factor)
        ax.set_ylabel("Count")
        if factor in ["Prosociality", "Navigational Ability", "Video Game Experience"]:
            ax.set_xlim([0,5.5])
        plt.savefig(baseDir + "%s.png" % factor)

    # GIDs
    fig = plt.figure()
    ax = fig.subplots()
    fig.suptitle('GIDs')
    ax.hist(gids)
    ax.set_xlabel("Game ID")
    ax.set_ylabel("Count")
    plt.savefig(baseDir + "gids.png")
