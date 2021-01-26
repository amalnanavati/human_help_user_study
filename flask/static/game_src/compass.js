function createCompass(scene) {
  // Add the compass
  scene.game.compass = {};
  scene.game.compass.radius = tileSize*1.0
  scene.game.compass.circle = scene.add.graphics({ x: 0, y: 0 });
  scene.game.compass.circle.fillStyle(0x000000, 0.5);
  scene.game.compass.circle.lineStyle(4, 0xececec, 0.5);
  scene.game.compass.circle.fillCircle(0, 0, scene.game.compass.radius);
  scene.game.compass.circle.setDepth(13);//3);//

  scene.game.compass.playerArrow = scene.add.graphics({ x: 0, y: 0 });
  scene.game.compass.playerArrow.lineStyle(4, playerColor, 0.5);
  scene.game.compass.playerArrow.lineBetween(0, 0, scene.game.compass.radius, 0);
  scene.game.compass.playerArrow.setDepth(14);//4);//
  scene.game.compass.playerGoalText = scene.add.text(scene.game.compass.radius, 0, "", {
    font: "24px monospace",
    fill: playerColorStr,
    padding: { x: 0, y: 0 },
    align: "center",
    backgroundColor: "rgba(236, 236, 236, 0.75)",
  });
  scene.game.compass.playerGoalText.setDepth(14);//4);//

  scene.game.compass.robotArrow = scene.add.graphics({ x: 0, y: 0 });
  scene.game.compass.robotArrow.lineStyle(4, robotColor, 0.5);
  scene.game.compass.robotArrow.lineBetween(0, 0, scene.game.compass.radius, 0);
  scene.game.compass.robotArrow.setDepth(14);//4);//
  scene.game.compass.robotGoalText = scene.add.text(scene.game.compass.radius, 0, "", {
    font: "24px monospace",
    fill: robotColorStr,
    padding: { x: 0, y: 0 },
    align: "center",
    backgroundColor: "#ececec",
  });
  scene.game.compass.robotGoalText.setDepth(14);//4);/
}

function updateCompass(scene) {
  scene.game.compass.circle.x = scene.game.player.x;
  scene.game.compass.circle.y = scene.game.player.y;

  if (scene.game.player.taskPlan == null || scene.game.player.taskPlan.length == 0) {
    scene.game.compass.playerArrow.setVisible(false);
    scene.game.compass.playerGoalText.setVisible(false);
  } else if (scene.game.player.taskI < scene.game.tasks.tasks.length) {
    scene.game.compass.playerArrow.setVisible(true);
    var goal = scene.game.player.taskPlan[scene.game.player.taskPlan.length - 1];
    var rotation = Math.atan2(goal.y - scene.game.player.currentTile.y, goal.x - scene.game.player.currentTile.x)
    scene.game.compass.playerArrow.rotation = rotation;
    scene.game.compass.playerArrow.x = scene.game.compass.circle.x;
    scene.game.compass.playerArrow.y = scene.game.compass.circle.y;

    scene.game.compass.playerGoalText.setVisible(true);
    scene.game.compass.playerGoalText.text = scene.game.tasks.tasks[scene.game.player.taskI].semanticLabel + "\nDist: "+scene.game.player.taskPlan.length;
    var origin = rotationToOrigin(rotation);
    scene.game.compass.playerGoalText.setOrigin(origin.x, origin.y);
    scene.game.compass.playerGoalText.x = scene.game.compass.playerArrow.x + scene.game.compass.radius*Math.cos(rotation);
    scene.game.compass.playerGoalText.y = scene.game.compass.playerArrow.y + scene.game.compass.radius*Math.sin(rotation);
  }

  if (scene.game.robot && (scene.game.robot.isBeingLed || (scene.game.robot.actionInProgress && scene.game.robot.currentState == robotState.STATIONARY && scene.game.robot.helpBubble.getVisible())) && scene.game.robot.currentActionI < scene.game.tasks.robotActions.length && scene.game.player.taskI == scene.game.tasks.robotActions[scene.game.robot.currentActionI].afterHumanTaskIndex + 1 && scene.game.tasks.robotActions[scene.game.robot.currentActionI].robotAction.query != "walkPast" /*&& scene.game.robot.taskPlan != null && scene.game.robot.taskPlan.length > 0*/) {
    scene.game.compass.robotArrow.setVisible(true);
    var goalSemanticLabel = scene.game.tasks.robotActions[scene.game.robot.currentActionI].robotAction.targetSemanticLabel + pointOfInterestString + "1";
    console.log("goalSemanticLabel", goalSemanticLabel, scene.game.robot.currentActionI, scene.game.tasks.robotActions[scene.game.robot.currentActionI]);
    var goal = scene.game.semanticLabelsToXY[goalSemanticLabel][0];
    // console.log("scene.game.robot.taskPlan", scene.game.robot.taskPlan, goal);
    var rotation = Math.atan2(goal.y - scene.game.player.currentTile.y, goal.x - scene.game.player.currentTile.x)
    scene.game.compass.robotArrow.rotation = rotation;
    scene.game.compass.robotArrow.x = scene.game.compass.circle.x;
    scene.game.compass.robotArrow.y = scene.game.compass.circle.y;

    scene.game.compass.robotGoalText.setVisible(true);
    var distanceEstimate = scene.game.robot.taskPlan.length > 0 ? scene.game.robot.taskPlan.length : Math.abs(scene.game.player.currentTile.x-goal.x)+Math.abs(scene.game.player.currentTile.y-goal.y);
    scene.game.compass.robotGoalText.text = scene.game.tasks.robotActions[scene.game.robot.currentActionI].robotAction.targetSemanticLabel + "\nDist: "+distanceEstimate;
    var origin = rotationToOrigin(rotation);
    scene.game.compass.robotGoalText.setOrigin(origin.x, origin.y);
    scene.game.compass.robotGoalText.x = scene.game.compass.robotArrow.x + scene.game.compass.radius*Math.cos(rotation);
    scene.game.compass.robotGoalText.y = scene.game.compass.robotArrow.y + scene.game.compass.radius*Math.sin(rotation);
  } else {
    scene.game.compass.robotArrow.setVisible(false);
    scene.game.compass.robotGoalText.setVisible(false);
  }
}

function rotationToOrigin(rotation) {
  if ((rotation >= -Math.PI/4 && rotation <= 0) || (rotation <= Math.PI/4 && rotation >= 0)) {
    originX = 0;
    originY = (rotation + Math.PI/4)/(Math.PI/2);
  } else if (rotation <= -Math.PI/4 && rotation >= -3*Math.PI/4) {
    originX = (-rotation - Math.PI/4)/(Math.PI/2);
    originY = 1;
  } else if (rotation <= -3*Math.PI/4 || rotation >= 3*Math.PI/4) {
    originX = 1;
    if (rotation < 0) {
      originY = (-rotation-3*Math.PI/4)/(Math.PI/2);
    } else {
      originY = (rotation-3*Math.PI/4)/(Math.PI/2);
    }
  } else if (rotation >= Math.PI/4 && rotation <= 3*Math.PI/4) {
    originX = (rotation - Math.PI/4)/(Math.PI/2);
    originY = 0;
  } else {
    throw "rotation that did not fit in range "+rotation.toString();
  }
  return {x: originX, y: originY};
}
