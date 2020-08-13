// Return whether or not a tile is valid for the player/robot to be in.
// includePlayer indicates whether we should treat the player as an obstacle,
// and includeRobot indicates whether we should treat the robot as an
// obstacle
function isValidTile(tile, includePlayer, includeRobot) {
  // Is the tile on screen?
  if (tile.x < 0 ||
      tile.x >= game.map.width ||
      tile.y < 0 ||
      tile.y >= game.map.height) {
      return false;
  }
  // Is the tile a wall?
  if (game.worldLayer.getTileAt(tile.x, tile.y) != null) {
    return false;
  }
  // Does the tile collide with the player?
  if (game.player &&
      includePlayer && ((
        tile.x == game.player.currentTile.x &&
        tile.y == game.player.currentTile.y
      ) || (
        tile.x == game.player.nextTile.x &&
        tile.y == game.player.nextTile.y
      ))) {
      return false;
  }
  // Does the tile collide with the robot?
  if (game.robot &&
      includeRobot && ((
        tile.x == game.robot.currentTile.x &&
        tile.y == game.robot.currentTile.y
      ) || (
        tile.x == game.robot.nextTile.x &&
        tile.y == game.robot.nextTile.y
      ))) {
      return false;
  }
  // Does the tile collide with any of the other players?
  for (otherUUID in game.otherPlayers) {
    if (((
          tile.x == game.otherPlayers[otherUUID].currentTile.x &&
          tile.y == game.otherPlayers[otherUUID].currentTile.y
        ) || (
          tile.x == game.otherPlayers[otherUUID].nextTile.x &&
          tile.y == game.otherPlayers[otherUUID].nextTile.y
        ))) {
        return false;
    }
  }
  return true;
}

// Implements the A* algorithm to search for a path from start to one of
// the goal tiles. It can take in multiple goals (in the form of an array),
// but only one for the heurstic function.
function generatePlan(startLoc, endLocs, heuristicEndLoc) {
  // Used so that each unique (x,y) pair has maximally one object in the
  // queues/sets.
  var xyToUniqueObject = {};
  xyToUniqueObject[String([startLoc.x, startLoc.y])] = {x : startLoc.x, y : startLoc.y, f : distance(heuristicEndLoc, startLoc), dist : 0, visitedFrom : null};
  for (endLoc of endLocs) {
    xyToUniqueObject[String([endLoc.x, endLoc.y])] = {x : endLoc.x, y : endLoc.y, f : null, dist : null, visitedFrom : null};
  }

  // The nodes we have yet to search through
  var openNodes = new PriorityQueue((a, b) => a.f < b.f);
  openNodes.push(xyToUniqueObject[String([startLoc.x, startLoc.y])]);

  // The nodes we have already searched through
  var closedNodes = new Set();

  var goalReachable = false;

  var currNode = null;

  while (!openNodes.isEmpty()) {
    currNode = openNodes.pop();
    closedNodes.add(currNode);
    var reachedGoal = false;
    for (endLoc of endLocs) {
      if (currNode.x == endLoc.x && currNode.y == endLoc.y) {
        goalReachable = true;
        reachedGoal = true;
        break;
      }
    }
    if (reachedGoal) {
      break;
    }

    for (dNode of [{x:0,y:1},{x:1,y:0},{x:0,y:-1},{x:-1,y:0}]) {
      var childX = currNode.x + dNode.x;
      var childY = currNode.y + dNode.y;
      if (!(String([childX, childY]) in xyToUniqueObject)) {
        xyToUniqueObject[String([childX, childY])] = {x : childX, y : childY, f : null, dist : null, visitedFrom : null};
      }
      var childNode = xyToUniqueObject[String([childX, childY])];
      // Skip invalid tiles. However, make an exception for the goal in case
      // another agent is the reason the goal is invalid
      if (!isValidTile(childNode, true, false)) {
        var isItAnEndLoc = false;
        for (endLoc of endLocs) {
          if (childNode.x == endLoc.x && childNode.y == endLoc.y) {
            isItAnEndLoc = true;
            break;
          }
        }
        if (!isItAnEndLoc) {
          continue;
        }
      }
      if (closedNodes.has(childNode)) {
        continue;
      }

      var heuristicDist = distance(heuristicEndLoc, childNode);

      // Add a small factor if the user moves the wrong direction in a hallway
      var orientationFactor = 0.0;
      var key = null;
      var currKey = String([currNode.x, currNode.y]);
      var childKey = String([currNode.x, currNode.y]);
      if (currKey in game.hallwayOrientation) {
        key = currKey;
      } else if (childKey in game.hallwayOrientation) {
        key = childKey;
      }
      if (key) {
        if (childNode.x != currNode.x) { // horizontal movement
          if (game.hallwayOrientation[key] == hallwayOrientation.VERTICAL) {
            orientationFactor += 0.1;
          }
        } else { // vertical movement
          if (game.hallwayOrientation[key] == hallwayOrientation.HORIZONTAL) {
            orientationFactor += 0.1;
          }
        }
      }
      var childDist = currNode.dist + 1 + orientationFactor;

      if (childNode.dist == null || childDist < childNode.dist) {
        childNode.dist = childDist;
        childNode.visitedFrom = currNode;
        childNode.f = childDist + heuristicDist;
        openNodes.push(childNode);
      }
    }
  }

  if (!goalReachable) {
    return [];
  }

  var plan = [];
  // currNode is already the goal
  while (currNode.x != startLoc.x || currNode.y != startLoc.y) {
    plan.unshift({x : currNode.x, y : currNode.y});
    currNode = currNode.visitedFrom;
  }
  // plan.unshift({x : startLoc.x, y : startLoc.y});

  return plan;
}

