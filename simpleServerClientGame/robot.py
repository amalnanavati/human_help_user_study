import time
import json
import random
from enum import Enum

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

    def updateUserState(self, state):
        pass

    def update(self, userLocations):
        if self.isActionFinished and self.state.robotHighLevelState == RobotHighLevelState.AUTONOMOUS_MOTION: # and self.state.robotHighLevelState == RobotHighLevelState.AUTONMOUS_MOTION (10/27/20 - step 1) # Get the next action
            self.currentAction = self.getNextAction(userLocations)
            if self.currentAction == RobotAction.ASK_FOR_HELP:
                self.state.robotHighLevelState = RobotHighLevelState.ASKING_FOR_HELP
            #if self.currentAction == RobotAction.ASK_FOR_HELP (10/27/20)
                #self.state.robotHighLevelState = RobotHighLevelState.ASKING_FOR_HELP

            #print("Robot x {}, y {}, currentAction {}, userLocations {}".format(self.state.currentTile.x, self.state.currentTile.y, self.currentAction, userLocations))
            self.currentActionStartTime = time.time()
            self.isActionFinished = False
        elif self.isActionFinished and self.state.robotHighLevelState == RobotHighLevelState.FOLLOWING_HUMAN:
            actions = [RobotAction.MOVE_LEFT, RobotAction.MOVE_RIGHT, RobotAction.MOVE_UP, RobotAction.MOVE_DOWN]
            xDiff = self.state.currentTile.x - userLocations[self.currentAction.targetuuid]["currentTile"].x
            yDiff = self.state.currentTile.y - userLocations[self.currentAction.targetuuid]["currentTile"].y
            if(yDiff > xDiff):
                if(yDiff < 0):
                    self.currentAction = actions[3]
                    #dx, dy = actions[3].toDxDy()
                else:
                    self.currentAction = actions[2]
                    #dx, dy = actions[2].toDxDy()
            else:
                if(xDiff < 0):
                    self.currentAction = actions[1]
                    #dx, dy = actions[1].toDxDy()
                else:
                    self.currentAction = actions[0]
                    #dx, dy = actions[0].toDxDy()
            # progress = min((time.time()-self.currentActionStartTime)/Robot.robotSecPerStep, 1.0)
            # self.state.tileForRendering.x = self.state.currentTile.x + progress*dx
            # self.state.tileForRendering.y = self.state.currentTile.y + progress*dy
            # if progress >= 1.0:
            #     self.state.currentTile.x += dx
            #     self.state.currentTile.y += dy
            #     self.isActionFinished = True
            self.currentActionStartTime = time.time()
            self.isActionFinished = False

        # elif self.state.robotHighLevelState == RobotHighLevelState.FOLLOWING_HUMAN: (10/27/20)
            # create something similar to isActionInProgress and currentActionStartTime, so you can gave smooth motion
            # figure out how to follow human - get the user location from the robotActioTargetuuid and get the x difference and y difference and move one unit
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
        for uuid in userLocations:
            if ((self.state.currentTile.x - userLocations[uuid]["currentTile"].x < 2 and self.state.currentTile.y - userLocations[uuid]["currentTile"].y < 2) or
                (self.state.currentTile.x - userLocations[uuid]["nextTile"].x < 2 and self.state.currentTile.y - userLocations[uuid]["nextTile"].y < 2)):
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
            if (nextTile.x >= 1 and nextTile.x <= 10 and nextTile.y >= 1 and nextTile.y <= 10):
                is_in_collision = False
                for uuid in userLocations:
                    if((nextTile.x == userLocations[uuid]["currentTile"].x and nextTile.y == userLocations[uuid]["currentTile"].y) or
                            (nextTile.x == userLocations[uuid]["nextTile"].x and nextTile.y == userLocations[uuid]["nextTile"].y)):
                            is_in_collision = True
                            break

                for uuid in userLocations:
                    if not is_in_collision:
                        potentialActions.append(action)
                        nextAction = action
                        nextAction.setActionTargetuuid(uuid)
                        return nextAction

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
            "isHelpBubbleVisible" : (self.currentAction == RobotAction.ASK_FOR_HELP or
                                    self.state.robotHighLevelState != RobotHighLevelState.AUTONOMOUS_MOTION),
        }
        animString = self.currentAction.toAnimationString()
        if animString is not None:
            retval["animation"] = animString
        return retval
