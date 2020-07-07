const tutorialStep1Text = "This is your character. Hold down the arrow keys to move them around.";
const tutorialStep2Text = "These are the room labels in this environment. Navigate to Room 43.";
const tutorialStep3Text = "Great! Now, navigate to Room 5.";
const tutorialStep4Text = "Your job is to maintain the computers. Move to the highlighted computer and hold down the Space bar.";
const tutorialStep5Text = "This is your compass. Use your compass to navigate to Room 22 and clear viruses."
const tutorialStep6Text = "The header shows you game information. Go to Room 4 before the time runs out!"
const tutorialStep7Text = "For every fixed computer, you get +10 points. For every second late you arrive, you get -1 point. Go to Room 30."
const tutorialStep8Text = "Sometimes, you will get break time. Go to the Game Room and take a break."
const tutorialStep9Text = "Sometimes, you will see a robot moving around the building. Go to the Room 8, and keep your eyes open for the robot."
const tutorialStep10Text = "The robot is new and still learning about the building. It will sometimes ask for help. Go to Room 20. When the robot asks for help, ignore it and walk past."
const tutorialStep11Text = "Nice! Now go to Room 47. When the robot asks for help, say \"Yes\" and lead it to its goal."
const tutorialStep12Text = "Nice! Now go to Room 6. When the robot asks for help, say \"Can't Help\" and continue on your way."
const tutorialStep13Text = "You have now learned every way to interact with the robot: 1) ignore; 2) \"Yes\"; and 3) \"Can't Help\". Take a break in the Lounge. When the robot asks for help, decide how you want to interact with it."

