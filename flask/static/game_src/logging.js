// const playbackSpeed = 2.0;

const eventType = {
  MOVEMENT : 0,
  CLICK : 1,
  INITIAL : 2,
  SPACEBAR_START : 3,
  SPACEBAR_END : 4,
  PLAYER_STATE_CHANGE : 5,
  ROBOT_STATE_CHANGE : 6,
  SET_HELP_BUBBLE : 7,
  SCORE_CHANGE : 8,
  TUTORIAL_NEXT_BUTTON_PRESSED : 9,
  TUTORIAL_LOAD_STATE : 10,
  SHIFT_GAME_KILL : 11,
  SHOWING_ENDING_SCREEN : 12,
  SHIFT_PRESSED : 13,
}

const logGameConfigEndpoint = "log_game_config";
const logGameStateEndpoint = "log_game_state";
const logTutorialConfigEndpoint = "log_tutorial_config";
const logTutorialStateEndpoint = "log_tutorial_state";

// Currently, I have no retry mechanism. I assume every request will go through,
// but there may be some delay due to browser blocking/queuing. Therefore, I
// do not store past requests
const batchSize = 6;
var currentBatch = [];

// if you have >= logDataErrorNum errors within logDataErrorTimeLimit secs, tell the user to quit.
const logDataErrorTimeLimit = 60; // seconds
const logDataErrorNum = 20/batchSize;
var logDataRecentErrors = [];
const errorsBeforeRepeatNotifications = 20;
var errorsSinceLastNotification = 0;

var gameStateID = 0;
var largestSentGameStateID = 0;
var largestReceivedGameStateID = 0;
var numSentLogs = 0;
var numReceivedLogs = 0;

function getGameConfig(scene) {
  var browserData = bowser.getParser(window.navigator.userAgent);
  return {
    uuid:uuid,
    gid:gid,
    order:order,
    start_time: scene.game.start_time,
    browserData: browserData ? browserData.parsedResult : null,
    // playerMsPerStep: playerMsPerStep,
    // robotMsPerStep: robotMsPerStep,
  };
}

function getGameState(scene, eventType, additionalData) {
  var retval = {
    // User study details
    uuid:uuid,
    gid:gid,
    order:order,
    // eventType
    eventType: eventType,
    // Game state
    dtime: Date.now() - scene.game.start_time,
    gameStateID: gameStateID,
    player: {
      currentTile: scene.game.player.currentTile,
      nextTile: scene.game.player.nextTile,
      currentState: scene.game.player.currentState,
      // timerProgress: (scene.game.player.timer == null) ? null : scene.game.player.timer.getProgress(),
      // timerDelay: (scene.game.player.timer == null) ? null : scene.game.player.timer.delay,
      score: scene.game.player.score,
      taskI: scene.game.player.taskI,
      taskPlan: scene.game.player.taskPlan,
    },
    // Animation information
    player_anim_is_playing: scene.game.player.anims.isPlaying,
    player_anim_key: scene.game.player.anims.getCurrentKey(),
    active_player_movement_timer: scene.game.player.movementTimer != null,
    // Distraction Task Information
    distractionTaskTimerSecs: scene.game.distractionTaskTimerSecs,
    // Tutorial Data
    tutorialStep: scene.game.tutorialStep,
  };
  if (scene.game.robot) {
    retval.robot = {
      currentTile: scene.game.robot.currentTile,
      plan: scene.game.robot.plan,
      currentState: scene.game.robot.currentState,
      previousState: scene.game.robot.previousState,
      helpBubbleVisible: scene.game.robot.helpBubble.getVisible(),
      currentActionI: scene.game.robot.currentActionI,
      taskPlan: scene.game.robot.taskPlan,
    };
    // console.log("scene.game.robot.anims.getCurrentKey()", scene.game.robot.anims.getCurrentKey());
    retval.robot_anim_key = scene.game.robot.anims.getCurrentKey();
    retval.active_robot_movement_timer = scene.game.robot.movementTimer != null;
  }
  for (dataKey in additionalData) {
    retval[dataKey] = additionalData[dataKey];
  }
  gameStateID++;
  return retval;
}

