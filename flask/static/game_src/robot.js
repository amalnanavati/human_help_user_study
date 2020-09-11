const robotMsPerStep = 350;

const robotColor = 0x00ffff;
const robotColorStr = '#0077ff';

const queryAskingDistance = 3; // tiles, in the l-infinity norm
const moveTowardsHumanDistance = 8; // tiles, in the l-infinity norm
const numTimesToTryAskingForHelp = 1;

const robotToHumanDistance = 2;

const robotState = {
  OFFSCREEN: 0,
  APPROACH_HUMAN: 1,
  WALK_PAST_HUMAN: 2, // walks in the opposite direction of the human, and then transitions to offscreen
  STATIONARY: 3,
  LEAVE_SCREEN: 4, // walks off the screen
  GO_TOWARDS_GOAL: 5, // goes towards the goal until its offscreen
}

function createRobot(scene) {
  scene.game.robot = scene.physics.add.sprite(scene.game.config.width/2, scene.game.config.width/2, 'robot');
  scene.game.robot.setDepth(5);
  scene.game.robot.currentTile = {x : scene.game.tasks.robot_offscreen_location.x, y : scene.game.tasks.robot_offscreen_location.y};
  scene.game.robot.previousTile = scene.game.robot.currentTile;
  scene.game.robot.goalTile = scene.game.robot.currentTile;
  scene.game.robot.plan = null;
  gameXY = tileToGameXY(scene.game.robot.currentTile);
  scene.game.robot.x = gameXY.x;
  scene.game.robot.y = gameXY.y;
  scene.game.robot.currentState = robotState.OFFSCREEN;
  // scene.game.hasRobotStateChangedThisUpdate = false;
  scene.game.robot.isBeingLed = false;
  scene.game.robot.taskPlan = [];
  scene.game.robot.currentActionI = 0;
  scene.game.robot.actionInProgress = false;

  // Create the player animations
  scene.anims.create({
      key: 'robotDown',
      frames: scene.anims.generateFrameNumbers('robot', {start: 0, end: 3}),
      frameRate: 5,
      repeat: -1
  });
  scene.anims.create({
      key: 'robotUp',
      frames: scene.anims.generateFrameNumbers('robot', {start: 4, end: 7}),
      frameRate: 5,
      repeat: -1
  });
  scene.anims.create({
      key: 'robotLeft',
      frames: scene.anims.generateFrameNumbers('robot', {start: 8, end: 11}),
      frameRate: 5,
      repeat: -1
  });
  scene.anims.create({
      key: 'robotRight',
      frames: scene.anims.generateFrameNumbers('robot', {start: 12, end: 15}),
      frameRate: 5,
      repeat: -1
  });
  scene.game.robot.anims.play('robotDown', true);
  scene.game.robot.anims.stop();

  // Initialize the observation
  scene.game.robot.observation = {
    human_busyness_obs: 6,
    // human_num_recent_times_did_not_help_obs: 0,
    robot_did_ask_obs: [false, false, false, false, false],
    robot_room_obs: "obs_wrong_room",
  }

  scene.game.robot.numTimesHelped = 0;
}

function createRobotHelpBubble(scene) {
  var sampleQuestion = "Excuse me. Can you tell me if I'm in front of the Lounge?";
  scene.game.robot.helpBubble = new SpeechBubble(scene, 225, 300, 300, sampleQuestion, [
    {
      text : "Yes",
      rowI: 0,
      callbackFunction : () => console.log("Yes button clicked"),
    },
    {
      text : "No",
      rowI: 1,
      callbackFunction : () => console.log("No button clicked"),
    },
  ]);
  scene.game.robot.helpBubble.setVisible(false);
}

function setRobotActionInProgress(scene, val) {
  // console.log("setRobotActionInProgress", val);
  if (scene.game.robot.actionInProgress && !val) {
    // console.log("action in progress transition");
    // If you have not updated the observation for the last action yet, do that
    // if (scene.game.robot.currentActionI == 0) {
    //   if (!tutorial && !("hasQueriedServer" in scene.game.tasks.robotActions[scene.game.robot.currentActionI] && scene.game.tasks.robotActions[scene.game.robot.currentActionI].hasQueriedServer)) {
    //     queryPolicyServer(scene, scene.game.robot.currentActionI);
    //   }
    // } else {
    if (!tutorial && !("hasUpdatedObservation" in scene.game.tasks.robotActions[scene.game.robot.currentActionI].robotAction)) {
      updateObservation(scene, scene.game.tasks.robotActions[scene.game.robot.currentActionI].robotAction.query == "leadMe", false); // Robot asked, human ignored
    }
    // }
    scene.game.robot.currentActionI++;
  }
  scene.game.robot.actionInProgress = val;
}

function getOffScreenTileInDirectionOfHumanMotion(scene) {

  // Get the predicted human plan to the goal
  getCurrentTaskPlan(scene);
  // Get the point of the plan that goes off screen
  var robotSpawnNear = {
    x : scene.game.player.currentTile.x,
    y : scene.game.player.currentTile.y,
  };
  for (planPoint of scene.game.player.taskPlan) {
    robotSpawnNear.x = planPoint.x;
    robotSpawnNear.y = planPoint.y;
    // If the plan point goes off the visible screen
    if (isOffCamera(scene, planPoint)) {
        break;
    }
  }
  console.log("robotSpawnNear", robotSpawnNear);

  // The point must be the closest point to
  // robotSpawnNear (or the robot's currentTile) that is also:
  // 1) > cameraPadding units off-screen, and 2) is in a Hallway
  function goalConstraints(tile) {
    var key = String([tile.x, tile.y]);
    var isInHallway = (key in scene.game.xyToSemanticLabels &&
                       scene.game.xyToSemanticLabels[key].has("Hallway"));
    return isOffCamera(scene, tile) && isInHallway;
  }
  function pathConstraints(tile) {
    var notWall = scene.game.worldLayer.getTileAt(tile.x, tile.y) == null;
    return notWall;// && isOffCamera(scene, tile);
  }

  return closestPointWithinConstraints(robotSpawnNear, goalConstraints, pathConstraints, 40*screenSizeX*screenSizeY);
}

