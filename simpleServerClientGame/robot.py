import time
import json
import random
import numpy as np
from enum import Enum
from helpers import print_binary_map

from tile import Tile

class RobotState(object):
    def __init__(self, startTile=(5, 5)):
        self.currentTile = Tile(*startTile)
        self.tileForRendering = Tile(*startTile)
        self.robotHighLevelState = RobotHighLevelState.AUTONOMOUS_MOTION

class RobotHighLevelState(Enum):
    AUTONOMOUS_MOTION = 0
    ASKING_FOR_HELP = 1
    FOLLOWING_HUMAN = 2

class RobotAction(Enum):
    NO_ACTION = -1 # lasts for robotMsPerStep
    MOVE_UP = 0
    MOVE_DOWN = 1
    MOVE_LEFT = 2
    MOVE_RIGHT = 3
    ASK_FOR_HELP = 4

    def setActionTargetuuid(self, uuid):
        self.targetuuid = uuid

    def toDxDy(self):
        if self == RobotAction.NO_ACTION or self == RobotAction.ASK_FOR_HELP:
            return (0,0)
        if self == RobotAction.MOVE_UP:
            return (0,-1)
        if self == RobotAction.MOVE_DOWN:
            return (0,1)
        if self == RobotAction.MOVE_LEFT:
            return (-1,0)
        if self == RobotAction.MOVE_RIGHT:
            return (1,0)
        return (None, None)

    def toAnimationString(self):
        if self == RobotAction.MOVE_UP:
            return "robotUp"
        if self == RobotAction.MOVE_DOWN:
            return "robotDown"
        if self == RobotAction.MOVE_LEFT:
            return "robotLeft"
        if self == RobotAction.MOVE_RIGHT:
            return "robotRight"
        return None

