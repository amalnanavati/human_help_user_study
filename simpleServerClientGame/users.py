from tile import Tile

class Users(object):
    def __init__(self):
        self.states = {}
        self.lastTimestamp = {}
        # TODO (amal): remove states that haven't been updated for a while

    def addUserState(self, uuid, timestamp, state):
        self.states[uuid] = state
        self.lastTimestamp[uuid] = timestamp

    def getStatesToSend(self):
        """
        Returns the elements of the state that must be broadcast to all clients,
        including x, y, whether they are leading the robot, etc.
        """
        retval = {}
        for uuid in self.states:
            retval[uuid] = {
                "currentTile" : self.states[uuid]["player"]["currentTile"],
                "nextTile" : self.states[uuid]["player"]["nextTile"],
                "x" : self.states[uuid]["player"]["x"],
                "y" : self.states[uuid]["player"]["y"],
                "time" : self.states[uuid]["player"]["time"],
            }
            if "player_anim_key" in self.states[uuid]:
                retval[uuid]["animation"] = self.states[uuid]["player_anim_key"]
            if "player_anim_is_playing" in self.states[uuid]:
                retval[uuid]["player_anim_is_playing"] = self.states[uuid]["player_anim_is_playing"]
        return retval

    def getUserLocations(self):
        """
        Used to ensure the robot does not collide with a person
        """
        locations = set()
        for uuid in self.states:
            currentTile = self.states[uuid]["player"]["currentTile"]
            nextTile = self.states[uuid]["player"]["nextTile"]
            locations.add(Tile(currentTile["x"], currentTile["y"]))
            locations.add(Tile(nextTile["x"], nextTile["y"]))
        return locations

    def removeUser(self, uuid):
        if uuid in self.states:
            del self.states[uuid]
        if uuid in self.lastTimestamp:
            del self.lastTimestamp[uuid]

    def getJSON(self):
        """
        Generate the JSON that will be broadcast to all users
        """
        pass
