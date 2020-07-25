const pointOfInterestString = " Chair ";
const highlightPointString = " Computer ";
const timeForDistractionTask = 10;

const playerMsPerStep = 200;

const playerColor = 0xff0000
const playerColorStr = '#ff0000'

const scorePerTask = 10;

const playerState = {
  NAVIGATION_TASK: 0,
  DISTRACTION_TASK: 1,
  COMPLETED_TASKS: 2,
}

function createPlayer(scene) {
  scene.game.player = scene.physics.add.sprite(scene.game.config.width/2, scene.game.config.width/2, 'characters');
  scene.game.player.setScale(0.80);
  scene.game.player.setDepth(5);
  scene.game.player.currentTile = {x : scene.game.tasks.player_start_location.x, y : scene.game.tasks.player_start_location.y};
  scene.game.player.previousTile = scene.game.player.currentTile;
  scene.game.player.nextTile = scene.game.player.currentTile;
  var gameXY = tileToGameXY(scene.game.player.currentTile);
  scene.game.player.x = gameXY.x;
  scene.game.player.y = gameXY.y;
  scene.game.player.taskPlan = null;
  scene.game.player.taskI = 0;
  scene.game.player.previousTaskI = scene.game.player.taskI;
  scene.game.player.score = 0;
  scene.game.player.currentState = scene.game.tasks.tasks.length > 0 ? playerState.NAVIGATION_TASK : playerState.COMPLETED_TASKS;
  scene.game.player.enableBody();

  // Create the player animations
  scene.anims.create({
      key: 'down',
      frames: scene.anims.generateFrameNumbers('characters', {start: 0, end: 3}),
      frameRate: 10,
      repeat: -1
  });
  scene.anims.create({
      key: 'up',
      frames: scene.anims.generateFrameNumbers('characters', {start: 4, end: 7}),
      frameRate: 10,
      repeat: -1
  });
  scene.anims.create({
      key: 'left',
      frames: scene.anims.generateFrameNumbers('characters', {start: 8, end: 11}),
      frameRate: 10,
      repeat: -1
  });
  scene.anims.create({
      key: 'right',
      frames: scene.anims.generateFrameNumbers('characters', {start: 12, end: 15}),
      frameRate: 10,
      repeat: -1
  });
  scene.game.player.anims.play('left', true);
  scene.game.player.anims.stop();
}

function setTimeLimitFromBusyness(scene) {
  // Compute the timeLimit for this task
  if (scene.game.tasks.tasks[scene.game.player.taskI].busyness == "free time") {
    scene.game.tasks.tasks[scene.game.player.taskI].timeLimit = -1;
  } else if (scene.game.tasks.tasks[scene.game.player.taskI].busyness != null) {
    var startLoc = scene.game.player.currentTile;
    var goalSemanticLabel = scene.game.tasks.tasks[scene.game.player.taskI].semanticLabel + pointOfInterestString + scene.game.tasks.tasks[scene.game.player.taskI].target.toString();
    var endLocs = scene.game.semanticLabelsToXY[goalSemanticLabel];
    var playerPlan = generatePlan(startLoc, endLocs, endLocs[0]);
    var distanceToGoal = playerPlan.length;
    if (scene.game.tasks.tasks[scene.game.player.taskI].busyness == "high") {
      // 2.0 is cutting it close for Amal
      scene.game.tasks.tasks[scene.game.player.taskI].timeLimit = distanceToGoal*3.0*playerMsPerStep/1000;
    } else if (scene.game.tasks.tasks[scene.game.player.taskI].busyness == "medium") {
      // 4.0 is cutting it close for Amal to help the robot *and* get to the goal
      scene.game.tasks.tasks[scene.game.player.taskI].timeLimit = distanceToGoal*7.0*playerMsPerStep/1000;
    } else {
      console.log("Unknown busyness", scene.game.tasks.tasks[scene.game.player.taskI].busyness);
      scene.game.tasks.tasks[scene.game.player.taskI].timeLimit = -1;
    }
  }
}