function createTutorialTextBox(scene) {
  // For the Speech Bubble only, (x,y) is in the bottom-left corner.
  // Generally in Phaser3 it is top-left (although it can be changed
  // with the setOrigin() method)
  var width = scene.game.camera.width*2/5;
  var x = scene.game.camera.width/2;
  var y = scene.game.camera.height/2;
  scene.game.tutorialTextBox = new SpeechBubble(
    scene, width, x, y, tutorialStep1Text,
    [
      {
        text : "Next",
        rowI: 0,
        callbackFunction : function () {
          scene.game.tutorialHighlight.setVisible(false);
          scene.game.tutorialTextBox.setVisible(false);
          scene.game.isRunning = true;
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
  scene.game.tutorialTextBox.setText(tutorialStep1Text); // This is probably a bug in SpeechBubble, but it only really re-renders after calling setText
  scene.game.tutorialTextBox.setScrollFactor(0.0, 0.0);
}

function loadStep1(scene) {
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

  // Circle the player
  scene.game.tutorialHighlight = scene.add.graphics({x:scene.game.player.x, y: scene.game.player.x});
  scene.game.tutorialHighlight.lineStyle(16, playerColor, 0.5);
  scene.game.tutorialHighlight.strokeCircle(0, 0, tileSize*1.3);
  scene.game.tutorialHighlight.setDepth(15);
  scene.game.tutorialHighlight.setScrollFactor(0.0, 0.0);

  // Start the game
  scene.game.isRunning = false;
  scene.game.start_time = Date.now(); // ms
  scene.game.tutorialStep = 1;

  // Start logging
  if (!load) {
    logData(tutorial ? logTutorialConfigEndpoint : logGameConfigEndpoint, getGameConfig(scene));
    logData(tutorial ? logTutorialStateEndpoint : logGameStateEndpoint, getGameState(scene, eventType.TUTORIAL_LOAD_STATE));
  }
}

function loadStep2(scene) {
  // Stop the game
  scene.game.isRunning = false;
  if (!load) logData(tutorial ? logTutorialStateEndpoint : logGameStateEndpoint, getGameState(scene, eventType.TUTORIAL_LOAD_STATE));
  scene.game.player.anims.stop();

  // Create the text box
  scene.game.tutorialTextBox.setText(tutorialStep2Text);
  scene.game.tutorialTextBox.setVisible(true);

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

  // Set the tutorialStep
  scene.game.tutorialStep = 2;
}

function loadStep3(scene) {
  // Stop the game
  scene.game.isRunning = false;
  if (!load) logData(tutorial ? logTutorialStateEndpoint : logGameStateEndpoint, getGameState(scene, eventType.TUTORIAL_LOAD_STATE));
  scene.game.player.anims.stop();

  // Create the text box
  scene.game.tutorialTextBox.setText(tutorialStep3Text);
  scene.game.tutorialTextBox.setVisible(true);

  // Set the tutorialStep
  scene.game.tutorialStep = 3;
}

function loadStep4(scene) {
  // Stop the game
  scene.game.isRunning = false;
  if (!load) logData(tutorial ? logTutorialStateEndpoint : logGameStateEndpoint, getGameState(scene, eventType.TUTORIAL_LOAD_STATE));
  scene.game.player.anims.stop();

  // Create the window that is shown during the distraction task
  createDistractionTaskBar(scene);
  setDistractionTaskBarVisible(scene, false);
  // Create the box that will highlight our goal location
  createHighlightBox(scene);
  var targetTile = null;
  var targetStr = "Room 5" + highlightPointString + "8";
  targetTile = game.semanticLabelsToXY[targetStr][0];
  updateHighlightBox(scene, true, targetTile);

  // Create the text box
  scene.game.tutorialTextBox.setText(tutorialStep4Text);
  scene.game.tutorialTextBox.setVisible(true);

  // Set the tutorialStep
  scene.game.tutorialStep = 4;
}

function loadStep5(scene) {
  // Stop the game
  scene.game.isRunning = false;
  if (!load) logData(tutorial ? logTutorialStateEndpoint : logGameStateEndpoint, getGameState(scene, eventType.TUTORIAL_LOAD_STATE));
  scene.game.player.anims.stop();

  // var targetTile = null;
  // var targetStr = "Room 22" + highlightPointString + "2";
  // targetTile = game.semanticLabelsToXY[targetStr][0];
  // updateHighlightBox(scene, true, targetTile);

  // Create the compass
  createCompass(scene);
  updateCompass(scene);

  // Create the text box
  scene.game.tutorialTextBox.setText(tutorialStep5Text);
  scene.game.tutorialTextBox.setVisible(true);
  console.log(scene.game.camera.height, scene.game.tutorialTextBox.getHeight());
  // scene.game.tutorialTextBox.setPosition(
  //   scene.game.camera.width*3/4-scene.game.tutorialTextBox._width/2,
  //   scene.game.camera.height/2+scene.game.tutorialTextBox.getHeight()/2,
  // );

  // Highlight the compass
  scene.game.tutorialHighlight.setPosition(scene.game.player.x-scene.game.camera.scrollX, scene.game.player.y-scene.game.camera.scrollY);
  scene.game.tutorialHighlight.setVisible(true);

  // Set the tutorialStep
  scene.game.tutorialStep = 5;
}

function loadStep6(scene) {
  // Stop the game
  scene.game.isRunning = false;
  if (!load) logData(tutorial ? logTutorialStateEndpoint : logGameStateEndpoint, getGameState(scene, eventType.TUTORIAL_LOAD_STATE));
  scene.game.player.anims.stop();

  // Create the header
  createHeader(scene);
  // updateHeader(scene);
  console.log("scene.game.timeProgressBar.text.text", scene.game.timeProgressBar.text.text);
  scene.game.timeProgressBar.drawBar(0.0, scene.game.tasks.tasks[scene.game.player.taskI].timeLimit);
  console.log("scene.game.timeProgressBar.text.text", scene.game.timeProgressBar.text.text);

  // Create the negative score red outline
  createNegativeScoreOutline(scene);

  // Create the text box
  scene.game.tutorialTextBox.setText(tutorialStep6Text);
  scene.game.tutorialTextBox.setVisible(true);
  scene.game.tutorialTextBox.additionalCallback = function() {
    initializeGamePlayerTimer(scene);
  }

  // Highlight the time progress bar
  // console.log("horiz", scene.game.timeProgressBar.x, scene.game.timeProgressBar.width, scene.game.camera.scrollX);
  // console.log("vert", scene.game.timeProgressBar.y, scene.game.timeProgressBar.height, scene.game.camera.scrollY);
  // scene.game.tutorialHighlight.setPosition(
  //   scene.game.timeProgressBar.x+scene.game.timeProgressBar.width/2,//-scene.game.camera.scrollX,
  //   scene.game.timeProgressBar.y+scene.game.timeProgressBar.height/2,//-scene.game.camera.scrollY,
  // );
  // scene.game.tutorialHighlight.setVisible(true);

  // Set the tutorialStep
  scene.game.tutorialStep = 6;
}

function loadStep7(scene) {
  // Stop the game
  scene.game.isRunning = false;
  if (!load) logData(tutorial ? logTutorialStateEndpoint : logGameStateEndpoint, getGameState(scene, eventType.TUTORIAL_LOAD_STATE));
  scene.game.player.anims.stop();

  // Create the text box
  scene.game.tutorialTextBox.setText(tutorialStep7Text);
  scene.game.tutorialTextBox.setVisible(true);
  // scene.game.tutorialTextBox.additionalCallback = function() {};

  // Set the tutorialStep
  scene.game.tutorialStep = 7;
}

function loadStep8(scene) {
  // Stop the game
  scene.game.isRunning = false;
  if (!load) logData(tutorial ? logTutorialStateEndpoint : logGameStateEndpoint, getGameState(scene, eventType.TUTORIAL_LOAD_STATE));
  scene.game.player.anims.stop();

  // Create the text box
  scene.game.tutorialTextBox.setText(tutorialStep8Text);
  scene.game.tutorialTextBox.setVisible(true);
  // scene.game.tutorialTextBox.additionalCallback = function() {};

  // Set the tutorialStep
  scene.game.tutorialStep = 8;
}

function loadStep9(scene) {
  // Stop the game
  scene.game.isRunning = false;
  if (!load) logData(tutorial ? logTutorialStateEndpoint : logGameStateEndpoint, getGameState(scene, eventType.TUTORIAL_LOAD_STATE));
  scene.game.player.anims.stop();

  //Create the robot
  createRobot(scene);
  // Create the robot help bubble
  createRobotHelpBubble(scene);

  // Create the text box
  scene.game.tutorialTextBox.setText(tutorialStep9Text);
  scene.game.tutorialTextBox.setVisible(true);
  // scene.game.tutorialTextBox.additionalCallback = function() {};

  // Set the tutorialStep
  scene.game.tutorialStep = 9;
}

function loadStep10(scene) {
  // Stop the game
  scene.game.isRunning = false;
  if (!load) logData(tutorial ? logTutorialStateEndpoint : logGameStateEndpoint, getGameState(scene, eventType.TUTORIAL_LOAD_STATE));
  scene.game.player.anims.stop();

  // Create the text box
  scene.game.tutorialTextBox.setText(tutorialStep10Text);
  scene.game.tutorialTextBox.setVisible(true);
  // scene.game.tutorialTextBox.additionalCallback = function() {};

  // Set the tutorialStep
  scene.game.tutorialStep = 10;
}

function loadStep11(scene) {
  // Stop the game
  scene.game.isRunning = false;
  if (!load) logData(tutorial ? logTutorialStateEndpoint : logGameStateEndpoint, getGameState(scene, eventType.TUTORIAL_LOAD_STATE));
  scene.game.player.anims.stop();

  // Create the text box
  scene.game.tutorialTextBox.setText(tutorialStep11Text);
  scene.game.tutorialTextBox.setVisible(true);
  // scene.game.tutorialTextBox.additionalCallback = function() {};

  // Set the tutorialStep
  scene.game.tutorialStep = 11;
}

function loadStep12(scene) {
  // Stop the game
  scene.game.isRunning = false;
  if (!load) logData(tutorial ? logTutorialStateEndpoint : logGameStateEndpoint, getGameState(scene, eventType.TUTORIAL_LOAD_STATE));
  scene.game.player.anims.stop();

  // Create the text box
  scene.game.tutorialTextBox.setText(tutorialStep12Text);
  scene.game.tutorialTextBox.setVisible(true);
  // scene.game.tutorialTextBox.additionalCallback = function() {};

  // Set the tutorialStep
  scene.game.tutorialStep = 12;
}

function loadStep13(scene) {
  // Stop the game
  scene.game.isRunning = false;
  if (!load) logData(tutorial ? logTutorialStateEndpoint : logGameStateEndpoint, getGameState(scene, eventType.TUTORIAL_LOAD_STATE));
  scene.game.player.anims.stop();

  // Create the text box
  scene.game.tutorialTextBox.setText(tutorialStep13Text);
  scene.game.tutorialTextBox.setVisible(true);
  // scene.game.tutorialTextBox.additionalCallback = function() {};

  // Set the tutorialStep
  scene.game.tutorialStep = 13;
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
                loadStep2(scene);
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
          loadStep3(scene);
        }
      }
      break;
    case 3:
      var currentLocationKey = String([scene.game.player.currentTile.x, scene.game.player.currentTile.y]);
      if (currentLocationKey in scene.game.xyToSemanticLabels) {
        var currentSemanticLabels = scene.game.xyToSemanticLabels[currentLocationKey];
        var goalSemanticLabel = "Room 5";
        if (currentSemanticLabels.has(goalSemanticLabel)) {
          loadStep4(scene);
        }
      }
      break;
    case 4:
      if (scene.game.player.taskI == 2 && scene.game.player.currentState == playerState.NAVIGATION_TASK) {
        // Have completed distraction task
        loadStep5(scene);
      }
      break;
    case 5:
      if (scene.game.player.taskI == 3 && scene.game.player.currentState == playerState.NAVIGATION_TASK) {
        // Have completed distraction task
        loadStep6(scene);
      }
      break;
    case 6:
      if (scene.game.player.taskI == 4 && scene.game.player.currentState == playerState.NAVIGATION_TASK) {
        // Have completed distraction task
        loadStep7(scene);
      }
      break;
    case 7:
      if (scene.game.player.taskI == 5 && scene.game.player.currentState == playerState.NAVIGATION_TASK) {
        // Have completed distraction task
        loadStep8(scene);
      }
      break;
    case 8:
      if (scene.game.player.taskI == 6 && scene.game.player.currentState == playerState.NAVIGATION_TASK) {
        // Have completed distraction task
        loadStep9(scene);
      }
      break;
    case 9:
      if (scene.game.player.taskI == 7 && scene.game.player.currentState == playerState.NAVIGATION_TASK) {
        // Have completed distraction task
        loadStep10(scene);
      }
      break;
    case 10:
      if (scene.game.player.taskI == 8 && scene.game.player.currentState == playerState.NAVIGATION_TASK) {
        // Have completed distraction task
        loadStep11(scene);
      }
      break;
    case 11:
      if (scene.game.player.taskI == 9 && scene.game.player.currentState == playerState.NAVIGATION_TASK) {
        // Have completed distraction task
        loadStep12(scene);
      }
      break;
    case 12:
      if (scene.game.player.taskI == 10 && scene.game.player.currentState == playerState.NAVIGATION_TASK) {
        // Have completed distraction task
        loadStep13(scene);
      }
      break;
    case 13:
      if (scene.game.player.taskI == 11 && scene.game.player.currentState == playerState.NAVIGATION_TASK) {
        // // Have completed distraction task
        // scene.game.isRunning = false;
        // createTutorialEndingScreen(scene);
      }
      break;
    default:
      break;
  }
}