function getOffScreenTileInOppositeDirectionOfHumanMotion(scene) {

  // Get the predicted human plan to the goal
  getCurrentTaskPlan(scene);
  // Get the point of the plan that goes off screen
  var robotSpawnNear = {
    x : scene.game.player.currentTile.x,
    y : scene.game.player.currentTile.y,
  };
  for (planPoint of scene.game.player.taskPlan) {
    robotSpawnNear.x = planPoint.x;
    robotSpawnNear.y = planPoint.y;
    // If the plan point goes off the visible screen
    if (isOffCamera(scene, planPoint)) {
        break;
    }
  }

  // Get the camera bounds
  var cameraBounds = getCameraBounds(scene);

  var robotSpawnNearLeft = robotSpawnNear.x < cameraBounds.left - cameraPadding;
  var robotSpawnNearRight = robotSpawnNear.x >= cameraBounds.right + cameraPadding;
  var robotSpawnNearUp = robotSpawnNear.y < cameraBounds.up - cameraPadding;
  var robotSpawnNearDown = robotSpawnNear.y >= cameraBounds.down + cameraPadding;
  if (!(robotSpawnNearLeft || robotSpawnNearRight || robotSpawnNearUp || robotSpawnNearDown)) {
    robotSpawnNearLeft = scene.game.robot.tileAtBeginningOfWalkPast.x < scene.game.player.currentTile.x;
    robotSpawnNearRight = scene.game.robot.tileAtBeginningOfWalkPast.x > scene.game.player.currentTile.x;
    robotSpawnNearUp = scene.game.robot.tileAtBeginningOfWalkPast.y < scene.game.player.currentTile.y;
    robotSpawnNearDown = scene.game.robot.tileAtBeginningOfWalkPast.y > scene.game.player.currentTile.y;
  }
  // The robot spawn point must be:
  // 1) > cameraPadding units off-screen, 2) is in a Hallway, and
  // 3) in the opposite direction of robotSpawnNear
  function goalConstraints(tile) {
    var tileLeft = tile.x < cameraBounds.left - cameraPadding;
    var tileRight = tile.x >= cameraBounds.right + cameraPadding;
    var tileUp = tile.y < cameraBounds.up - cameraPadding;
    var tileDown = tile.y >= cameraBounds.down + cameraPadding;

    var isOffCamera =  tileLeft || tileRight || tileUp || tileDown;

    var key = String([tile.x, tile.y]);
    var isInHallway = (key in scene.game.xyToSemanticLabels &&
                       scene.game.xyToSemanticLabels[key].has("Hallway"));

    var isInOppositeDirection = !(tileLeft && robotSpawnNearLeft) && !(tileRight && robotSpawnNearRight) && !(tileUp && robotSpawnNearUp) && !(tileDown && robotSpawnNearDown);

    return isOffCamera && isInHallway && isInOppositeDirection;
  }
  function pathConstraints(tile) {
    var notWall = scene.game.worldLayer.getTileAt(tile.x, tile.y) == null;
    return notWall;
  }
  return closestPointWithinConstraints(scene.game.player.currentTile/*scene.game.robot.currentTile*/, goalConstraints, pathConstraints, 40*screenSizeX*screenSizeY);
}

function getOffScreenTile(scene) {

  // The point must be the closest point to
  // robot current position (or the robot's currentTile) that is also:
  // 1) > cameraPadding units off-screen, and 2) is in a Hallway
  function goalConstraints(tile) {
    var key = String([tile.x, tile.y]);
    var isInHallway = (key in scene.game.xyToSemanticLabels &&
                       scene.game.xyToSemanticLabels[key].has("Hallway"));
    return isOffCamera(scene, tile) && isInHallway;
  }
  function pathConstraints(tile) {
    var notWall = scene.game.worldLayer.getTileAt(tile.x, tile.y) == null;
    return notWall;
  }

  return closestPointWithinConstraints(scene.game.robot.currentTile, goalConstraints, pathConstraints, 40*screenSizeX*screenSizeY);
}

function logClick(scene, hitArea, x, y, button) {
  if (!load) {
    logData(tutorial ? logTutorialStateEndpoint : logGameStateEndpoint, getGameState(scene, eventType.CLICK, {
      buttonName : button.text,
      x : button.x - button.width*button.originX + x,
      y : button.y - button.height*button.originY + y,
    }));
  }
}

