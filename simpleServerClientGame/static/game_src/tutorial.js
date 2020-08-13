const tutorialText = {
  1 : "This is your character. Hold down the arrow keys to move them around.",
  2 : "These are the room labels in this environment. Navigate to Room 43.",
  3 : "Great! Now, navigate to Room 5.",
  4 : "Your job is to maintain the computers. Move to the highlighted computer's keyboard and hold down the Space bar.",
  5 : "This is your compass. It tells you the direction and distance to your goal. Use your compass to navigate to Room 22 and clear computer viruses.",
  6 : "The header shows you game information. Go to Room 4 before the time runs out!",
  7 : "For every repaired computer, you get +10 points. For every second late you arrive, you get -1 point. Go to Room 30.",
  8 : "Sometimes, you will get break time. Go to the Game Room and take a break. Meanwhile, keep your eyes open for the office robot.",
  // 9 : "Sometimes, you will see a robot moving around the building. Go to the Room 8, and keep your eyes open for the robot.",
  9 : "The robot is new and still learning about the building. It will sometimes ask for help. Go to Room 7. When the robot asks for help, ignore it and walk past.",
  10 : "Nice! Now go to Room 47. When the robot asks for help, say \"Yes\" and drop it off near its goal.",
  // 12 : "Nice! Now go to Room 6. When the robot asks for help, say \"Can't Help\" and continue on your way.",
  11 : "There are three ways to interact with the robot: 1) ignore; 2) \"Yes\"; and 3) \"Can't Help\". Take a break in the Lounge. When the robot asks for help, you can decide how you want to interact with it.",
};

function createTutorialTextBox(scene) {
  // For the Speech Bubble only, (x,y) is in the bottom-left corner.
  // Generally in Phaser3 it is top-left (although it can be changed
  // with the setOrigin() method)
  var width = scene.game.camera.width*2/5;
  var x = scene.game.camera.width/2;
  var y = scene.game.camera.height/2;
  scene.game.tutorialTextBox = new SpeechBubble(
    scene, width, x, y, tutorialText[1],
    [
      {
        text : "Next",
        rowI: 0,
        callbackFunction : function () {
          scene.game.tutorialHighlight.setVisible(false);
          scene.game.tutorialTextBox.setVisible(false);
          scene.game.isRunning = true;
          scene.game.helpButton.setVisible(true);
          scene.game.tutorialTextBox.additionalCallback();
          if (!load) logData(tutorial ? logTutorialStateEndpoint : logGameStateEndpoint, getGameState(scene, eventType.TUTORIAL_NEXT_BUTTON_PRESSED));
        },
      },
    ],
    false,
  );
  scene.game.tutorialTextBox.additionalCallback = function() {};
  scene.game.tutorialTextBox.setPosition(
    scene.game.camera.width*3/4-scene.game.tutorialTextBox._width/2,
    scene.game.camera.height/2,///4+scene.game.tutorialTextBox.getHeight()/2,
  );
  scene.game.tutorialTextBox.setScrollFactor(0.0, 0.0);
}

