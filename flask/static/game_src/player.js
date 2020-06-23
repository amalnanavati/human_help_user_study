const pointOfInterestString = " Chair ";
const highlightPointString = " Computer ";
const timeForDistractionTask = 10;

const playerMsPerStep = 200;

const playerColor = 0xff0000

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
  game.player.anims.play('left', true);
}

function initializeGamePlayerTimer(scene) {
  scene.game.player.negativeScoreTimer = null;
  scene.game.player.timer = scene.time.addEvent({
    delay: scene.game.tasks.tasks[scene.game.player.taskI].timeLimit*1000,
    loop: false,
    callback: function() {
      scene.game.player.negativeScoreTimer = scene.time.addEvent({
        delay: 500, // 0.5 sec
        loop: true,
        callback: function() {
          if (scene.game.negativeScoreRedOutline.visible) {
            scene.game.negativeScoreRedOutline.setVisible(false);
            scene.game.scoreText.setFill("#ececec");
          } else {
            scene.game.negativeScoreRedOutline.setVisible(true);
            scene.game.scoreText.setFill("#ff0000");
            scene.game.player.score -= 1;
          }
        },
      });
    },
  });
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

function transitionPlayerState(scene) {
  // Check if we have completed a navigation task
  if (scene.game.player.currentState == playerState.NAVIGATION_TASK && hasCompletedCurrentNavigationTask(scene)) {
    scene.game.player.currentState = playerState.DISTRACTION_TASK;
    scene.game.distractionTaskTimerSecs = 0;
    scene.game.player.hasCompletedDistractionTask = false;
    scene.game.player.timer.destroy();
    if (scene.game.player.taskI < scene.game.tasks.tasks.length) {
      if (scene.game.player.negativeScoreTimer != null) {
        scene.game.scoreText.setFill("#ececec");
        scene.game.negativeScoreRedOutline.setVisible(false);
        scene.game.player.negativeScoreTimer.destroy();
        scene.game.player.negativeScoreTimer = null;
      }
    }
    setRobotActionInProgress(scene, false);
    destroyRobotGoalRect(scene);
    if (scene.game.robot.currentState != robotState.OFFSCREEN && scene.game.robot.currentState != robotState.WALK_PAST_HUMAN) {
      scene.game.robot.currentState = robotState.WALK_PAST_HUMAN;
    }
  }

  // If we are in the distraction task, display the distraction task timer
  if (scene.game.player.currentState == playerState.DISTRACTION_TASK && scene.game.distractionTaskTimerSecs > 0 && !hasCompletedCurrentDistractionTask(scene)) {
    setDistractionTaskBarVisible(scene, true);
    drawDistractionTaskBarProgress(scene);
  }

  // Check if we have completed a distraction task
  if (scene.game.player.currentState == playerState.DISTRACTION_TASK && hasCompletedCurrentDistractionTask(scene)) {
    console.log("completed distraction task");
    scene.game.player.taskI++;
    transitionToNewTask(scene);
    scene.game.player.score += scorePerTask;
    if (scene.game.player.taskI < scene.game.tasks.tasks.length) {
      scene.game.player.currentState = playerState.NAVIGATION_TASK;
      initializeGamePlayerTimer(scene);
      getCurrentTaskPlan(scene);
      scene.game.player.currentTaskDistance = scene.game.player.taskPlan.length;
    } else {
      scene.game.player.currentState = playerState.COMPLETED_TASKS;
      scene.game.endGameDelayTimer = scene.time.addEvent({
        delay: 2*1000,
        callback: function() {
          scene.game.isRunning = false;
          createEndingScreen(scene);
        },
      });
    }
  }

  // Update the task plans (periodically, to increase efficiency)
  if (scene.game.player.taskPlan == null || scene.game.player.taskPlan.length == 0 || scene.game.player.elapsedDistanceSinceComputingTaskPlan >= Math.floor(scene.game.player.taskPlan.length/5)) {
    getCurrentTaskPlan(scene);
  }
  if (scene.game.robot.isBeingLed) {
    if (scene.game.robot.taskPlan == null || scene.game.robot.taskPlan.length == 0 || scene.game.robot.elapsedDistanceSinceComputingTaskPlan >= Math.floor(scene.game.robot.taskPlan.length/5)) {
      getCurrentPlanToRobotGoal(scene);
    }
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

  renderPlayerAndCameraOnMinimap(scene);

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
  if (objectsOverlaps(scene.game.player, scene.game.minimap)) {
    setMinimapAlpha(scene, 0.25);
  } else {
    setMinimapAlpha(scene, 1.0);
  }

  if (scene.game.player.movementTimer == null) {
    scene.game.player.previousTile = scene.game.player.currentTile;
  }
  if (scene.game.player.movementTimer != null && scene.game.player.movementTimer.getOverallProgress() == 1.0) {
    scene.game.player.currentTile = scene.game.player.nextTile;
    scene.game.player.movementTimer = null;
    // Log the game state
    // if (!load) logData(logGameStateEndpoint, getGameState());
  }
}

function processPlayerKeyPresses(scene) {
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
          }
          if (scene.game.distractionTaskTimerSecs >= timeForDistractionTask) {
            scene.game.player.hasCompletedDistractionTask = true;
            setDistractionTaskBarVisible(scene, false);
          }

        }
      }
    }
  } else if (!scene.game.cursors.space.isDown) {
    scene.game.lastTimeSpaceHeld = null;
  }

  if (newAction) {
    scene.game.player.movementTimer = scene.time.addEvent({delay: playerMsPerStep});
  }
  // Log the game state
  // if (shouldLogData && !load) logData(logGameStateEndpoint, getGameState());
}

function transitionToNewTask(scene) {
  var hasNextGoal = game.player.taskI < game.tasks.tasks.length;
  var targetTile = null;
  if (hasNextGoal) {
    var targetStr = game.tasks.tasks[game.player.taskI].semanticLabel + highlightPointString + game.tasks.tasks[game.player.taskI].target;
    targetTile = game.semanticLabelsToXY[targetStr][0];
  }
  updateHighlightBox(scene, hasNextGoal, targetTile);
  renderPlayerGoalOnMinimap(scene, hasNextGoal, targetTile);
}