function initializeGamePlayerTimer(scene) {
  if (!scene.game.tasks.tasks[scene.game.player.taskI].timeLimit) {
    setTimeLimitFromBusyness(scene);
  }

  if (scene.game.tasks.tasks[scene.game.player.taskI].timeLimit > 0) {
    scene.game.player.negativeScoreTimer = null;
    if (scene.game.player.timer) {
      scene.game.player.timer.destroy();
      scene.game.player.timer = null;
    }
    scene.game.player.timer = scene.time.addEvent({
      delay: scene.game.tasks.tasks[scene.game.player.taskI].timeLimit*1000,
      loop: false,
      callback: function() {
        if (scene.game.isRunning) {
          scene.game.player.negativeScoreTimer = scene.time.addEvent({
            delay: 1000,
            loop: true,
            callback: function() {
              if (!load && scene.game.isRunning) {
                scene.game.player.score -= 1;
                logData(tutorial ? logTutorialStateEndpoint : logGameStateEndpoint, getGameState(scene, eventType.SCORE_CHANGE));
              }
            },
          });
        }
      },
    });
    scene.game.timeProgressBar.setText("Time: ");
  } else {
    if (scene.game.player.timer != null) {
      scene.game.player.timer.destroy();
      scene.game.player.timer = null;
    }
  }
}

function getCurrentTaskPlan(scene) {
  if (scene.game.player.taskI >= scene.game.tasks.tasks.length) {
    scene.game.player.taskPlan = [];
    return scene.game.player.taskPlan;
  }
  var goal = scene.game.tasks.tasks[scene.game.player.taskI].semanticLabel;
  var currLoc = scene.game.player.currentTile;
  var goalLocs = scene.game.semanticLabelsToXY[goal];
  var heuristicGoal = goalLocs[Math.floor(Math.random() * goalLocs.length)];
  if (scene.game.player.taskPlan != null && scene.game.player.taskPlan.length > 0) {
    heuristicGoal = scene.game.player.taskPlan[scene.game.player.taskPlan.length - 1];
  }
  // var goalLocs = game.semanticLabelsToXY[goal+pointOfInterestString];
  // var heuristicGoal = goalLocs[0];
  scene.game.player.elapsedDistanceSinceComputingTaskPlan = 0;
  scene.game.player.taskPlan = generatePlan(currLoc, goalLocs, heuristicGoal)
}

function getCurrentPlanToRobotGoal(scene) {
  if (!scene.game.robot.isBeingLed) {
    scene.game.robot.taskPlan = [];
    return scene.game.robot.taskPlan;
  }
  var goal = scene.game.tasks.robotActions[scene.game.robot.currentActionI].robotAction.targetSemanticLabel;
  var currLoc = scene.game.player.currentTile;
  var goalLocs = scene.game.semanticLabelsToXY[goal];
  var heuristicGoal = goalLocs[Math.floor(Math.random() * goalLocs.length)];
  if (scene.game.robot.taskPlan != null && scene.game.robot.taskPlan.length > 0) {
    heuristicGoal = scene.game.robot.taskPlan[scene.game.robot.taskPlan.length - 1];
  }
  scene.game.robot.elapsedDistanceSinceComputingTaskPlan = 0;
  scene.game.robot.taskPlan = generatePlan(currLoc, goalLocs, heuristicGoal);
  return scene.game.robot.taskPlan;
}

function hasCompletedCurrentNavigationTask(scene) {
  if (scene.game.player.taskI >= scene.game.tasks.tasks.length) {
    return false;
  }

  var currentLocationKey = String([scene.game.player.currentTile.x, scene.game.player.currentTile.y]);
  if (currentLocationKey in scene.game.xyToSemanticLabels) {
    var currentSemanticLabels = scene.game.xyToSemanticLabels[currentLocationKey];
    var goalSemanticLabel = scene.game.tasks.tasks[scene.game.player.taskI].semanticLabel;
    return currentSemanticLabels.has(goalSemanticLabel);
  }

  return false;
}

