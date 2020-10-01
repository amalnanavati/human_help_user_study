import time
import json
import random
from enum import Enum

from tile import Tile

class RobotState(object):
    def __init__(self, startTile=(5, 5)):
        self.currentTile = Tile(*startTile)
        self.tileForRendering = Tile(*startTile)

class RobotAction(Enum):
    NO_ACTION = -1 # lasts for robotMsPerStep
    MOVE_UP = 0
    MOVE_DOWN = 1
    MOVE_LEFT = 2
    MOVE_RIGHT = 3

    def toDxDy(self):
        if self == RobotAction.NO_ACTION:
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
        self.isActionFinished = True

    def updateUserState(self, state):
        pass

    def update(self, userLocations):
        if self.isActionFinished: # Get the next action
            self.currentAction = self.getNextAction(userLocations)
            #print("Robot x {}, y {}, currentAction {}, userLocations {}".format(self.state.currentTile.x, self.state.currentTile.y, self.currentAction, userLocations))
            self.currentActionStartTime = time.time()
            self.isActionFinished = False
        else: # Finish executing the current action
            if self.currentAction in [
                RobotAction.NO_ACTION,
                RobotAction.MOVE_UP,
                RobotAction.MOVE_DOWN,
                RobotAction.MOVE_LEFT,
                RobotAction.MOVE_RIGHT]:

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
        # For now, pick NO_ACTION with likelihood 0.25, and the other legal
        # movement actions uniformly
        if random.random() < 0.25:
            return RobotAction.NO_ACTION
        potentialActions = []
        for action in [RobotAction.MOVE_LEFT, RobotAction.MOVE_RIGHT, RobotAction.MOVE_UP, RobotAction.MOVE_DOWN]:
            dx, dy = action.toDxDy()
            nextTile = Tile(self.state.currentTile.x+dx, self.state.currentTile.y+dy)
            if (nextTile.x >= 1 and nextTile.x <= 10 and nextTile.y >= 1 and nextTile.y <= 10 and
                nextTile not in userLocations):
                potentialActions.append(action)

        if len(potentialActions) > 0:
            return random.choice(potentialActions)
            
        return RobotAction.NO_ACTION

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
        }
        animString = self.currentAction.toAnimationString()
        if animString is not None:
            retval["animation"] = animString
        return retval