// Expands a frontier outwards from startLoc until it finds a point that satisfies
// goalConstraints. If any child violates pathConstraints while its parent does not,
// it is not considered. This is a modified version of Djikstra's algorithm.
function closestPointWithinConstraints(startLoc, goalConstraints, pathConstraints, n_iter) {
  // Used so that each unique (x,y) pair has maximally one object in the
  // queues/sets.
  var xyToUniqueObject = {};
  xyToUniqueObject[String([startLoc.x, startLoc.y])] = {x : startLoc.x, y : startLoc.y, f : 0};

  // The nodes we have yet to search through
  var openNodes = new PriorityQueue((a, b) => a.f < b.f);
  openNodes.push(xyToUniqueObject[String([startLoc.x, startLoc.y])]);

  // The nodes we have already searched through
  var closedNodes = new Set();

  var goalReachable = false;

  var currNode = null;

  var iter = -1;

  while (!openNodes.isEmpty()) {
    iter++;

    if (n_iter != null && iter > n_iter) {
      break;
    }

    currNode = openNodes.pop();
    closedNodes.add(currNode);
    goalReachable = goalConstraints(currNode);
    if (goalReachable) {
      break;
    }

    for (dNode of [{x:0,y:1},{x:1,y:0},{x:0,y:-1},{x:-1,y:0}]) {
      var childX = currNode.x + dNode.x;
      var childY = currNode.y + dNode.y;
      if (!(String([childX, childY]) in xyToUniqueObject)) {
        xyToUniqueObject[String([childX, childY])] = {x : childX, y : childY, f : null};
      }
      var childNode = xyToUniqueObject[String([childX, childY])];
      // Skip invalid tiles.
      if (pathConstraints(currNode) && !pathConstraints(childNode)) {
        continue;
      }
      if (closedNodes.has(childNode)) {
        continue;
      }
      var childDist = currNode.f + 1;

      if (childNode.dist == null || childDist < childNode.dist) {
        childNode.f = childDist;
        openNodes.push(childNode);
      }
    }
  }

  if (goalReachable) {
    console.log("iter", iter);
    return {x : currNode.x, y : currNode.y};
  } else {
    return null;
  }

}

function distance(tile0, tile1) {
  return Math.abs(tile0.x - tile1.x) + Math.abs(tile0.y - tile1.y);
}