function hasCompletedCurrentDistractionTask(scene) {
  return scene.game.player.hasCompletedDistractionTask;
}

function navigationTaskToDistractionTask(scene) {
  scene.game.distractionTaskTimerSecs = 0;
  scene.game.player.hasCompletedDistractionTask = false;
  if (scene.game.robot) scene.game.robot.isBeingLed = false;
}

function inDistractionTask(scene) {
  if (scene.game.player.timer != null && !scene.game.player.timer.paused) {
    // TODO (amal) maybe set paused = true first?
    scene.game.player.timer.destroy();
    scene.game.player.timer.paused = true;
    // if (scene.game.player.taskI < scene.game.tasks.tasks.length) {
    if (scene.game.player.negativeScoreTimer != null) {
      // scene.game.scoreText.setFill("#ececec");
      // scene.game.negativeScoreRedOutline.setVisible(false);
      // TODO (amal) maybe set paused = true first?
      scene.game.player.negativeScoreTimer.destroy();
      scene.game.player.negativeScoreTimer.paused = true;
      scene.game.player.negativeScoreTimer = null;
    }
    scene.game.timeProgressBar.destroyTimer();
  }
  if (scene.game.distractionTaskText) {
    // if (scene.game.player.timer == null) {
      if (game.tasks.tasks[game.player.taskI].semanticLabel.includes("Restroom")) {
        scene.game.distractionTaskText.text = "Using the restroom. Continue holding the Space bar...";
      } else if (game.tasks.tasks[game.player.taskI].semanticLabel.includes("Lounge")) {
        if (game.tasks.tasks[game.player.taskI].target == 1) { // coffee
          scene.game.distractionTaskText.text = "Making coffee. Continue holding the Space bar...";
        } else { // microwave
          scene.game.distractionTaskText.text = "Heating food. Continue holding the Space bar...";
        }
      } else if (game.tasks.tasks[game.player.taskI].semanticLabel.includes("Game")) {
        if (game.tasks.tasks[game.player.taskI].target % 2 == 1) { // tetris
          scene.game.distractionTaskText.text = "Playing Tetris. Continue holding the Space bar...";
        } else { // Pacman
          scene.game.distractionTaskText.text = "Playing Pacman. Continue holding the Space bar...";
        }
      } else {
        if ((scene.game.player.taskI % 2) == 0) {
          scene.game.distractionTaskText.text = "Clearing viruses. Continue holding the Space bar...";
        } else {
          scene.game.distractionTaskText.text = "Updating software. Continue holding the Space bar...";
        }
        // console.log("Free time without restroom or lounge or game room");
        // scene.game.distractionTaskText.text = "Continue holding the Space bar...";
      }
    // } else {

    // }
    setDistractionTaskBarVisible(scene, true);
    drawDistractionTaskBarProgress(scene);
  }
}

function completedDistractionTask(scene) {
  if (scene.game.distractionTaskText) setDistractionTaskBarVisible(scene, false);
  scene.game.player.taskI++;
  transitionToNewTask(scene);
  if (!load) {
    scene.game.player.score += scorePerTask;
    logData(tutorial ? logTutorialStateEndpoint : logGameStateEndpoint, getGameState(scene, eventType.SCORE_CHANGE));
  }
  if (scene.game.player.taskI < scene.game.tasks.tasks.length) {
    scene.game.player.currentState = playerState.NAVIGATION_TASK;
    if (scene.game.player.taskI < scene.game.tasks.tasks.length) {
      if (scene.game.timeProgressBar) initializeGamePlayerTimer(scene);
      getCurrentTaskPlan(scene);
      scene.game.player.currentTaskDistance = scene.game.player.taskPlan.length;
    }
  } else {
    scene.game.player.currentState = playerState.COMPLETED_TASKS;
    if (!load) logData(tutorial ? logTutorialStateEndpoint : logGameStateEndpoint, getGameState(scene, eventType.PLAYER_STATE_CHANGE));
    scene.game.endGameDelayTimer = scene.time.addEvent({
      delay: 2*1000,
      callback: function() {
        scene.game.isRunning = false;
        createEndingScreen(scene);
      },
    });
  }
}