var helpRequestButtonCallbacks = {
  // "amIHere" : {
  //   "Yes" : function(scene) {
  //     scene.game.robot.helpBubble.setText("Thank you.");
  //     scene.game.robot.helpBubble.setButtons([]);
  //     scene.game.robot.currentState = robotState.WALK_PAST_HUMAN;
  //     setRobotActionInProgress(scene, false);
  //     if (scene.game.minimap) destroyRobotGoalRect(scene);
  //   },
  //   "No" : function(scene) {
  //     scene.game.robot.helpBubble.setText("Thank you.");
  //     scene.game.robot.helpBubble.setButtons([]);
  //     scene.game.robot.currentState = robotState.WALK_PAST_HUMAN;
  //     setRobotActionInProgress(scene, false);
  //     if (scene.game.minimap) destroyRobotGoalRect(scene);
  //   },
  //   // "Don't Know" : function(scene) {
  //   //   scene.game.robot.helpBubble.setText("Thank you.");
  //   //   scene.game.robot.helpBubble.setButtons([]);
  //   //   scene.game.robot.currentState = robotState.WALK_PAST_HUMAN;
  //   //   setRobotActionInProgress(scene, false);
  //   //   if (scene.game.minimap) destroyRobotGoalRect(scene);
  //   // },
  //   "Can't Help" : function(scene) {
  //     scene.game.robot.helpBubble.setText("That's okay.");
  //     scene.game.robot.helpBubble.setButtons([]);
  //     scene.game.robot.currentState = robotState.WALK_PAST_HUMAN;
  //     setRobotActionInProgress(scene, false);
  //     if (scene.game.minimap) destroyRobotGoalRect(scene);
  //   },
  // },
  "leadMe" : {
    "Yes" : function(scene) {
      setHelpBubbleToLeadMe(scene, true);
      scene.game.robot.isBeingLed = true;
      getCurrentPlanToRobotGoal(scene);
      scene.game.robot.currentState = robotState.APPROACH_HUMAN;
    },
    "Can't Help" : function(scene) {
      scene.game.robot.helpBubble.setText("That's okay.");
      scene.game.robot.helpBubble.setButtons([]);
      scene.game.robot.currentState = robotState.WALK_PAST_HUMAN;
      if (!tutorial && !("hasUpdatedObservation" in scene.game.tasks.robotActions[scene.game.robot.currentActionI].robotAction)) {
        updateObservation(scene, true, false); // Robot asked, human said no
      }
      setRobotActionInProgress(scene, false);
      if (scene.game.minimap) destroyRobotGoalRect(scene);
    },
    "Stop Following" : function(scene) {
      scene.game.robot.helpBubble.setText("Thank you.");
      scene.game.robot.helpBubble.setButtons([]);
      scene.game.robot.isBeingLed = false;
      if (scene.game.robot.taskPlan.length <= 8) {
        scene.game.robot.numTimesHelped += 1;
        if (!tutorial && !("hasUpdatedObservation" in scene.game.tasks.robotActions[scene.game.robot.currentActionI].robotAction)) {
          updateObservation(scene, true, true); // Robot asked, human helped
        }
      } else {
        if (!tutorial && !("hasUpdatedObservation" in scene.game.tasks.robotActions[scene.game.robot.currentActionI].robotAction)) {
          updateObservation(scene, true, false); // Robot asked, human inaccurately / mistakenly
        }
      }
      scene.game.robot.taskPlan = [];
      var goalSemanticLabel = scene.game.tasks.robotActions[scene.game.robot.currentActionI].robotAction.targetSemanticLabel + pointOfInterestString + "1";
      var goalLocs = scene.game.semanticLabelsToXY[goalSemanticLabel];
      scene.game.robot.goalTile = goalLocs[Math.floor(Math.random() * goalLocs.length)]
      if (scene.game.robot.movementTimer != null) {
        // If we're in the middle of a movement, set the currentTile to the tile it is going towards
        if (scene.game.robot.plan != null && scene.game.robot.plan.length > 0) {
          scene.game.robot.currentTile = scene.game.robot.plan[0];
        }
        scene.game.robot.movementTimer.destroy();
        scene.game.robot.movementTimer = null;
      }
      scene.game.robot.plan = generatePlan(scene.game.robot.currentTile, [scene.game.robot.goalTile], scene.game.robot.goalTile, isValidTile);
      scene.game.robot.currentState = robotState.GO_TOWARDS_GOAL; // TODO (amal): might the user expect the robot to go into the target room, instead of just walking away?
      setRobotActionInProgress(scene, false);
      if (scene.game.minimap) destroyRobotGoalRect(scene);
    },
  },
}

function setHelpBubbleToAmIHere(scene) {
  if (!load) logData(tutorial ? logTutorialStateEndpoint : logGameStateEndpoint, getGameState(scene, eventType.SET_HELP_BUBBLE, {helpBubbleType: "amIHere"}));
  scene.game.robot.helpBubble.setText("Excuse me. Am I in front of " + scene.game.tasks.robotActions[scene.game.robot.currentActionI].robotAction.targetStr + " (see map below)?");
  scene.game.robot.helpBubble.setButtons([
    {
      text : "Yes",
      rowI: 0,
      callbackFunction : function(hitArea, x, y) {
        logClick(scene, hitArea, x, y, this);
        helpRequestButtonCallbacks["amIHere"][this.text](scene);
      },
    },
    {
      text : "No",
      rowI: 0,
      callbackFunction : function(hitArea, x, y) {
        logClick(scene, hitArea, x, y, this);
        helpRequestButtonCallbacks["amIHere"][this.text](scene);
      },
    },
    /*{
      text : "Don't Know",
      rowI: 1,
      callbackFunction : function(hitArea, x, y) {
        logClick(scene, hitArea, x, y, this);
        helpRequestButtonCallbacks["amIHere"][this.text](scene);
      },
    },*/
    {
      text : "Can't Help",
      rowI: 1,
      callbackFunction : function(hitArea, x, y) {
        logClick(scene, hitArea, x, y, this);
        helpRequestButtonCallbacks["amIHere"][this.text](scene);
      },
    },
  ]);
  if (scene.game.minimap) {
    var robotGoalSemanticLabel = scene.game.tasks.robotActions[scene.game.robot.currentActionI].robotAction.targetSemanticLabel;
    var robotGoalRect = scene.game.semanticLabelToRoomRectBounds[robotGoalSemanticLabel];
    if (scene.game.minimap) createRobotGoalRect(scene, robotGoalRect, robotGoalSemanticLabel);
  }
}

