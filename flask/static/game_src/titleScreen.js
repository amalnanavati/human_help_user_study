const instructionText = "Instructions:\n\n\t1) Use the arrow keys to move. \n\t2) Hold down Space to fix a computer. \n\t3) If the robot talks to you, you can ignore it or click the buttons to respond to it. \n\t4) The instructions on the top tell you where to go and how much time you have left. \n\t5) Every cleaned computer is +10 points. \n\t6) Every second late you arrive is -1 point.";

function createTitleScreen(scene, callbackFunction) {
  var offset = scene.game.config.width/20;
  scene.game.titleScreen = scene.add.graphics({ x: scene.game.config.width/2, y: scene.game.config.height/2 });
  scene.game.titleScreen.fillStyle(0xececec, 1.0);
  scene.game.titleScreen.lineStyle(4, 0x000000, 1.0);
  scene.game.titleScreen.fillRect(-scene.game.config.width/2, -scene.game.config.height/2, scene.game.config.width, scene.game.config.height); // White background
  scene.game.titleScreen.setDepth(16);

  scene.game.titleScreen.title = scene.add.text(
    scene.game.config.width/2,
    offset,
    tutorial ? "Tutorial" : "Office Game",
    {
      font: "32px monospace",
      fill: "rgba(0, 0, 0, 1.0)",
    },
  ).setOrigin(0.5, 1.0);
  scene.game.titleScreen.title.setDepth(16);

  scene.game.titleScreen.description = scene.add.text(
    scene.game.config.width/2,
    scene.game.config.height/2,
    tutorial ? "You are an IT admin at this company, and must perform routine computer maintainence tasks before employees arrive for the day.\n\nAs you do so, you may see the company's mail delivery robot. This robot is new, so it is still learning about the building. \n\nThis tutorial will walk you through the game." : "You are an IT admin at this company, and must perform routine computer maintainence tasks before employees arrive for the day.\n\nAs you do so, you may see the company's mail delivery robot. This robot is new, so it is still learning about the building. \n\n"+instructionText,
    {
      font: "24px monospace",
      fill: "rgba(0, 0, 0, 1.0)",
      wordWrap: {width: scene.game.config.width-2*offset},
    },
  ).setOrigin(0.5, 0.5);
  scene.game.titleScreen.description.setDepth(16);

  scene.game.titleScreen.title.y = scene.game.titleScreen.description.y - scene.game.titleScreen.description.height/2 - scene.game.titleScreen.title.height;

  scene.game.titleScreen.startButton = scene.add.text(
    scene.game.config.width/2,
    scene.game.titleScreen.description.y + scene.game.titleScreen.description.height/2 + scene.game.titleScreen.title.height,
    "Start",
    {
      font: "32px monospace",
      fill: "rgba(0, 0, 0, 1.0)",
      backgroundColor: "rgba(255, 0, 0, 1.0)"
    },
  ).setOrigin(0.5, 0.0);
  scene.game.titleScreen.startButton.setInteractive();
  scene.game.titleScreen.startButton.on('pointerdown', function(hitArea, x, y) {
    // if (!load) {
    //   logData(tutorial ? logTutorialStateEndpoint : logGameStateEndpoint, getGameState(scene, eventType.CLICK, {
    //     buttonName : this.text,
    //     x : this.x - this.width*this.originX + x,
    //     y : this.xy - this.height*this.originY + y,
    //   }));
    // }
    scene.game.titleScreen.startButton.destroy();
    scene.game.titleScreen.description.destroy();
    scene.game.titleScreen.title.destroy();
    scene.game.titleScreen.destroy();
    callbackFunction(scene);
  }, scene.game.titleScreen.startButton);
  scene.game.titleScreen.startButton.setDepth(16);
  // console.log("scene.game.titleScreen.startButton", scene.game.titleScreen.startButton);
}
