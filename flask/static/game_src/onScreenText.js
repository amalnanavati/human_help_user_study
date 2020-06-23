function createInstructionText(scene) {
  scene.game.instructionText = scene.add.text(16, 16, "Arrow keys to move", {
    font: "24px monospace",
    fill: "#ececec",
    padding: { x: 20, y: 10 },
    backgroundColor: "#000000"
  });
  scene.game.instructionText.setOrigin(0.0, 0.0); // top-left
  scene.game.instructionText.setScrollFactor(0);
  scene.game.instructionText.setDepth(6);
}

function createScoreText(scene) {
  scene.game.scoreText = scene.add.text(scene.game.config.width-16, 16, "Score: 0", {
    font: "24px monospace",
    fill: "#ececec",
    padding: { x: 20, y: 10 },
    backgroundColor: "#000000"
  });
  scene.game.scoreText.setOrigin(1.0, 0.0); // top-right
  scene.game.scoreText.setScrollFactor(0);
  scene.game.scoreText.setDepth(6);
}

function regenerateInstructionText(scene) {
  scene.game.instructionText.text = "";//scene.game.baseInstructionsStr;
  if (scene.game.player.currentState == playerState.NAVIGATION_TASK) {
    scene.game.instructionText.text += "Goal: "+scene.game.tasks.tasks[scene.game.player.taskI].semanticLabel;
    var remainingSecs = Math.round((scene.game.player.timer.delay - scene.game.player.timer.getProgress()*scene.game.player.timer.delay)/1000);
    scene.game.instructionText.text += "\nTime: "+remainingSecs.toString()+" secs";
  } else if (scene.game.player.currentState == playerState.DISTRACTION_TASK) {
    scene.game.instructionText.text += "Hold Space at the red computer.";
  } else if (scene.game.player.currentState == playerState.COMPLETED_TASKS) {
    scene.game.instructionText.text += "Completed tasks!";
  }
}

function regenerateScoreText(scene) {
  scene.game.scoreText.text = "Score: " + scene.game.player.score.toString();
}
