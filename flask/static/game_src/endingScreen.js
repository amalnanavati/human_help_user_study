function createEndingScreen(scene) {
  if (!load) logData(tutorial ? logTutorialStateEndpoint : logGameStateEndpoint, getGameState(scene, eventType.SHOWING_ENDING_SCREEN));

  var offset = scene.game.config.width/20;
  scene.game.endingScreen = scene.add.graphics({ x: scene.game.config.width/2, y: scene.game.config.height/2 });
  scene.game.endingScreen.fillStyle(0xececec, 1.0);
  scene.game.endingScreen.lineStyle(4, 0x000000, 1.0);
  scene.game.endingScreen.fillRect(-scene.game.config.width/2, -scene.game.config.height/2, scene.game.config.width, scene.game.config.height); // White background
  scene.game.endingScreen.setDepth(16);

  if (tutorial) {
    if (scene.game.gameEndedDueToShift || !scene.game.robot || scene.game.robot.numTimesHelped != 0) {
      title = "Completed Tutorial";
      titleColor = "rgba(0, 0, 0, 1.0)";
      body = "Congratulations, you have succesfully completed the tutorial! \n\nPlease be patient as the game log gets saved. This can take several minutes. Wait until the \"Continue\" button appears.";
    } else {
      title = "ERROR: Did Not Follow Instructions";
      titleColor = "rgba(255, 0, 0, 1.0)";
      body = "You did not follow the tutorial instructions, which makes you ineligible for this HIT. Please exit and do not try again. You will not get paid.";
    }
  } else {
    title = "Completed Tasks";
    titleColor = "rgba(0, 0, 0, 1.0)";
    body = "You have succesfully cleared all viruses. \n\nScore: "+scene.game.player.score.toString()+" / "+(scene.game.tasks.tasks.length*scorePerTask).toString()+"\n\nPlease be patient as the game log gets saved. This can take several minutes. Wait until the \"Continue\" button appears.";
  }
  console.log("titleColor", titleColor);

  scene.game.endingScreen.title = scene.add.text(
    scene.game.config.width/2,
    offset,
    title,
    {
      font: "32px monospace",
      fill: titleColor,
    },
  ).setOrigin(0.5, 1.0);
  scene.game.endingScreen.title.setDepth(16);

  scene.game.endingScreen.description = scene.add.text(
    scene.game.config.width/2,
    scene.game.config.height/2,
    body,
    {
      font: "24px monospace",
      fill: "rgba(0, 0, 0, 1.0)",
      wordWrap: {width: scene.game.config.width-2*offset},
    },
  ).setOrigin(0.5, 0.5);
  scene.game.endingScreen.description.setDepth(16);

  scene.game.endingScreen.title.y = scene.game.endingScreen.description.y - scene.game.endingScreen.description.height/2 - scene.game.endingScreen.title.height;


  scene.game.endingScreen.progressBar = new TimeProgressBar(
    scene,
    scene.game.config.width/4,
    scene.game.endingScreen.description.y + scene.game.endingScreen.description.height/2 + scene.game.endingScreen.title.height,
    scene.game.config.width/2,
    32,
    function() {},
    0x008000,
  );
  scene.game.endingScreen.progressBar.setText("Saving Game Log: ");
  scene.game.endingScreen.progressBar.setDepth(16);

  scene.game.endingScreen.setScrollFactor(0.0, 0.0);
  scene.game.endingScreen.title.setScrollFactor(0.0, 0.0);
  scene.game.endingScreen.description.setScrollFactor(0.0, 0.0);

  // createEndingScreenContinueButton(scene);

  console.log("Created ending screen");
}

function updateEndingScreen(scene) {
  if (tutorial && (scene.game.robot && scene.game.robot.numTimesHelped == 0)) {
    return; // do not update the ending screen if the human never helped
  }
  if (scene.game.endingScreen.oldNumReceivedLogs == null || numReceivedLogs != scene.game.endingScreen.oldNumReceivedLogs) {
    if (scene.game.endingScreen.timer) {
      scene.game.endingScreen.timer.destroy();
      scene.game.endingScreen.timer = null;
    }
    scene.game.endingScreen.timer = scene.time.addEvent({
      delay: 60*1000, // 1 minute
      loop: false,
      callback: function() {
        createEndingScreenContinueButton(scene);
      },
    });
  }
  var percent = numSentLogs == 0 ? 100 : Math.floor(numReceivedLogs/numSentLogs*100);
  scene.game.endingScreen.progressBar.drawBar(
    numSentLogs == 0 ? 1.0 : numReceivedLogs/numSentLogs,
    numSentLogs,
    percent.toString()+"%",
  );
  if (numReceivedLogs == numSentLogs) {
    createEndingScreenContinueButton(scene);
  }
  scene.game.endingScreen.oldNumReceivedLogs = numReceivedLogs;
}

function createEndingScreenContinueButton(scene) {
  var relativeTo;
  if (scene.game.endingScreen.progressBar) {
    relativeTo = scene.game.endingScreen.progressBar;
  } else {
    relativeTo = scene.game.endingScreen.description;
  }
  scene.game.endingScreen.continueButton = scene.add.text(
    scene.game.config.width/2,
    relativeTo.y + relativeTo.height + scene.game.endingScreen.title.height,
    // scene.game.endingScreen.description.y + scene.game.endingScreen.description.height/2 + scene.game.endingScreen.title.height,
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
    //   logData(tutorial ? logTutorialStateEndpoint : logGameStateEndpoint, getGameState(scene, eventType.CLICK, {
    //     buttonName : this.text,
    //     x : this.x - this.width*this.originX + x,
    //     y : this.xy - this.height*this.originY + y,
    //   }));
    // }

    // scene.game.endingScreen.continueButton.destroy();
    // scene.game.endingScreen.description.destroy();
    // scene.game.endingScreen.title.destroy();
    // scene.game.endingScreen.destroy();
    if (tutorial) {
      post_form('/game', {uuid: uuid, order: "a"});
    } else {
      post_form('/survey', {uuid: uuid, gid: gid, order: order});
    }
  }, scene.game.endingScreen.continueButton);
  scene.game.endingScreen.continueButton.setDepth(16);

  scene.game.endingScreen.continueButton.setScrollFactor(0.0, 0.0);
}