function setHelpBubbleToLeadMe(scene, hasSaidYes) {
  if (!load) logData(tutorial ? logTutorialStateEndpoint : logGameStateEndpoint, getGameState(scene, eventType.SET_HELP_BUBBLE, {helpBubbleType: "leadMe", hasSaidYes: hasSaidYes}));
  if (!hasSaidYes) {
    scene.game.robot.helpBubble.setText("Excuse me. Can you lead me towards " + scene.game.tasks.robotActions[scene.game.robot.currentActionI].robotAction.targetStr + "?");
    scene.game.robot.helpBubble.setButtons([
      {
        text : "Yes",
        rowI: 0,
        callbackFunction : function(hitArea, x, y) {
          logClick(scene, hitArea, x, y, this);
          helpRequestButtonCallbacks["leadMe"][this.text](scene);
        },
      },
      {
        text : "Can't Help",
        rowI: 0,
        callbackFunction : function(hitArea, x, y) {
          logClick(scene, hitArea, x, y, this);
          helpRequestButtonCallbacks["leadMe"][this.text](scene);
        },
      },
    ]);
    console.log("leadMe", scene.game.tasks.robotActions[scene.game.robot.currentActionI].robotAction.targetSemanticLabel, scene.game.semanticLabelToRoomRectBounds, scene.game.semanticLabelToRoomRectBounds[scene.game.tasks.robotActions[scene.game.robot.currentActionI].robotAction.targetSemanticLabel]);
    if (scene.game.minimap) {
      var robotGoalSemanticLabel = scene.game.tasks.robotActions[scene.game.robot.currentActionI].robotAction.targetSemanticLabel;
      var robotGoalRect = scene.game.semanticLabelToRoomRectBounds[robotGoalSemanticLabel];
      createRobotGoalRect(scene, robotGoalRect, robotGoalSemanticLabel);
    }
  } else {
    scene.game.robot.helpBubble.setText("Thank you for leading me towards " + scene.game.tasks.robotActions[scene.game.robot.currentActionI].robotAction.targetStr + ". Tell me when I should stop following you.");
    scene.game.robot.helpBubble.setButtons([
      {
        text : "Stop Following",
        rowI: 0,
        callbackFunction : function(hitArea, x, y) {
          logClick(scene, hitArea, x, y, this);
          helpRequestButtonCallbacks["leadMe"][this.text](scene);
        },
      },
    ]);
  }
}

function sendNewUserMsgToPolicyServer(scene) {
  var url = basePolicyURL + "new_user";

  var data = {
    uuid: parseInt(uuid),
    gid: parseInt(gid),
    robot_action_i: 0,
  }
  // console.log("Send ", data)
  $.ajax({
    type : "POST",
    url : url,
    data: JSON.stringify(data, null, '\t'),
    contentType: 'application/json;charset=UTF-8',
    success: function(received_data, status) {
        received_data = JSON.parse(received_data);
        if ("action" in received_data) {
          if (received_data["action"] == "ask") {
            scene.game.tasks.robotActions[0].robotAction.query = "leadMe";
            console.log("got ask scene.game.tasks.robotActions", scene.game.tasks.robotActions);
          } else if (received_data["action"] == "walk_past") {
            scene.game.tasks.robotActions[0].robotAction.query = "walkPast";
          } else {
            console.log("Received unknown action from policy server", received_data["action"]);
          }
          scene.game.tasks.robotActions[0].hasQueriedServer = true;
          console.log("SUCCESS: got action from server", received_data["action"]);
        }
    },
    error: function(received_data, status) {
        // NOTE: For now I'm not going to log the number of errors and stuff for non-logging data because I'm hoping that the internet error will happen for the policy and logging equivalently
        // Set the obs to the right busyness, so that when the server is queried with an obs, it is correct
        randomlyAssignBusyness(scene, scene.game.tasks.robotActions[0].afterHumanTaskIndex+1);
        var busyness_float = scene.game.tasks.tasks[scene.game.tasks.robotActions[0].afterHumanTaskIndex+1].busyness;
        scene.game.robot.observation.human_busyness_obs = (busyness_float/0.4*(num_busyness-1))+1;

        scene.game.tasks.robotActions[0].hasQueriedServer = false;
    }
  });
  scene.game.tasks.robotActions[0].hasQueriedServer = true;
}

