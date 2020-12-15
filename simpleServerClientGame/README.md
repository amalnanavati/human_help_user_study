# How did the game become multiplayer?

In the real-world, we knew that the robot would be interacting with multiple people in the same room. We wanted our game to replicate this. With this new implementation, we can now see how people would interact with the robot in the presence of other humans.

# How often does communication happen?

The client sends a game state log to the server every time a player movement finishes (a player movement finishes when the animation stops rendering and the player has moved to a new tile). This message includes the current location of the player. The server uses this message to keep track of the movement of every player, so it can determine robot actions.

Every 0.02 seconds, the server sends to every client, the locations of every player, the robot’s location, and the robot’s action. The client uses this to render every player and the robot, and to display the speech bubble if the robot is interacting with that user.

# Who is in charge of rendering motion?

In `game.html`, we have code that renders player and robot movement. `game.html` only receives updates when a player has moved to a new tile and renders the animation between two adjacent tiles by itself. Game.html is also in charge of initializing all players, the robot, and the game.

# Brief description of each .py file:

- `run.py` - server that receives information from the user and sends information back
- `robot.py` - in charge of changing the movement, the state, and the next action of the robot. 
- `user.py` - keeps track of information about the users and adds/remove users
- `logger.py` - controls logging

# Future Tasks and Considerations:

- Path planning for robot (making sure the robot doesn’t run into walls and follows an optimal path)
- Generating tasks for other players (so that no two players are performing software maintenance on the same computer) 
- Putting the robot goal on the compass
- Deleting players if they have not moved in a while
- Can’t Help Button not working (causes the robot to freeze)
- Changing the robot actions from random to goal/policy directed (both movement and asking for help)