function transitionPlayerState(scene) {
  var playerStateAtBeginning = scene.game.player.currentState;
  // Check if we have completed a navigation task
  if (scene.game.player.currentState == playerState.NAVIGATION_TASK && hasCompletedCurrentNavigationTask(scene)) {
    scene.game.player.currentState = playerState.DISTRACTION_TASK;
    navigationTaskToDistractionTask(scene);
    if (scene.game.tutorialStep < 3) {
      console.log("skip distraction task");
      // For the first few steps of the tutorial before we have distraction tasks
      scene.game.player.hasCompletedDistractionTask = true;
      completedDistractionTask(scene);
    }

    // }
    if (scene.game.robot) {
      setHelpBubbleVisible(scene, false);
      setRobotActionInProgress(scene, false);
      if (scene.game.minimap) destroyRobotGoalRect(scene);
      if (scene.game.robot.currentState != robotState.OFFSCREEN && scene.game.robot.currentState != robotState.WALK_PAST_HUMAN) {
        scene.game.robot.currentState = robotState.WALK_PAST_HUMAN;
      }
    }
  }

  // If we are in the distraction task, display the distraction task timer
  if (scene.game.player.currentState == playerState.DISTRACTION_TASK && scene.game.distractionTaskTimerSecs > 0 && !hasCompletedCurrentDistractionTask(scene)) {
    inDistractionTask(scene);
  }

  // Check if we have completed a distraction task
  if (scene.game.player.currentState == playerState.DISTRACTION_TASK && hasCompletedCurrentDistractionTask(scene)) {
    completedDistractionTask(scene);
  }

  // Update the task plans (periodically, to increase efficiency)
  if (scene.game.player.taskPlan == null || scene.game.player.taskPlan.length == 0 || scene.game.player.elapsedDistanceSinceComputingTaskPlan >= Math.floor(scene.game.player.taskPlan.length/5)) {
    getCurrentTaskPlan(scene);
  }
  if (scene.game.robot && scene.game.robot.isBeingLed) {
    if (scene.game.robot.taskPlan == null || scene.game.robot.taskPlan.length == 0 || scene.game.robot.elapsedDistanceSinceComputingTaskPlan >= Math.floor(scene.game.robot.taskPlan.length/5)) {
      getCurrentPlanToRobotGoal(scene);
    }
  }

  if (scene.game.player.currentState != playerStateAtBeginning) {
    if (!load) logData(tutorial ? logTutorialStateEndpoint : logGameStateEndpoint, getGameState(scene, eventType.PLAYER_STATE_CHANGE));
  }

}