function queryPolicyServer(scene, robotActionI) {
  var url = basePolicyURL + "received_obs";

  var data = {
    uuid: parseInt(uuid),
    gid: parseInt(gid),
    obs: scene.game.robot.observation,
    robot_action_i: robotActionI,
  }
  console.log("queryPolicyServer ", data)
  $.ajax({
    type : "POST",
    url : url,
    data: JSON.stringify(data, null, '\t'),
    contentType: 'application/json;charset=UTF-8',
    success: function(received_data, status) {
        received_data = JSON.parse(received_data);
        if ("action" in received_data) {
          if (received_data["action"] == "ask") {
            console.log("got ask robotActionI", robotActionI);
            if (robotActionI < scene.game.tasks.robotActions.length) {
              scene.game.tasks.robotActions[robotActionI].robotAction.query = "leadMe";
            }
          } else if (received_data["action"] == "walk_past") {
            if (robotActionI < scene.game.tasks.robotActions.length) {
              scene.game.tasks.robotActions[robotActionI].robotAction.query = "walkPast";
            }
          } else {
            console.log("Received unknown action from policy server", received_data["action"]);
          }
          if (robotActionI < scene.game.tasks.robotActions.length) {
            scene.game.tasks.robotActions[robotActionI].hasQueriedServer = true;
          }
          console.log("SUCCESS: got action from server", received_data["action"]);
        }
    },
    error: function(received_data, status) {
        // NOTE: For now I'm not going to log the number of errors and stuff for non-logging data because I'm hoping that the internet error will happen for the policy and logging equivalently
        if (robotActionI < scene.game.tasks.robotActions.length) {
          scene.game.tasks.robotActions[robotActionI].hasQueriedServer = false; // Hopefully this doesn't extend beyond one taskI
        }
    }
  });
  if (robotActionI < scene.game.tasks.robotActions.length) {
    scene.game.tasks.robotActions[robotActionI].hasQueriedServer = true;
  }
}

// NOTE: This function *MUST* be called BEFORE currentActionI has been incremented
function updateObservation(scene, didRobotAsk, didHumanHelp=false) {
  // Update busyness
  if (scene.game.robot.currentActionI+1 < scene.game.tasks.robotActions.length) {
    var nextTaskIWhenTheRobotWillAppear = scene.game.tasks.robotActions[scene.game.robot.currentActionI+1].afterHumanTaskIndex+1;
    if (nextTaskIWhenTheRobotWillAppear < scene.game.tasks.tasks.length) {
      randomlyAssignBusyness(scene, nextTaskIWhenTheRobotWillAppear);
      var busyness_float = scene.game.tasks.tasks[nextTaskIWhenTheRobotWillAppear].busyness;
      scene.game.robot.observation.human_busyness_obs = Math.round((busyness_float/0.4*(num_busyness-1))+1);
      console.log("updateObservation", busyness_float, scene.game.robot.observation.human_busyness_obs);
    } // Otherwise, keep the observed busyness the same, because we won't execute the action anyway
  }

  // // Update human_num_recent_times_did_not_help_obs
  // if (didRobotAsk) {
  //   if (didHumanHelp) {
  //     scene.game.robot.observation.human_num_recent_times_did_not_help_obs = 0;
  //   } else {
  //     scene.game.robot.observation.human_num_recent_times_did_not_help_obs += 1;
  //   }
  // }

  // Add an item to the end of robot_did_ask_obs and remove it from the beginning
  scene.game.robot.observation.robot_did_ask_obs.push(didRobotAsk);
  scene.game.robot.observation.robot_did_ask_obs.shift();

  // Simulate randomly picking a room
  if (didHumanHelp) {
    scene.game.robot.observation.robot_room_obs = "obs_human_helped";
  } else {
    if (Math.random() <= 1.0/numRooms) {
      scene.game.robot.observation.robot_room_obs = "obs_correct_room";
    } else {
      scene.game.robot.observation.robot_room_obs = "obs_wrong_room";
    }
  }

  // NOTE: This function *MUST* be called BEFORE currentActionI has been incremented
  // Query the policy server for the next action
  // if (scene.game.robot.currentActionI+1 < scene.game.tasks.robotActions.length) {
  queryPolicyServer(scene, scene.game.robot.currentActionI+1);
  // }

  scene.game.tasks.robotActions[scene.game.robot.currentActionI].robotAction.hasUpdatedObservation = true;
}

function initiateRobotActionIfApplicable(scene) {
  // Initiate the robot action, if applicable
  if (scene.game.robot.currentState == playerState.NAVIGATION_TASK) {
    // console.log("player navigation");
    if (scene.game.robot.currentActionI < scene.game.tasks.robotActions.length) {
      // console.log("robot action length fine");
      var robotAction = scene.game.tasks.robotActions[scene.game.robot.currentActionI];
      // Has the human completed the precondition task?
      if (scene.game.player.taskI == robotAction.afterHumanTaskIndex + 1) {
        if (!scene.game.robot.actionInProgress && scene.game.robot.currentState == robotState.OFFSCREEN) {
          // console.log("robot offscreen");
          var requiredDistanceToGoal = Math.ceil(scene.game.player.currentTaskDistance*(1.0-robotAction.humanDistanceProportionToNextGoal));
          var oldTaskPlanDistanceFromRequiredDistance = scene.game.player.taskPlan.length - requiredDistanceToGoal;
          // Has the player traversed enough distance to justify recalculating the plan?
          // console.log("after correct player task", scene.game.player.currentTaskDistance, requiredDistanceToGoal, scene.game.player.elapsedDistanceSinceComputingTaskPlan, oldTaskPlanDistanceFromRequiredDistance);
          if (scene.game.player.elapsedDistanceSinceComputingTaskPlan >= Math.floor(oldTaskPlanDistanceFromRequiredDistance*0.5)) {
            getCurrentTaskPlan(scene);
            var distanceProportionToNextGoal = 1.0 - scene.game.player.taskPlan.length/scene.game.player.currentTaskDistance;
            console.log("distanceProportionToNextGoal", distanceProportionToNextGoal, robotAction.humanDistanceProportionToNextGoal);
            // Has the human traversed enough distance to trigger the robot action?
            if (distanceProportionToNextGoal >= robotAction.humanDistanceProportionToNextGoal) {
              console.log("robot appears, distance", scene.game.player.taskPlan.length, "taskI", scene.game.player.taskI);
              setRobotActionInProgress(scene, true);

              var robotSpawnTile = getOffScreenTileInDirectionOfHumanMotion(scene);
              console.log("robotSpawnTile", robotSpawnTile);
              if (scene.game.robot.movementTimer) {
                scene.game.robot.movementTimer.destroy();
                scene.game.robot.movementTimer = null;
              }
              scene.game.robot.currentState = robotState.STATIONARY;

              // Spawn the robot there
              scene.game.robot.currentTile = robotSpawnTile;
              scene.game.numTimesAskedForHelp = -1;

              // Change the helpBubbleText
              if (scene.game.tasks.robotActions[scene.game.robot.currentActionI].robotAction.query == "amIHere") {
                setHelpBubbleToAmIHere(scene);
              } else if (scene.game.tasks.robotActions[scene.game.robot.currentActionI].robotAction.query == "leadMe") {
                setHelpBubbleToLeadMe(scene, false);
              } /*else if (game.tasks.robotActions[game.robot.currentActionI].robotAction.query == "walkPast") {
                game.robot.tileAtBeginningOfWalkPast = robotSpawnTile;
              }*/
            }
          }
        }
      }
    }
  }
}

