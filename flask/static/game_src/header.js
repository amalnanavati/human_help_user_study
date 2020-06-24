function createHeader(scene) {
  var offset = 16;
  var fontSize = 26;
  scene.game.instructionText = scene.add.text(offset, /*tileSize+*/tileSize/2, "Arrow keys to move", {
    font: fontSize.toString()+"px monospace",
    fill: "#ffffff",//"#ececec",
    // padding: { x: offset, y: offset },
    backgroundColor: "#000000",
    // wordWrap: {
    //   width: maxWidth,
    // },
  });
  scene.game.instructionText.setOrigin(0.0, 0.5); // top-left
  scene.game.instructionText.setScrollFactor(0);
  scene.game.instructionText.setDepth(6);

  scene.game.scoreText = scene.add.text(scene.game.config.width-offset, /*tileSize+*/tileSize/2, "Score: 0", {
    font: fontSize.toString()+"px monospace",
    fill: "#ececec",
    // padding: { x: offset, y: offset },
    backgroundColor: "#000000",
    // wordWrap: {
    //   width: maxWidth,
    // },
  });
  scene.game.scoreText.setOrigin(1.0, 0.5); // top-right
  scene.game.scoreText.setScrollFactor(0);
  scene.game.scoreText.setDepth(6);

  var x = scene.game.instructionText.x + scene.game.instructionText.width + 2*offset;
  var height = tileSize*2/3;
  var y = (tileSize-height)/2;
  var width = scene.game.scoreText.x - scene.game.scoreText.width - 2*offset - x;
  // console.log("createHeader", x, y, width, height);
  scene.game.timeProgressBar = new TimeProgressBar(scene, x, y, width, height, negativeScoreRedOutlineBlinker);
}

function updateHeader(scene) {
  scene.game.instructionText.text = "";//scene.game.baseInstructionsStr;
  if (scene.game.player.currentState == playerState.NAVIGATION_TASK || scene.game.player.currentState == playerState.DISTRACTION_TASK) {
    scene.game.instructionText.text += "Goal: "+scene.game.tasks.tasks[scene.game.player.taskI].semanticLabel;
    // var remainingSecs = Math.round((scene.game.player.timer.delay - scene.game.player.timer.getProgress()*scene.game.player.timer.delay)/1000);
    // scene.game.instructionText.text += "\nTime: "+remainingSecs.toString()+" secs";
  } /*else if (scene.game.player.currentState == playerState.DISTRACTION_TASK) {
    scene.game.instructionText.text += "Hold Space at the red computer.";
  }*/ else if (scene.game.player.currentState == playerState.COMPLETED_TASKS) {
    scene.game.instructionText.text += "Completed tasks!";
  }

  scene.game.scoreText.text = "Score: " + scene.game.player.score.toString();

  var offset = 16;

  var x = scene.game.instructionText.x + scene.game.instructionText.width + 2*offset;
  var width = scene.game.scoreText.x - scene.game.scoreText.width - 2*offset - x;
  scene.game.timeProgressBar.setX(x);
  scene.game.timeProgressBar.setWidth(width);

  // console.log("updateHeader", scene.game.timeProgressBar.timeProgressBar, scene.game.timeProgressBar.timeProgressBarStroke);

  if (scene.game.player.currentState == playerState.COMPLETED_TASKS) {
    scene.game.timeProgressBar.removeBar();
    scene.game.timeProgressBar.setText("Congratulations!");
  } else if (scene.game.player.timer != null) {
    scene.game.timeProgressBar.drawBar(scene.game.player.timer);
    scene.game.timeProgressBar.setText("Time: ");
  } else {
    scene.game.timeProgressBar.removeBar();
    scene.game.timeProgressBar.setText("Take a Break!");
  }
}
