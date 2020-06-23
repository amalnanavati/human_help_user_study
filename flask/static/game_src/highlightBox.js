function createHighlightBox(scene) {
  scene.game.highlightBox = scene.add.graphics({ x: 0, y: 0 });
  scene.game.highlightBox.lineStyle(4, playerColor, 0.5);
  scene.game.highlightBox.strokeRect(0, 0, tileSize, tileSize);
}

function updateHighlightBox(scene, hasNextGoal, targetTile) {
  if (hasNextGoal) {
    scene.game.highlightBox.setVisible(true);
    scene.game.highlightBox.x = targetTile.x*tileSize;
    scene.game.highlightBox.y = targetTile.y*tileSize;
  } else {
    scene.game.highlightBox.setVisible(false);
  }
}