function renderPlayerMovementAnimation(scene) {
  var p = scene.game.player.movementTimer == null ? 0 : scene.game.player.movementTimer.getOverallProgress();
  var gameXY = tileToGameXY({
    x : scene.game.player.currentTile.x * (1-p) + scene.game.player.nextTile.x * p,
    y : scene.game.player.currentTile.y * (1-p) + scene.game.player.nextTile.y * p,
  });
  scene.game.player.x = gameXY.x;
  scene.game.player.y = gameXY.y;

  if (scene.game.minimap) {
    renderPlayerAndCameraOnMinimap(scene);
    if (objectsOverlaps(scene.game.player, scene.game.minimap)) {
      setMinimapAlpha(scene, 0.25);
    } else {
      setMinimapAlpha(scene, 1.0);
    }
  }

  if (objectsOverlaps(scene.game.player, scene.game.helpButton)) {
    scene.game.helpButton.setAlpha(0.25);
  } else {
    scene.game.helpButton.setAlpha(1.0);
  }

  if (scene.game.instructionText) {
    if (objectsOverlaps(scene.game.player, scene.game.instructionText)) {
      scene.game.instructionText.setAlpha(0.25);
    } else {
      scene.game.instructionText.setAlpha(1.0);
    }
    if (objectsOverlaps(scene.game.player, scene.game.scoreText)) {
      scene.game.scoreText.setAlpha(0.25);
    } else {
      scene.game.scoreText.setAlpha(1.0);
    }
    if (objectsOverlaps(scene.game.player, scene.game.timeProgressBar)) {
      scene.game.timeProgressBar.setAlpha(0.25);
    } else {
      scene.game.timeProgressBar.setAlpha(1.0);
    }
  }

  if (scene.game.player.movementTimer == null) {
    scene.game.player.previousTile = scene.game.player.currentTile;
  }
  if (scene.game.player.movementTimer != null && scene.game.player.movementTimer.getOverallProgress() == 1.0) {
    scene.game.player.currentTile = scene.game.player.nextTile;
    scene.game.player.movementTimer = null;
    if (!load) {
      // Log the game state
      logData(tutorial ? logTutorialStateEndpoint : logGameStateEndpoint, getGameState(scene, eventType.MOVEMENT));
    }
  }
}