function renderRobotMovementAnimation(scene) {
  var p = scene.game.robot.movementTimer == null ? 0 : scene.game.robot.movementTimer.getOverallProgress();
  var gameXY = tileToGameXY({
    x : scene.game.robot.currentTile.x * (1-p) + (scene.game.robot.plan == null || scene.game.robot.plan.length == 0 ? scene.game.robot.currentTile.x * p : scene.game.robot.plan[0].x * p),
    y : scene.game.robot.currentTile.y * (1-p) + (scene.game.robot.plan == null || scene.game.robot.plan.length == 0 ? scene.game.robot.currentTile.y * p : scene.game.robot.plan[0].y * p),
  });
  scene.game.robot.x = gameXY.x;
  scene.game.robot.y = gameXY.y;
  if (scene.game.minimap) {
    if (!isOffCamera(scene, scene.game.robot.currentTile, 0) && scene.game.robot.currentTile.x >= 0 && scene.game.robot.currentTile.y >= 0) {
      scene.game.minimap.robotDot.setVisible(true);
      scene.game.minimap.robotDot.x = scene.game.minimap.x + scene.game.robot.x*scene.game.minimap.scale;
      scene.game.minimap.robotDot.y = scene.game.minimap.y + scene.game.robot.y*scene.game.minimap.scale;
    } else {
      scene.game.minimap.robotDot.setVisible(false);
    }
  }
  scene.game.robot.helpBubble.setPosition(scene.game.robot.x + scene.game.robot.width / 3, scene.game.robot.y - scene.game.robot.height/3);
  if (scene.game.robot.movementTimer == null) {
    scene.game.robot.previousTile = scene.game.robot.currentTile;
  }
  if (scene.game.robot.movementTimer != null && scene.game.robot.movementTimer.getOverallProgress() == 1.0) {
    if (scene.game.robot.plan != null && scene.game.robot.plan.length > 0) {
      scene.game.robot.currentTile = scene.game.robot.plan[0];
    }
    scene.game.robot.plan.splice(0,1);
    scene.game.robot.movementTimer.destroy();
    scene.game.robot.movementTimer = null;
    if (!load) {
      // Log the game state
      logData(tutorial ? logTutorialStateEndpoint : logGameStateEndpoint, getGameState(scene, eventType.MOVEMENT));
    }
  }
}

function executeRobotAction(scene) {
  if (scene.game.tasks.robotActions[scene.game.robot.currentActionI].robotAction.query == "amIHere" ||
      scene.game.tasks.robotActions[scene.game.robot.currentActionI].robotAction.query == "leadMe") {
    // console.log("executeRobotAction", scene.game.robot.isBeingLed, scene.game.robot.movementTimer, scene.game.robot.actionInProgress);

    if (!scene.game.robot.isBeingLed) {
      // If the human is far enough from you to try moving towards
      // them again, do so
      if (scene.game.numTimesAskedForHelp == -1 || distance(scene.game.robot.currentTile, scene.game.player.currentTile) >= moveTowardsHumanDistance) {
        setHelpBubbleVisible(scene, false);
        if (scene.game.robot.currentState == robotState.STATIONARY) {
          scene.game.numTimesAskedForHelp += 1;
        }
        if (scene.game.numTimesAskedForHelp >= numTimesToTryAskingForHelp) {
          console.log("human ignored the robot");
          if (!tutorial && !("hasUpdatedObservation" in scene.game.tasks.robotActions[scene.game.robot.currentActionI].robotAction)) {
            updateObservation(scene, true, false); // Robot asked, human ignored
          }
          setHelpBubbleVisible(scene, false);
          scene.game.robot.currentState = robotState.WALK_PAST_HUMAN;
          setRobotActionInProgress(scene, false);
          if (scene.game.minimap) destroyRobotGoalRect(scene);
        } else {
          scene.game.robot.currentState = robotState.APPROACH_HUMAN;
        }
      }

      // If the human is too far away from you to answer the query,
      // make the query invisible.
      // if (distance(game.robot.currentTile, game.player.currentTile) >= queryAnsweringDistance) {
      //     setHelpBubbleVisible(false);
      // }

      // When you are close enough to the human, display the query
      // and stop moving
      if (distance(scene.game.robot.currentTile, scene.game.player.currentTile) <= queryAskingDistance) {
        setHelpBubbleVisible(scene, true);
        scene.game.robot.currentState = robotState.STATIONARY;
      }
    }
  } else if (scene.game.tasks.robotActions[scene.game.robot.currentActionI].robotAction.query == "walkPast") {
    // console.log("executeRobotAction walkPast", scene.game.robot.currentState);
    if (scene.game.robot.currentState == robotState.OFFSCREEN) {
      if (!tutorial && !("hasUpdatedObservation" in scene.game.tasks.robotActions[scene.game.robot.currentActionI].robotAction)) {
        updateObservation(scene, false); // robot did not ask
      }
      setRobotActionInProgress(scene, false);
    } else {
      scene.game.robot.currentState = robotState.WALK_PAST_HUMAN;
    }
  }
}

