function createHelpButton(scene) {
  // Create the text box
  var width = scene.game.config.width*2/3;
  var x = scene.game.config.width/2 - width/2;
  var y = scene.game.config.height/2;
  scene.game.helpText = new SpeechBubble(
    scene, width, x, y, instructionText,
    [
      {
        text : "Close",
        rowI: 0,
        callbackFunction : function () {
          scene.game.helpText.setVisible(false);
          if (scene.game.player.timer) scene.game.player.timer.paused = false;
          if (scene.game.player.negativeScoreTimer) scene.game.player.negativeScoreTimer.paused = false;
          if (scene.game.tutorialStep1Timer) scene.game.tutorialStep1Timer.paused = false;
          scene.game.isRunning = true;
        },
      },
    ],
    false,
  );
  scene.game.helpText.setPosition(
    scene.game.camera.width/2-scene.game.helpText._width/2,
    scene.game.camera.height/2+scene.game.helpText.getHeight()/2,
  );
  scene.game.helpText.setScrollFactor(0.0, 0.0);
  scene.game.helpText.setVisible(false);
  scene.game.helpText.setDepth(14);

  // Create the help button
  scene.game.helpButton = scene.add.text(
    scene.game.config.width-headerOffset,
    tileSize*1.2,
    "Help",
    {
      font: headerFontSize.toString()+"px monospace",
      fill: "rgba(0, 0, 0, 1.0)",
      backgroundColor: 'rgba(255,0,0,0.75)'
    },
  ).setOrigin(1.0, 0.5).setScrollFactor(0.0, 0.0);
  scene.game.helpButton.setInteractive();
  scene.game.helpButton.on('pointerdown', function(hitArea, x, y) {
    // Make the help text visible
    scene.game.helpText.setVisible(!scene.game.helpText.getVisible());
    if (scene.game.helpText.getVisible()) {
      if (scene.game.player.timer) scene.game.player.timer.paused = true;
      if (scene.game.player.negativeScoreTimer) scene.game.player.negativeScoreTimer.paused = true;
      if (scene.game.tutorialStep1Timer) scene.game.tutorialStep1Timer.paused = true;
      scene.game.isRunning = false;
    } else {
      if (scene.game.player.timer) scene.game.player.timer.paused = false;
      if (scene.game.player.negativeScoreTimer) scene.game.player.negativeScoreTimer.paused = false;
      if (scene.game.tutorialStep1Timer) scene.game.tutorialStep1Timer.paused = false;
      scene.game.isRunning = true;
    }
  }, scene.game.helpButton);
  scene.game.helpButton.setDepth(16);
}