function loadStep(scene, step) {
  // Stop the game
  scene.game.isRunning = false;
  if (scene.game.helpButton) scene.game.helpButton.setVisible(false);
  if (scene.game.player) scene.game.player.anims.stop();

  // Create the text box
  if (scene.game.tutorialTextBox) scene.game.tutorialTextBox.setText(tutorialText[step]);
  if (scene.game.tutorialTextBox) scene.game.tutorialTextBox.setVisible(true);

  // Set the help text
  if (scene.game.helpText) scene.game.helpText.setText(tutorialText[step]);
  if (scene.game.helpText) scene.game.helpText.setPosition(
    scene.game.camera.width/2-scene.game.helpText._width/2,
    scene.game.camera.height/2+scene.game.helpText.getHeight()/2,
  );

  switch (step) {
    case 1:
      scene.game.start_time = Date.now(); // ms

      // Create the map
      createMap(scene);

      // Load the tasks for this game ID
      scene.game.tasks = scene.cache.json.get('tasks');

      // Create the player
      createPlayer(scene);

      // Create and configure the camera to follow the player and not leave the map
      createCamera(scene);

      // Configure the keyboard input
      scene.game.cursors = scene.input.keyboard.createCursorKeys();

      // Create the tutorial text box
      createTutorialTextBox(scene);

      // Create the help button
      createHelpButton(scene);
      scene.game.helpButton.setVisible(false);
      scene.game.helpText.setText(tutorialText[step]);
      scene.game.helpText.setPosition(
        scene.game.camera.width/2-scene.game.helpText._width/2,
        scene.game.camera.height/2+scene.game.helpText.getHeight()/2,
      );


      // Circle the player
      scene.game.tutorialHighlight = scene.add.graphics({x:scene.game.player.x, y: scene.game.player.x});
      scene.game.tutorialHighlight.lineStyle(16, playerColor, 0.5);
      scene.game.tutorialHighlight.strokeCircle(0, 0, tileSize*1.3);
      scene.game.tutorialHighlight.setDepth(15);
      scene.game.tutorialHighlight.setScrollFactor(0.0, 0.0);
      if (!load) logData(tutorial ? logTutorialConfigEndpoint : logGameConfigEndpoint, getGameConfig(scene));
      break;
    case 2:
      // Highlight the game element
      for (labelName in scene.game.roomLabels) {
        var labels = scene.game.roomLabels[labelName];
        for (var label of labels) {
          var x = label.x;
          var y = label.y;
          if (isOnCamera(scene, x, y, 0)) {
            scene.game.tutorialHighlight.setPosition(x-scene.game.camera.scrollX, y-scene.game.camera.scrollY);
            break;
          }
        }
      }
      scene.game.tutorialHighlight.setVisible(true);
      break;
    case 4:
      // Create the window that is shown during the distraction task
      createDistractionTaskBar(scene);
      setDistractionTaskBarVisible(scene, false);
      // Create the box that will highlight our goal location
      createHighlightBox(scene);
      var targetTile = null;
      var targetStr = "Room 5" + highlightPointString + game.tasks.tasks[game.player.taskI].target;
      targetTile = game.semanticLabelsToXY[targetStr][0];
      var adjacentStr = "Room 5" + pointOfInterestString + game.tasks.tasks[game.player.taskI].target;
      adjacentTile = game.semanticLabelsToXY[adjacentStr][0];
      updateHighlightBox(scene, true, targetTile, adjacentTile);
      break;
    case 5:
      // Create the compass
      createCompass(scene);
      updateCompass(scene);
      // Highlight the compass
      scene.game.tutorialHighlight.setPosition(scene.game.player.x-scene.game.camera.scrollX, scene.game.player.y-scene.game.camera.scrollY);
      scene.game.tutorialHighlight.setVisible(true);
      break;
    case 6:
      // Create the header
      createHeader(scene);
      // updateHeader(scene);
      if (!scene.game.tasks.tasks[scene.game.player.taskI].timeLimit) {
        setTimeLimitFromBusyness(scene);
      }
      scene.game.timeProgressBar.drawBar(0.0, scene.game.tasks.tasks[scene.game.player.taskI].timeLimit*1000);

      // Create the negative score red outline
      createNegativeScoreOutline(scene);

      scene.game.tutorialTextBox.additionalCallback = function() {
        initializeGamePlayerTimer(scene);
      }
      break;
    case 8:
      //Create the robot
      createRobot(scene);
      // Create the robot help bubble
      createRobotHelpBubble(scene);
      break;
  }

  if (!load) logData(tutorial ? logTutorialStateEndpoint : logGameStateEndpoint, getGameState(scene, eventType.TUTORIAL_LOAD_STATE));
  scene.game.tutorialStep = step;
}

function tutorialUpdate(scene) {
  // console.log("scene.game.tutorialStep", scene.game.tutorialStep);
  switch (scene.game.tutorialStep) {
    case 1:
      if (scene.game.player.elapsedDistanceSinceComputingTaskPlan > 0 && scene.game.tutorialStep1Timer == null) {
        scene.game.tutorialStep1Timer = scene.time.addEvent({
          delay: 7*1000, // ms
          loop: false,
          callback: function() {
                loadStep(scene, 2);
          },
        });
      }
      break;
    case 2:
      var currentLocationKey = String([scene.game.player.currentTile.x, scene.game.player.currentTile.y]);
      if (currentLocationKey in scene.game.xyToSemanticLabels) {
        var currentSemanticLabels = scene.game.xyToSemanticLabels[currentLocationKey];
        var goalSemanticLabel = "Room 43";
        if (currentSemanticLabels.has(goalSemanticLabel)) {
          loadStep(scene, 3);
        }
      }
      break;
    case 3:
      var currentLocationKey = String([scene.game.player.currentTile.x, scene.game.player.currentTile.y]);
      if (currentLocationKey in scene.game.xyToSemanticLabels) {
        var currentSemanticLabels = scene.game.xyToSemanticLabels[currentLocationKey];
        var goalSemanticLabel = "Room 5";
        if (currentSemanticLabels.has(goalSemanticLabel)) {
          loadStep(scene, 4);
        }
      }
      break;
    case 4:
    case 5:
    case 6:
    case 7:
    case 8:
    case 9:
    case 10:
    case 11:
    case 12:
      if (scene.game.player.taskI == scene.game.tutorialStep-2 && scene.game.player.currentState == playerState.NAVIGATION_TASK) {
        // Have completed distraction task
        loadStep(scene, scene.game.tutorialStep+1);
      }
      break;
  }
}