function setHelpBubbleVisible(scene, visible) {
  // console.log("setHelpBubbleVisible", visible);
  scene.game.robot.helpBubble.setVisible(visible);
  if (scene.game.minimap) setRobotGoalRectVisible(scene, visible);
}

function transitionRobotState(scene) {
  if (scene.game.robot.currentState != scene.game.robot.previousState) {
    if (!load) logData(tutorial ? logTutorialStateEndpoint : logGameStateEndpoint, getGameState(scene, eventType.ROBOT_STATE_CHANGE));
  }
  var robotStateToEvaluate = scene.game.robot.currentState;
  switch(robotStateToEvaluate) {
    case robotState.OFFSCREEN:
      scene.game.robot.tileAtBeginningOfWalkPast = null;
      scene.game.robot.currentTile = {x : scene.game.tasks.robot_offscreen_location.x, y : scene.game.tasks.robot_offscreen_location.y};
      scene.game.robot.goalTile = scene.game.robot.currentTile;
      scene.game.robot.plan = null;
      break;
    case robotState.APPROACH_HUMAN:
      scene.game.robot.tileAtBeginningOfWalkPast = null;
      if (scene.game.robot.plan == null || scene.game.robot.plan.length == 0 || scene.game.robot.goalTile == null || distance(scene.game.robot.goalTile, scene.game.player.currentTile) != robotToHumanDistance) {
        scene.game.robot.goalTile = scene.game.player.currentTile;
        scene.game.robot.plan = generatePlan(scene.game.robot.currentTile, [scene.game.robot.goalTile], scene.game.robot.goalTile);
        // Have the robot stay 1 unit away from the human
        if (scene.game.robot.plan != null && scene.game.robot.plan.length > robotToHumanDistance) {
          scene.game.robot.goalTile = scene.game.robot.plan[scene.game.robot.plan.length - robotToHumanDistance - 1];
          scene.game.robot.plan.splice(scene.game.robot.plan.length - robotToHumanDistance, robotToHumanDistance);
        } else if (scene.game.robot.plan != null && scene.game.robot.plan.length == robotToHumanDistance) {
          // The robot should stay stationary
          scene.game.robot.goalTile = scene.game.robot.currentTile;
          scene.game.robot.plan = null;
        } else { // the robot is too close to the human
          // Find a point that is a distance of robotToHumanDistance away from the human
          function goalConstraints(tile) {
            var awayFromHuman = distance(tile, scene.game.player.currentTile) >= robotToHumanDistance;
            var notWall = game.worldLayer.getTileAt(tile.x, tile.y) == null;
            return awayFromHuman && notWall;
          }
          function pathConstraints(tile) {
            return true;
          }

          var goalTile =  closestPointWithinConstraints(scene.game.robot.currentTile, goalConstraints, pathConstraints, 20*screenSizeX*screenSizeY);
          if (goalTile != null) {
            scene.game.robot.goalTile = goalTile;
            scene.game.robot.plan = generatePlan(scene.game.robot.currentTile, [scene.game.robot.goalTile], scene.game.robot.goalTile);
          }
        }
      }
      break;
    case robotState.WALK_PAST_HUMAN:
      // console.log("WALK_PAST_HUMAN", scene.game.numTimesRobotOnScreen, isOffCamera(scene, scene.game.robot.currentTile));
      // If we just transitioned to WALK_PAST, set numTimesRobotOnScreen to 0
      if (scene.game.robot.previousState != robotState.WALK_PAST_HUMAN) {
        scene.game.numTimesRobotOnScreen = 0;
      }
      if (isOffCamera(scene, scene.game.robot.currentTile) && scene.game.numTimesRobotOnScreen > 0) {
        setHelpBubbleVisible(scene, false);
        // game.hasRobotStateChangedThisUpdate = false;
        scene.game.robot.currentState = robotState.OFFSCREEN;
      } else {

        if (!isOffCamera(scene, scene.game.robot.currentTile)) {
          scene.game.numTimesRobotOnScreen++;
        }

        if (scene.game.robot.tileAtBeginningOfWalkPast == null) {
          scene.game.robot.tileAtBeginningOfWalkPast = scene.game.robot.currentTile;
        }

        if (scene.game.robot.previousState != robotState.WALK_PAST_HUMAN || scene.game.robot.plan == null || scene.game.robot.plan.length == 0 || scene.game.player.previousTaskI != scene.game.player.taskI) {
          // Have the robot move off-screen
          var tile = getOffScreenTileInOppositeDirectionOfHumanMotion(scene);
          if (tile == null) {
            tile = getOffScreenTile(scene);
            if (tile == null) {
              scene.game.robot.goalTile = scene.game.robot.currentTile; // stop the robot
            } else {
              scene.game.robot.goalTile = tile;
            }
          } else {
            scene.game.robot.goalTile = tile;
          }
          scene.game.robot.plan = generatePlan(scene.game.robot.currentTile, [scene.game.robot.goalTile], scene.game.robot.goalTile);
        }
      }
      break;
    case robotState.STATIONARY:
      scene.game.robot.anims.stop();
      scene.game.robot.tileAtBeginningOfWalkPast = null;
      scene.game.robot.goalTile = scene.game.robot.currentTile;
      scene.game.robot.plan = null;
      break;
    case robotState.LEAVE_SCREEN:
      if (isOffCamera(scene, scene.game.robot.currentTile)) {
        setHelpBubbleVisible(scene, false);
        scene.game.robot.currentState = robotState.OFFSCREEN;
      } else {
        // Have the robot move off-screen
        if (scene.game.robot.previousState != robotState.LEAVE_SCREEN || scene.game.robot.plan == null || scene.game.robot.plan.length == 0 || scene.game.player.previousTaskI != scene.game.player.taskI) {
          var tile = getOffScreenTile(scene);
          if (tile == null) {
            scene.game.robot.goalTile = scene.game.robot.currentTile; // stop the robot
          } else {
            scene.game.robot.goalTile = tile;
          }
          scene.game.robot.plan = generatePlan(scene.game.robot.currentTile, [scene.game.robot.goalTile], scene.game.robot.goalTile);
        }
      }
      break;
    case robotState.GO_TOWARDS_GOAL:
      if (scene.game.robot.goalTile != null && (scene.game.robot.plan == null || scene.game.robot.plan.length == 0 || distance(scene.game.robot.goalTile, scene.game.robot.plan[scene.game.robot.plan.length - 1]) != 0)) {
        scene.game.robot.plan = generatePlan(scene.game.robot.currentTile, [scene.game.robot.goalTile], scene.game.robot.goalTile);
        // Have the robot not get too close to the human
        // console.log("GO_TOWARDS_GOAL", scene.game.robot.plan, distance(scene.game.robot.currentTile, scene.game.player.currentTile));
        if ((scene.game.robot.plan == null || scene.game.robot.plan.length == 0) && distance(scene.game.robot.currentTile, scene.game.player.currentTile) <= robotToHumanDistance) {
          // Find a point that is a distance of robotToHumanDistance away from the human
          function goalConstraints(tile) {
            var awayFromHuman = distance(tile, scene.game.player.currentTile) >= robotToHumanDistance;
            var notWall = game.worldLayer.getTileAt(tile.x, tile.y) == null;
            return awayFromHuman && notWall;
          }
          function pathConstraints(tile) {
            return true;
          }

          var goalTile =  closestPointWithinConstraints(scene.game.robot.currentTile, goalConstraints, pathConstraints, 20*screenSizeX*screenSizeY);
          // console.log("GO_TOWARDS_GOAL goalTile", goalTile);
          if (goalTile != null) {
            scene.game.robot.plan = generatePlan(scene.game.robot.currentTile, [goalTile], goalTile);
          }
        }
      }
      if (isOffCamera(scene, scene.game.robot.currentTile)) {
        setHelpBubbleVisible(scene, false);
        // game.hasRobotStateChangedThisUpdate = false;
        scene.game.robot.currentState = robotState.OFFSCREEN;
      }
      break;
    default:
      break;
  }
  scene.game.robot.previousState = robotStateToEvaluate;
}

