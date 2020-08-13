import json, pprint

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
            gameLog.append(json.loads(line))
        # Sometimes, the data arrives a few ms out of order
        if sort:
            if "gameStateID" in gameLog[0]:
                gameLog.sort(key=lambda x : int(x['gameStateID']))
            else:
                gameLog.sort(key=lambda x : int(x['dtime']))
    return gameLog

def fix501Files(surveyData, baseDir, taskDefinitions, tutorialTaskDefinition):
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
            if int(gameLog[-1]["gameStateID"]) == 3119:
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
    tutorialHelpGivingData, tutorialHumanHelpSequence = processGameLog(firstTutorialLog, tutorialTaskDefinition)
    surveyData[501]["Demography"]["tutorialOverallHelping"] = tutorialHelpGivingData["overall"]
    surveyData[501]["helpGivingData"], surveyData[501]["humanHelpSequence"] = processGameLog(game3Log, taskDefinitions[3], afterTaskI=6)
    getTimes(surveyData, 501, baseDir)
    surveyData[501]["completionCode"] = uuidToCompletionID[str(501)] if str(501) in uuidToCompletionID else None

    # Second Player -- UUID 505
    tutorialHelpGivingData, tutorialHumanHelpSequence = processGameLog(secondTutorialLog, tutorialTaskDefinition)
    surveyData[505]["Demography"]["tutorialOverallHelping"] = tutorialHelpGivingData["overall"]
    surveyData[505]["helpGivingData"], surveyData[505]["humanHelpSequence"] = processGameLog(game1Log, taskDefinitions[1], afterTaskI=6)
    getTimes(surveyData, 505, baseDir)
    surveyData[505]["completionCode"] = uuidToCompletionID[str(505)] if str(505) in uuidToCompletionID else None

    return

if __name__ == "__main__":



    tutorialGameLog = loadGameLog("../flask/ec2_outputs/501/0_tutorial_data.json")
    gameStateIDs = []
    for logEntry in tutorialGameLog:
        gameStateIDs.append(logEntry["gameStateID"])
    print(gameStateIDs)
