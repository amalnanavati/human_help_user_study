function updatePlayerPath(scene) {
  if (scene.game.player.path != null) {
    scene.game.player.path.destroy();
    scene.game.player.path = null;
  }

  scene.game.player.path = scene.add.graphics({ x: 0, y: 0 });
  scene.game.player.path.lineStyle(8, playerColor, 0.5);
  if (scene.game.player.taskPlan != null && scene.game.player.taskPlan.length > 0) {
    var points = [];
    for (var taskPlanPoint of scene.game.player.taskPlan) {
      var x = (taskPlanPoint.x+0.55)*tileSize;
      var y = (taskPlanPoint.y+0.55)*tileSize;
      points.push(new Phaser.Geom.Point(x, y));
    }
    scene.game.player.path.strokePoints(points);
  }
}