function logData(endpoint, data) {
  var payloadToSend;

  if (endpoint == logGameStateEndpoint || endpoint == logTutorialStateEndpoint) {
    var dataGameStateID = data.gameStateID;
    if (dataGameStateID > largestSentGameStateID) {
      largestSentGameStateID = dataGameStateID;
    }
    currentBatch.push(data);
    if (currentBatch.length >= batchSize || data.eventType == eventType.SHOWING_ENDING_SCREEN) {
      payloadToSend = currentBatch;
      numSentLogs += currentBatch.length;
      currentBatch = [];
    } else {
      return;
    }
  } else {
    payloadToSend = data;
  }

  var url = baseURL + endpoint;
  // console.log("Send ", data)
  $.ajax({
    type : "POST",
    url : url,
    data: JSON.stringify(payloadToSend, null, '\t'),
    contentType: 'application/json;charset=UTF-8',
    success: function(received_data, status) {
        received_data = JSON.parse(received_data);
        if ("largestGameStateID" in received_data) {
          if (received_data["largestGameStateID"] > largestReceivedGameStateID) {
            largestReceivedGameStateID = received_data["largestGameStateID"];
          }
          numReceivedLogs += received_data["numReceivedLogs"];
          console.log("SUCCESS: confirmed log with largestGameStateID", received_data["largestGameStateID"], numReceivedLogs, numSentLogs);
        }
    },
    error: function(received_data, status) {
        try {
          received_data = JSON.parse(received_data);
          if ("largestGameStateID" in received_data) {
            if (parseInt(received_data["largestGameStateID"]) > largestReceivedGameStateID) {
              largestReceivedGameStateID = parseInt(received_data["largestGameStateID"]);
            }
            numReceivedLogs += parseInt(received_data["numReceivedLogs"]);
            console.log("FAILURE: confirmed log with largestGameStateID", received_data["largestGameStateID"], numReceivedLogs, numSentLogs);
          }
        } catch(err) {

        }
        for (var i = 0; i < logDataRecentErrors.length; i++) {
          if (Date.now() - logDataRecentErrors[i] >= logDataErrorTimeLimit*1000) {
            logDataRecentErrors.splice(i, 1);
            i -= 1;
            if (logDataRecentErrors.length == 0) {
              break;
            }
          } else {
            break;
          }
        }
        if (logDataRecentErrors.length == 0) {
          errorsSinceLastNotification = 0;
        }
        logDataRecentErrors.push(Date.now());
        if (logDataRecentErrors.length > logDataErrorNum) {
          if (errorsSinceLastNotification % errorsBeforeRepeatNotifications == 0) {
            if (errorsSinceLastNotification < errorsBeforeRepeatNotifications) {
              alert("WARNING: Your internet is unable to properly log game data. If this problem persists, you will be asked to stop the Amazon Mechanical Turk HIT.");
            } else {
              alert("ERROR: Please STOP the Amazon Mechanical Turk HIT. Data is not getting logged properly, and you will not be approved for the HIT.");
            }
          }
          errorsSinceLastNotification += numReceivedLogs;
        }
    }
  });
}

