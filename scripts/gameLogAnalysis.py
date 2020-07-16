import json
import pprint

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
        # Sometimes, the data arrives a few ms out
        # of order. Therefore, we reorder it by time
        gameLog.sort(key=lambda x : x['dtime'])
    return gameLog

def analyzeGameLog(uuid, gid):
    """
    Input:
      - the unique user ID
      - the game ID

     Output:
       - a list, where the length of the list is the number of times the robot
         asked for help, and the entries are strings indicating how the human
         responded. For example, say the robot asked for help three times, and
         the first time the player said "Yes," the second time the player ignored
         the robot, and the third time the player says "Can't Help." Then, the
         output will be ["Yes", "Ignore", "Can't Help"].
    """
    filepath ="../flask/outputs/1/0_data.json".format(uuid, gid)
    tasks ="../flask/assets/tasks/0.json".format(uuid, gid)
    gameLog = loadGameLog(filepath)

    prevIsOne = False
    askedForHelp = False

    prevRobotOffScreen = False
    taskNum = 0;

    humanResponseToHelp = []
    for logEntry in gameLog:
        # {"uuid":"1","gid":"0","eventType":0,"dtime":123498,"player":{"currentTile":{"x":35,"y":38},"nextTile":{"x":35,"y":38},"currentState":0,"score":50},"player_anim_is_playing":false,"player_anim_key":"up","robot_anim_key":null,"active_player_movement_timer":false,"distractionTaskTimerSecs":10.016000000000004,"robot":{"currentTile":{"x":35,"y":35},"plan":[{"x":35,"y":36},{"x":35,"y":37},{"x":35,"y":38},{"x":36,"y":38},{"x":36,"y":39}],
        # "currentState":1,"previousState":1,"helpBubbleVisible":false,"currentActionI":3},"active_robot_movement_timer":true}

        # {"uuid":"1","gid":"0","eventType":1,"dtime":135994,"player":{"currentTile":{"x":35,"y":38},"nextTile":{"x":35,"y":38},"currentState":0,"score":50},"player_anim_is_playing":false,"player_anim_key":"up","robot_anim_key":null,"active_player_movement_timer":false,"distractionTaskTimerSecs":10.016000000000004,"robot":{"currentTile":{"x":35,"y":35},"plan":null,
        # "currentState":3,"previousState":3,"helpBubbleVisible":true,"currentActionI":3},"active_robot_movement_timer":false,"buttonName":"Yes","x":2298.8995921360156,"y":2197.407279029463}

########################################################################
        # YOUR CODE HERE

        # Each log entry is a (often nested) dictionary. Use this function
        # to print it out prettily. (This is just for debugging purposes)
        #pprint.pprint(logEntry["robot"]["currentState"])

        # Access elements of logEntry using strings. For example:
        robotState = logEntry["robot"]["currentState"]


        # First, determine when the robot asked for help. Then, determine how
        # the human responded. This Google Doc has more pointers:
        # https://docs.google.com/document/d/1_RYKOTqaRre4kbgZDYgtMJP3xeNFwsSFTJ6Suk3SEhg/edit#


        # 1) how the human responded; but also
        # 2) where the human was going at that time; and - TODO not working
        # 3) what the time limit was for that goal. - TODO not working

        # determine what task the human completed and using that determine next goal

        if prevIsOne and robotState == 3:
            askedForHelp = True

        if robotState == 1:
            prevIsOne = True
        else:
            prevIsOne = False

        if prevRobotOffScreen and logEntry["robot"]["currentTile"]["x"] != -1:
            taskNum = taskNum + 1;

        if logEntry["robot"]["currentTile"]["x"] == -1:
            prevRobotOffScreen = True;
        else:
            prevRobotOffScreen = False;

        if logEntry.get("buttonName") is not None:
            if askedForHelp and logEntry["buttonName"] == "Yes":
                pprint.pprint("User said yes and was on task " + str(taskNum))
                askedForHelp = False;
                pprint.pprint(logEntry)
            elif askedForHelp and logEntry["buttonName"] == "No":
                pprint.pprint("User said no and was on task " + str(taskNum))
                askedForHelp = False;
                pprint.pprint(logEntry)
        elif askedForHelp and robotState == 2:
                pprint.pprint("User ignored and was on task " + str(taskNum))
                askedForHelp = False;









    ########################################################################
    return humanResponseToHelp

if __name__ == "__main__":
    uuid = 1 # user ID
    gid = 0 # game ID

    processedData = analyzeGameLog(uuid, gid)
    print(processedData)