function processPlayerKeyPresses(scene) {

  // A developer shortcut to quickly end a game
  if (scene.game.cursors.shift.isDown) {
    if (scene.game.lastTimeShiftHeld != null) {
      if (scene.game.shiftHeldSecs == 0) {
        if (!load) logData(tutorial ? logTutorialStateEndpoint : logGameStateEndpoint, getGameState(scene, eventType.SHIFT_PRESSED));
      }
      var currentTime = Date.now();
      scene.game.shiftHeldSecs += (currentTime - scene.game.lastTimeShiftHeld)/1000;
      scene.game.lastTimeShiftHeld = currentTime;
      if (scene.game.shiftHeldSecs > 10) {
        if (!load) logData(tutorial ? logTutorialStateEndpoint : logGameStateEndpoint, getGameState(scene, eventType.SHIFT_GAME_KILL));
        scene.game.isRunning = false;
        createEndingScreen(scene);
      }
    } else {
      scene.game.lastTimeShiftHeld = Date.now();
    }
  } else {
    scene.game.shiftHeldSecs = 0
    scene.game.lastTimeShiftHeld = null;
  }

  var newAction = false;
  var shouldLogData = false;
  if (scene.game.cursors.left.isDown && !(scene.game.player.currentState == playerState.DISTRACTION_TASK && scene.game.distractionTaskTimerSecs > 0)) {
    scene.game.player.nextTile = {
      x : scene.game.player.currentTile.x - 1,
      y : scene.game.player.currentTile.y,
    };
    scene.game.player.anims.play('left', true);
    newAction = isValidTile(scene.game.player.nextTile, false, true);
    shouldLogData = true;
  } else if (scene.game.cursors.right.isDown && !(scene.game.player.currentState == playerState.DISTRACTION_TASK && scene.game.distractionTaskTimerSecs > 0)) {
    scene.game.player.nextTile = {
      x : scene.game.player.currentTile.x + 1,
      y : scene.game.player.currentTile.y,
    };
    scene.game.player.anims.play('right', true);
    newAction = isValidTile(scene.game.player.nextTile, false, true);
    shouldLogData = true;
  } else if (scene.game.cursors.up.isDown && !(scene.game.player.currentState == playerState.DISTRACTION_TASK && scene.game.distractionTaskTimerSecs > 0)) {
    scene.game.player.nextTile = {
      x : scene.game.player.currentTile.x,
      y : scene.game.player.currentTile.y - 1,
    };
    scene.game.player.anims.play('up', true);
    newAction = isValidTile(scene.game.player.nextTile, false, true);
    shouldLogData = true;
  } else if (scene.game.cursors.down.isDown && !(scene.game.player.currentState == playerState.DISTRACTION_TASK && scene.game.distractionTaskTimerSecs > 0)) {
    scene.game.player.nextTile = {
      x : scene.game.player.currentTile.x,
      y : scene.game.player.currentTile.y + 1,
    };
    scene.game.player.anims.play('down', true);
    newAction = isValidTile(scene.game.player.nextTile, false, true);
    shouldLogData = true;
  } else {
    if (scene.game.player.anims.isPlaying) shouldLogData = true;
    scene.game.player.anims.stop();
  }

  // If the player is close enough to a Point of Interest to press space
  if (scene.game.cursors.space.isDown && scene.game.player.currentState == playerState.DISTRACTION_TASK) {
    if (scene.game.player.currentState == playerState.DISTRACTION_TASK && scene.game.player.taskI < scene.game.tasks.tasks.length) {
      var currentLocationKey = String([scene.game.player.currentTile.x, scene.game.player.currentTile.y]);
      if (currentLocationKey in scene.game.xyToSemanticLabels) {
        var currentSemanticLabels = scene.game.xyToSemanticLabels[currentLocationKey];
        var goalSemanticLabel = scene.game.tasks.tasks[scene.game.player.taskI].semanticLabel + pointOfInterestString + scene.game.tasks.tasks[scene.game.player.taskI].target.toString();
        // If the player pressed the space bar, to initiate the distraction task
        if (currentSemanticLabels.has(goalSemanticLabel)) {

          if (scene.game.lastTimeSpaceHeld != null) {
            var currentTime = Date.now();
            scene.game.distractionTaskTimerSecs += (currentTime - scene.game.lastTimeSpaceHeld)/1000;
            scene.game.lastTimeSpaceHeld = currentTime;
          } else {
            scene.game.lastTimeSpaceHeld = Date.now();
            if (!load) logData(tutorial ? logTutorialStateEndpoint : logGameStateEndpoint, getGameState(scene, eventType.SPACEBAR_START));
          }
          if (scene.game.distractionTaskTimerSecs >= timeForDistractionTask) {
            scene.game.player.hasCompletedDistractionTask = true;
            // Moved to transition
            // setDistractionTaskBarVisible(scene, false);
          }

        }
      }
    }
  } else if (!scene.game.cursors.space.isDown) {
    if (scene.game.lastTimeSpaceHeld != null) {
      if (!load) logData(tutorial ? logTutorialStateEndpoint : logGameStateEndpoint, getGameState(scene, eventType.SPACEBAR_END));
    }
    scene.game.lastTimeSpaceHeld = null;
  }

  if (newAction) {
    scene.game.player.movementTimer = scene.time.addEvent({delay: playerMsPerStep});
    if (!load) logData(tutorial ? logTutorialStateEndpoint : logGameStateEndpoint, getGameState(scene, eventType.MOVEMENT));
  }
  // Log the game state
  if (shouldLogData && !load) logData(tutorial ? logTutorialStateEndpoint : logGameStateEndpoint, getGameState(scene, eventType.MOVEMENT));
}

function transitionToNewTask(scene) {
  var hasNextGoal = game.player.taskI < game.tasks.tasks.length;
  var targetTile = null;
  if (hasNextGoal) {
    var targetStr = game.tasks.tasks[game.player.taskI].semanticLabel + highlightPointString + game.tasks.tasks[game.player.taskI].target;
    targetTile = game.semanticLabelsToXY[targetStr][0];
    var adjacentStr = game.tasks.tasks[game.player.taskI].semanticLabel + pointOfInterestString + game.tasks.tasks[game.player.taskI].target;
    adjacentTile = game.semanticLabelsToXY[adjacentStr][0];
  }
  if (scene.game.highlightBoxSq) updateHighlightBox(scene, hasNextGoal, targetTile, adjacentTile);
  if (scene.game.minimap) renderPlayerGoalOnMinimap(scene, hasNextGoal, targetTile);
}