function loadUpdate(scene) {
  scene.game.prevHelpBubbleVisible = false;
  if (dataToLoad.length > 0) {
    var numTimesInWhileLoop = 0;
    while (dataToLoad.length > 1) {
      numTimesInWhileLoop += 1;
      if (numTimesInWhileLoop > 1) {
        console.log("numTimesInWhileLoop", numTimesInWhileLoop);
      }
      var currentTime = Date.now();
      var dtime = (currentTime - scene.game.start_time) + starting_dtime;

      console.log("dtime", dtime, "dataToLoad[0].dtime", dataToLoad[0].dtime);

      switch (dataToLoad[0].eventType) {
        case eventType.SPACEBAR_START:
          scene.game.loadSpacebarStarted = true;
          break;
        case eventType.SPACEBAR_END:
          scene.game.loadSpacebarStarted = false;
          break;
        case eventType.SET_HELP_BUBBLE:
          if (scene.game.tasks.robotActions[scene.game.robot.currentActionI].robotAction.query == "amIHere") {
            setHelpBubbleToAmIHere(scene);
          } else if (scene.game.tasks.robotActions[scene.game.robot.currentActionI].robotAction.query == "leadMe") {
            setHelpBubbleToLeadMe(scene, dataToLoad[0].hasSaidYes);
          }
          break;
        case eventType.CLICK:
          // We only have leadMe queries.
          var queryType = "leadMe";//scene.game.tasks.robotActions[scene.game.robot.currentActionI].robotAction.query;
          console.log("click button", queryType, dataToLoad, dataToLoad[0].buttonName, helpRequestButtonCallbacks[queryType][dataToLoad[0].buttonName]);
          helpRequestButtonCallbacks[queryType][dataToLoad[0].buttonName](scene);
          break;
      }

      scene.game.player.currentTile = dataToLoad[0].player.currentTile;
      scene.game.player.nextTile = dataToLoad[0].player.nextTile;
      if (lastLoadedData == null || scene.game.player.anims.getCurrentKey() != lastLoadedData.player_anim_key) {
        scene.game.player.anims.play(dataToLoad[0].player_anim_key, true);
      }
      if (!dataToLoad[0].player_anim_is_playing) {
        scene.game.player.anims.stop();
      }
      // Update the player compass
      if (scene.game.compass) {
        updateCompass(scene);
      }
      if (dataToLoad[0].player.currentState != scene.game.player.currentState) {
        if (scene.game.player.currentState == playerState.NAVIGATION_TASK) {
          navigationTaskToDistractionTask(scene);
        } else if (scene.game.player.currentState == playerState.DISTRACTION_TASK) {
          completedDistractionTask(scene);
        }
      }
      scene.game.player.currentState = dataToLoad[0].player.currentState;
      if (scene.game.loadSpacebarStarted) {
        scene.game.distractionTaskTimerSecs += (currentTime - scene.game.lastLoadUpdateTime)/1000;
      }
      if (scene.game.player.currentState == playerState.DISTRACTION_TASK && scene.game.distractionTaskTimerSecs > 0) {
        inDistractionTask(scene);
      }
      if (dataToLoad[0].player.score != null) scene.game.player.score = dataToLoad[0].player.score;


      scene.game.robot.currentTile = dataToLoad[0].robot.currentTile;
      scene.game.robot.plan = dataToLoad[0].robot.plan;
      scene.game.robot.currentActionI = dataToLoad[0].robot.currentActionI;

      if (!dataToLoad[0].active_player_movement_timer) {
        if (scene.game.player.movementTimer) {
          scene.game.player.movementTimer.paused = true;
          scene.game.player.movementTimer.destroy();
        }
        scene.game.player.movementTimer = null;
      } else if (lastLoadedData != null && dataToLoad[0].active_player_movement_timer && !lastLoadedData.active_player_movement_timer && scene.game.player.movementTimer == null) {
        if (scene.game.player.movementTimer) {
          scene.game.player.movementTimer.paused = true;
          scene.game.player.movementTimer.destroy();
          scene.game.player.movementTimer = null;
        }
        scene.game.player.movementTimer = scene.time.addEvent({delay: playerMsPerStep});
      }

      renderPlayerMovementAnimation(scene);
      if (scene.game.player.movementTimer == null) {
        // if (hasCompletedCurrentNavigationTask(scene)) {
        //   scene.game.player.taskI++;
        // }
        var gameXY = tileToGameXY(scene.game.player.currentTile);
        scene.game.player.x = gameXY.x;
        scene.game.player.y = gameXY.y;
      }

      if (!dataToLoad[0].active_robot_movement_timer) {
        if (scene.game.robot.movementTimer) {
          scene.game.robot.movementTimer.paused = true;
          scene.game.robot.movementTimer.destroy();
        }
        scene.game.robot.movementTimer = null;
      } else if (lastLoadedData != null && dataToLoad[0].active_robot_movement_timer && !lastLoadedData.active_robot_movement_timer && scene.game.robot.movementTimer == null) {
        if (scene.game.robot.movementTimer) {
          scene.game.robot.movementTimer.paused = true;
          scene.game.robot.movementTimer.destroy();
          scene.game.robot.movementTimer = null;
        }
        scene.game.robot.movementTimer = scene.time.addEvent({delay: robotMsPerStep});
      }

      if (scene.game.minimap && scene.game.prevHelpBubbleVisible && !dataToLoad[0].robot.helpBubbleVisible) {
        destroyRobotGoalRect(scene);
      }
      scene.game.prevHelpBubbleVisible = dataToLoad[0].robot.helpBubbleVisible;

      scene.game.robot.helpBubble.setVisible(dataToLoad[0].robot.helpBubbleVisible);

      renderRobotMovementAnimation(scene);
      if (scene.game.robot.movementTimer == null) {
        var gameXY = tileToGameXY(scene.game.robot.currentTile);
        scene.game.robot.x = gameXY.x;
        scene.game.robot.y = gameXY.y;
      }

      scene.game.lastLoadUpdateTime = currentTime;

      var next_dtime = dataToLoad[1].dtime;
      if (dtime >= next_dtime) {
        lastLoadedData = dataToLoad.splice(0, 1);
      } else {
        lastLoadedData = dataToLoad[0];
        break;
      }
    }

    if (dataToLoad.length == 1) {
      console.log("Finished Playback!");
      dataToLoad = []
    }
  }
}
