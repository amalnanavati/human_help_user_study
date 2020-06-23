function createMinimap(scene) {
  scene.game.minimap = scene.physics.add.sprite(scene.game.config.width/2, scene.game.config.width/2, 'minimap');
  scene.game.minimap.setScale(0.075);
  scene.game.minimap.setOrigin(0.0, 0.0); // bottom-right
  scene.game.minimap.setDepth(15);
  scene.game.minimap.setAlpha(0.85);
  var minimapOffset = scene.game.config.width/100;
  // scene.game.minimap.cameraOffset.setTo(200, 500)
  scene.game.minimap.setPosition(minimapOffset + scene.game.camera.scrollX, scene.game.config.height-minimapOffset-scene.game.minimap.displayHeight+scene.game.camera.scrollY);
  // scene.game.minimap.fixedToCamera = true;
  scene.game.minimap.setScrollFactor(0.0, 0.0);
  scene.game.minimap.enableBody();

  scene.game.minimap.cameraBox = scene.add.graphics({ x: 0, y: 0 });
  scene.game.minimap.cameraBox.fillStyle(0x898989, 0.5);
  scene.game.minimap.cameraBox.lineStyle(2, 0x000000, 0.5);
  scene.game.minimap.cameraBox.setScrollFactor(0.0, 0.0);
  scene.game.minimap.cameraBox.setDepth(15);
  scene.game.minimap.cameraBox.fillRect(0, 0, scene.game.config.width*scene.game.minimap.scale, scene.game.config.height*scene.game.minimap.scale);
  scene.game.minimap.cameraBox.strokeRect(0, 0, scene.game.config.width*scene.game.minimap.scale, scene.game.config.height*scene.game.minimap.scale);

  scene.game.minimap.playerDot = scene.add.graphics({ x: 0, y: 0 });
  scene.game.minimap.playerDot.fillStyle(playerColor, 0.85);
  scene.game.minimap.playerDot.fillCircle(0, 0, 3);
  scene.game.minimap.playerDot.setDepth(15);
  scene.game.minimap.playerDot.setScrollFactor(0.0, 0.0);

  // Draw a star for the player's goal
  scene.game.minimap.playerGoal = scene.add.graphics({ x: 0, y: 0 });
  scene.game.minimap.playerGoal.lineStyle(2, playerColor, 0.85);
  var points = [];
  for (var i = 0; i < 5; i++) {
    points.push(new Phaser.Geom.Point(8*Math.cos(-Math.PI/2+Math.PI*2*((2*i)%5)/5), 8*Math.sin(-Math.PI/2+Math.PI*2*((2*i)%5)/5)));
  }
  scene.game.minimap.playerGoal.strokePoints(points, true);
  scene.game.minimap.playerGoal.setDepth(15);
  scene.game.minimap.playerGoal.setScrollFactor(0.0, 0.0);
  scene.game.minimap.playerGoal.setVisible(true);

  scene.game.minimap.robotDot = scene.add.graphics({ x: 0, y: 0 });
  scene.game.minimap.robotDot.fillStyle(robotColor, 0.85);
  scene.game.minimap.robotDot.fillCircle(0, 0, 3);
  scene.game.minimap.robotDot.setDepth(15);
  scene.game.minimap.robotDot.setScrollFactor(0.0, 0.0);

  renderPlayerAndCameraOnMinimap(scene);
}

function renderPlayerAndCameraOnMinimap(scene) {
  scene.game.minimap.playerDot.x = scene.game.minimap.x + scene.game.player.x * scene.game.minimap.scale;
  scene.game.minimap.playerDot.y = scene.game.minimap.y + scene.game.player.y * scene.game.minimap.scale;
  scene.game.minimap.cameraBox.x = scene.game.minimap.x + scene.game.camera.scrollX * scene.game.minimap.scale;
  scene.game.minimap.cameraBox.y = scene.game.minimap.y + scene.game.camera.scrollY * scene.game.minimap.scale;
}

function renderPlayerGoalOnMinimap(scene, hasNextGoal, targetTile) {
  if (hasNextGoal) {
    scene.game.minimap.playerGoal.setVisible(true);
    var x = targetTile.x*tileSize;
    var y = targetTile.y*tileSize;
    scene.game.minimap.playerGoal.x = scene.game.minimap.x+(x+tileSize/2)*scene.game.minimap.scale;
    scene.game.minimap.playerGoal.y = scene.game.minimap.y+(y+tileSize/2)*scene.game.minimap.scale;
  } else {
    scene.game.minimap.playerGoal.setVisible(false);
  }
}

function renderRobotOnMinimap(scene, isOnCamera) {
  if (isOnCamera) {
    scene.game.minimap.robotDot.setVisible(true);
    scene.game.minimap.robotDot.x = scene.game.minimap.x + scene.game.robot.x * scene.game.minimap.scale;
    scene.game.minimap.robotDot.y = scene.game.minimap.y + scene.game.robot.y * scene.game.minimap.scale;
  } else {
    scene.game.minimap.robotDot.setVisible(false);
  }
}

function createRobotGoalRect(scene, robotGoalRect) {
  destroyRobotGoalRect(scene);
  scene.game.minimap.robotGoal = scene.add.graphics({ x: 0, y: 0 });
  scene.game.minimap.robotGoal.lineStyle(4, robotColor, 0.85);
  scene.game.minimap.robotGoal.setScrollFactor(0.0, 0.0);
  scene.game.minimap.robotGoal.setDepth(15);
  scene.game.minimap.robotGoal.strokeRect(
    scene.game.minimap.x+robotGoalRect.x*scene.game.minimap.scale,
    scene.game.minimap.y+robotGoalRect.y*scene.game.minimap.scale,
    robotGoalRect.width*scene.game.minimap.scale,
    robotGoalRect.height*scene.game.minimap.scale,
  );
}

function destroyRobotGoalRect(scene) {
  if (scene.game.minimap.robotGoal != null) {
    scene.game.minimap.robotGoal.destroy();
  }
}

function setMinimapAlpha(scene, alpha) {
  scene.game.minimap.setAlpha(alpha);
  scene.game.minimap.cameraBox.setAlpha(alpha);
  scene.game.minimap.playerDot.setAlpha(alpha);
  scene.game.minimap.playerGoal.setAlpha(alpha);
  scene.game.minimap.robotDot.setAlpha(alpha);
  if (scene.game.minimap.robotGoal != null) {
    scene.game.minimap.robotGoal.setAlpha(alpha);
  }
}