function moveRobotAlongPlan(scene) {
  // If we have finished rendering the last robot movement animation
  if (scene.game.robot.movementTimer == null && scene.game.robot.plan != null && scene.game.robot.plan.length > 0) {
    // If the robot's next move would collide with the human
    if ((scene.game.robot.plan[0].x == scene.game.player.currentTile.x && scene.game.robot.plan[0].y == scene.game.player.currentTile.y) ||
        (scene.game.robot.plan[0].x == scene.game.player.nextTile.x && scene.game.robot.plan[0].y == scene.game.player.nextTile.y)) {
        // If the human is in the goal position, terminate the plan
        if (scene.game.robot.plan.length == 1) {
          scene.game.robot.plan = null;
        }
        // Else, replan
        else {
          scene.game.robot.plan = generatePlan(scene.game.robot.currentTile, [scene.game.robot.goalTile], scene.game.robot.goalTile);
        }

    }
    if (scene.game.robot.plan != null) {
      // Set the animation
      if (scene.game.robot.plan.length > 0) {
        var dx = scene.game.robot.plan[0].x - scene.game.robot.currentTile.x;
        if (dx == -1) {
          scene.game.robot.anims.play('robotLeft', true);
        } else if (dx == 1) {
          scene.game.robot.anims.play('robotRight', true);
        } else {
          var dy = scene.game.robot.plan[0].y - scene.game.robot.currentTile.y;
          if (dy == -1) {
            scene.game.robot.anims.play('robotUp', true);
          } else if (dy == 1) {
            scene.game.robot.anims.play('robotDown', true);
          } else {
            console.log("Robot movement uncompatible dx, dy", dx, dy);
            scene.game.robot.anims.stop();
          }
        }
      } else {
        scene.game.robot.anims.stop();
      }
      // Start the movement timer
      scene.game.robot.movementTimer = scene.time.addEvent({delay: robotMsPerStep});
      // Log the game state
      if (!load) logData(tutorial ? logTutorialStateEndpoint : logGameStateEndpoint, getGameState(scene, eventType.MOVEMENT));
    } else {
      scene.game.robot.anims.stop();
    }
  }
}
