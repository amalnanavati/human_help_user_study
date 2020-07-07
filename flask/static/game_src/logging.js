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
}

const logGameConfigEndpoint = "log_game_config";
const logGameStateEndpoint = "log_game_state";
const logTutorialConfigEndpoint = "log_tutorial_config";
const logTutorialStateEndpoint = "log_tutorial_state";

function getGameConfig(scene) {
  return {
    uuid:uuid,
    gid:gid,
    start_time: scene.game.start_time,
    // playerMsPerStep: playerMsPerStep,
    // robotMsPerStep: robotMsPerStep,
  };
}

function getGameState(scene, eventType, additionalData) {
  var retval = {
    // User study details
    uuid:uuid,
    gid:gid,
    // eventType
    eventType: eventType,
    // Game state
    dtime: Date.now() - scene.game.start_time,
    player: {
      currentTile: scene.game.player.currentTile,
      nextTile: scene.game.player.nextTile,
      currentState: scene.game.player.currentState,
      // timerProgress: (scene.game.player.timer == null) ? null : scene.game.player.timer.getProgress(),
      // timerDelay: (scene.game.player.timer == null) ? null : scene.game.player.timer.delay,
      score: scene.game.player.score,
    },
    // Animation information
    player_anim_is_playing: scene.game.player.anims.isPlaying,
    player_anim_key: scene.game.player.anims.getCurrentKey(),
    robot_anim_key: null,
    active_player_movement_timer: scene.game.player.movementTimer != null,
    // Distraction Task Information
    distractionTaskTimerSecs: scene.game.distractionTaskTimerSecs,
  };
  if (scene.game.robot) {
    retval.robot = {
      currentTile: scene.game.robot.currentTile,
      plan: scene.game.robot.plan,
      currentState: scene.game.robot.currentState,
      previousState: scene.game.robot.previousState,
      helpBubbleVisible: scene.game.robot.helpBubble.getVisible(),
      currentActionI: scene.game.robot.currentActionI,
    };
    retval.active_robot_movement_timer = scene.game.robot.movementTimer != null;
  }
  for (dataKey in additionalData) {
    retval[dataKey] = additionalData[dataKey];
  }
  return retval;
}

function logData(endpoint, data) {
  var url = baseURL + endpoint;
  // console.log("Send ", data)
  $.ajax({
    type : "POST",
    url : url,
    data: JSON.stringify(data, null, '\t'),
    contentType: 'application/json;charset=UTF-8',
    success: function(received_data, status) {
        // console.log(`${received_data} and status is ${status}`);
    }
  });
}

function loadUpdate(scene) {
  scene.game.prevHelpBubbleVisible = false;
  if (dataToLoad.length > 0) {
    var currentTime = Date.now();
    var dtime = currentTime - scene.game.start_time;
    while (dataToLoad.length > 1) {

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
          var queryType = scene.game.tasks.robotActions[scene.game.robot.currentActionI].robotAction.query;
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
        scene.game.player.movementTimer = null;
      } else if (lastLoadedData != null && dataToLoad[0].active_player_movement_timer && !lastLoadedData.active_player_movement_timer && scene.game.player.movementTimer == null) {
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
        scene.game.robot.movementTimer = null;
      } else if (lastLoadedData != null && dataToLoad[0].active_robot_movement_timer && !lastLoadedData.active_robot_movement_timer && scene.game.robot.movementTimer == null) {
        scene.game.robot.movementTimer = scene.time.addEvent({delay: robotMsPerStep});
      }

      if (scene.game.prevHelpBubbleVisible && !dataToLoad[0].robot.helpBubbleVisible) {
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

      var next_dtime = dataToLoad[1].dtime;
      if (dtime >= next_dtime) {
        lastLoadedData = dataToLoad.splice(0, 1);
      } else {
        lastLoadedData = dataToLoad[0];
        break;
      }
    }

    scene.game.lastLoadUpdateTime = currentTime;

    if (dataToLoad.length == 1) {
      console.log("Finished Playback!");
      dataToLoad = []
    }
  }
}
