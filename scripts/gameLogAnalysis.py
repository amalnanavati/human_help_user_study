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
    filepath ="../flask/outputs/{}/{}_data.json".format(uuid, gid)
    gameLog = loadGameLog(filepath)

    humanResponseToHelp = []
    for logEntry in gameLog:
        ########################################################################
        # YOUR CODE HERE

        # Each log entry is a (often nested) dictionary. Use this function
        # to print it out prettily. (This is just for debugging purposes)
        pprint.pprint(logEntry)

        # Access elements of logEntry using strings. For example:
        robotState = logEntry["robot"]["currentState"]

        # First, determine when the robot asked for help. Then, determine how
        # the human responded. This Google Doc has more pointers:
        # https://docs.google.com/document/d/1_RYKOTqaRre4kbgZDYgtMJP3xeNFwsSFTJ6Suk3SEhg/edit#


        ########################################################################
    return humanResponseToHelp

if __name__ == "__main__":
    uuid = 0 # user ID
    gid = 0 # game ID

    processedData = analyzeGameLog(uuid, gid)
    print(processedData)