class Robot(object):
    robotSecPerStep = 0.350 # sec

    def __init__(self):
        self.state = RobotState()
        self.currentAction = RobotAction.NO_ACTION
        self.currentActionStartTime = time.time()
        self.targetuuid = None
        self.isActionFinished = True
        self.map = self.loadMap("assets/map3.json", 50, 44)
        # print_binary_map(self.map)

    # adapted from Mridula's code https://github.com/amalnanavati/human_help_user_study/blob/model/scripts/convertToBinaryBitmap.py
    def loadMap(self, filepath, nRows, nCols):
        """
        Returns a bool np array, that is true where there is a wall and false otherwise
        """
        with open(filepath, "r") as f:
            mapData = json.load(f)
            for layer in mapData["layers"]:
                if layer["name"] == "World":
                    return (np.reshape(layer["data"], (nRows, nCols)) != 0)

    def is_in_collision(self, nextTile, userLocations):
        if (nextTile.x > 0 and nextTile.x < self.map.shape[1] and nextTile.y > 0 and nextTile.y < self.map.shape[0]):
            # Check if the next tile would collide with a wall
            if self.map[nextTile.y][nextTile.x]:
                return True
            # Check if the next tile would collide with a user
            else:
                for uuid in userLocations:
                    if ((nextTile.x == userLocations[uuid]["currentTile"].x and nextTile.y == userLocations[uuid]["currentTile"].y) or
                        (nextTile.x == userLocations[uuid]["nextTile"].x and nextTile.y == userLocations[uuid]["nextTile"].y)):
                        return True
            return False
        else:
            return True


    def updateUserState(self, state):
        pass

    def update(self, userLocations):
        # print("ROBOT update", self.isActionFinished, self.state.robotHighLevelState)
        if self.isActionFinished and self.state.robotHighLevelState == RobotHighLevelState.AUTONOMOUS_MOTION:
            self.currentAction = self.getNextAction(userLocations)
            if self.currentAction == RobotAction.ASK_FOR_HELP:
                self.state.robotHighLevelState = RobotHighLevelState.ASKING_FOR_HELP

            #print("Robot x {}, y {}, currentAction {}, userLocations {}".format(self.state.currentTile.x, self.state.currentTile.y, self.currentAction, userLocations))
            self.currentActionStartTime = time.time()
            self.isActionFinished = False
        elif self.isActionFinished and self.state.robotHighLevelState == RobotHighLevelState.FOLLOWING_HUMAN:
            currentUuid = self.currentAction.targetuuid
            xDiff = userLocations[currentUuid]["currentTile"].x - self.state.currentTile.x
            yDiff = userLocations[currentUuid]["currentTile"].y - self.state.currentTile.y

            potentialActions = []
            for action in [RobotAction.MOVE_LEFT, RobotAction.MOVE_RIGHT, RobotAction.MOVE_UP, RobotAction.MOVE_DOWN]:
                dx, dy = action.toDxDy()
                # sets a route for the robot based on the user's position
                if ((dx < 0 and xDiff < 0) or (dx > 0 and xDiff > 0) or
                    (dy < 0 and yDiff < 0) or (dy > 0 and yDiff > 0)):
                    nextTile = Tile(self.state.currentTile.x+dx, self.state.currentTile.y+dy)
                    # Computer collisions
                    if not self.is_in_collision(nextTile, userLocations):
                        action.setActionTargetuuid(None)
                        potentialActions.append(action)

            if len(potentialActions) > 0:
                self.currentAction = random.choice(potentialActions)
            else:
                self.currentAction = RobotAction.NO_ACTION

            self.currentAction.targetuuid = currentUuid
            self.currentActionStartTime = time.time()
            self.isActionFinished = False

        else: # Finish executing the current action
            if self.currentAction in [
                RobotAction.NO_ACTION,
                RobotAction.MOVE_UP,
                RobotAction.MOVE_DOWN,
                RobotAction.MOVE_LEFT,
                RobotAction.MOVE_RIGHT,
                RobotAction.ASK_FOR_HELP]:

                progress = min((time.time()-self.currentActionStartTime)/Robot.robotSecPerStep, 1.0)
                dx, dy = self.currentAction.toDxDy()
                self.state.tileForRendering.x = self.state.currentTile.x + progress*dx
                self.state.tileForRendering.y = self.state.currentTile.y + progress*dy

                if progress >= 1.0:
                    self.state.currentTile.x += dx
                    self.state.currentTile.y += dy
                    self.isActionFinished = True

    def getNextAction(self, userLocations):
        """
        The policy -- given the current state, predict the next action
        """
        # For now, if the human is within a square of 2 from the robot, it has a
        # 50% chance of asking for help.
        for uuid in userLocations:
            if ((abs(self.state.currentTile.x - userLocations[uuid]["currentTile"].x) < 2
                 and abs(self.state.currentTile.y - userLocations[uuid]["currentTile"].y) < 2) or
                (abs(self.state.currentTile.x - userLocations[uuid]["nextTile"].x) < 2
                 and abs(self.state.currentTile.y - userLocations[uuid]["nextTile"].y) < 2)):
                if random.random() < 0.5:
                    nextAction = RobotAction.ASK_FOR_HELP
                    nextAction.setActionTargetuuid(uuid)
                    return nextAction

        # For now, pick NO_ACTION with likelihood 0.25, and the other legal
        # movement actions uniformly
        if random.random() < 0.25:
            nextAction = RobotAction.NO_ACTION
            nextAction.setActionTargetuuid(None)
            return nextAction
        potentialActions = []
        for action in [RobotAction.MOVE_LEFT, RobotAction.MOVE_RIGHT, RobotAction.MOVE_UP, RobotAction.MOVE_DOWN]:
            dx, dy = action.toDxDy()
            nextTile = Tile(self.state.currentTile.x+dx, self.state.currentTile.y+dy)
            # Computer collisions
            if not self.is_in_collision(nextTile, userLocations):
                action.setActionTargetuuid(None)
                potentialActions.append(action)

        if len(potentialActions) > 0:
            return random.choice(potentialActions)

        nextAction = RobotAction.NO_ACTION
        nextAction.setActionTargetuuid(None)
        return nextAction

    def getDict(self):
        currentTile = self.state.currentTile
        dx, dy = self.currentAction.toDxDy()
        tileForRendering = self.state.tileForRendering
        retval = {
            "currentTile" : {
                "x" : currentTile.x,
                "y" : currentTile.y,
            },
            "nextTile" : {
                "x" : currentTile.x+dx,
                "y" : currentTile.y+dy,
            },
            "tileForRendering" : {
                "x" : tileForRendering.x,
                "y" : tileForRendering.y,
            },
            "currentAction" : self.currentAction.name,
            "currentActionUUID" : self.currentAction.targetuuid,
            "robotHighLevelState" : self.state.robotHighLevelState.name,
        }
        animString = self.currentAction.toAnimationString()
        if animString is not None:
            retval["animation"] = animString
        return retval
