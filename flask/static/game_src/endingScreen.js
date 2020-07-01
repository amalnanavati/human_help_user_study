function createEndingScreen(scene) {
  var offset = scene.game.config.width/20;
  scene.game.endingScreen = scene.add.graphics({ x: scene.game.config.width/2, y: scene.game.config.height/2 });
  scene.game.endingScreen.fillStyle(0xececec, 1.0);
  scene.game.endingScreen.lineStyle(4, 0x000000, 1.0);
  scene.game.endingScreen.fillRect(-scene.game.config.width/2, -scene.game.config.height/2, scene.game.config.width, scene.game.config.height); // White background
  scene.game.endingScreen.setDepth(16);

  scene.game.endingScreen.title = scene.add.text(
    scene.game.config.width/2,
    offset,
    "Completed Tasks",
    {
      font: "32px monospace",
      fill: "rgba(0, 0, 0, 1.0)",
    },
  ).setOrigin(0.5, 1.0);
  scene.game.endingScreen.title.setDepth(16);

  scene.game.endingScreen.description = scene.add.text(
    scene.game.config.width/2,
    scene.game.config.height/2,
    "You have succesfully cleared all viruses. \n\nScore: "+scene.game.player.score.toString()+" / "+(scene.game.tasks.tasks.length*scorePerTask).toString(),
    {
      font: "24px monospace",
      fill: "rgba(0, 0, 0, 1.0)",
      wordWrap: {width: scene.game.config.width-2*offset},
    },
  ).setOrigin(0.5, 0.5);
  scene.game.endingScreen.description.setDepth(16);

  scene.game.endingScreen.title.y = scene.game.endingScreen.description.y - scene.game.endingScreen.description.height/2 - scene.game.endingScreen.title.height;

  scene.game.endingScreen.continueButton = scene.add.text(
    scene.game.config.width/2,
    scene.game.endingScreen.description.y + scene.game.endingScreen.description.height/2 + scene.game.endingScreen.title.height,
    "Continue",
    {
      font: "32px monospace",
      fill: "rgba(0, 0, 0, 1.0)",
      backgroundColor: "rgba(255, 0, 0, 1.0)"
    },
  ).setOrigin(0.5, 0.0);
  scene.game.endingScreen.continueButton.setInteractive();
  scene.game.endingScreen.continueButton.on('pointerdown', function(hitArea, x, y) {
    // if (!load) {
    //   logData(logGameStateEndpoint, getGameState(scene, eventType.CLICK, {
    //     buttonName : this.text,
    //     x : this.x - this.width*this.originX + x,
    //     y : this.xy - this.height*this.originY + y,
    //   }));
    // }
    
    // scene.game.endingScreen.continueButton.destroy();
    // scene.game.endingScreen.description.destroy();
    // scene.game.endingScreen.title.destroy();
    // scene.game.endingScreen.destroy();
    post_form('/post_survey', {uuid: uuid});
  }, scene.game.endingScreen.continueButton);
  scene.game.endingScreen.continueButton.setDepth(16);

  scene.game.endingScreen.setScrollFactor(0.0, 0.0);
  scene.game.endingScreen.title.setScrollFactor(0.0, 0.0);
  scene.game.endingScreen.description.setScrollFactor(0.0, 0.0);
  scene.game.endingScreen.continueButton.setScrollFactor(0.0, 0.0);

  console.log("Created ending screen");
}
