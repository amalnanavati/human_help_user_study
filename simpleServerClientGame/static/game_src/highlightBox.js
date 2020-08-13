function createHighlightBox(scene) {
  scene.game.highlightBoxSq = scene.add.graphics({ x: 0, y: 0 });
  scene.game.highlightBoxSq.lineStyle(4, playerColor, 0.5);
  scene.game.highlightBoxSq.strokeRect(0, 0, tileSize, tileSize);
  scene.game.highlightBoxSq.setVisible(false);

  scene.game.highlightBoxHoriz = scene.add.graphics({ x: 0, y: 0 });
  scene.game.highlightBoxHoriz.lineStyle(4, playerColor, 0.5);
  scene.game.highlightBoxHoriz.strokeRect(0, 0, 2*tileSize, tileSize);
  scene.game.highlightBoxHoriz.setVisible(false);

  scene.game.highlightBoxVert = scene.add.graphics({ x: 0, y: 0 });
  scene.game.highlightBoxVert.lineStyle(4, playerColor, 0.5);
  scene.game.highlightBoxVert.strokeRect(0, 0, tileSize, 2*tileSize);
  scene.game.highlightBoxVert.setVisible(false);
}

function updateHighlightBox(scene, hasNextGoal, targetTile, adjacentTile) {
  if (hasNextGoal) {
    if (targetTile.x == adjacentTile.x) {
      if (targetTile.y == adjacentTile.y) { // tiles are the same
        scene.game.highlightBoxSq.setVisible(true);
        scene.game.highlightBoxSq.x = targetTile.x*tileSize;
        scene.game.highlightBoxSq.y = targetTile.y*tileSize;
        scene.game.highlightBoxHoriz.setVisible(false);
        scene.game.highlightBoxVert.setVisible(false);
      } else { // tiles are vertically related
        scene.game.highlightBoxVert.setVisible(true);
        scene.game.highlightBoxVert.x = targetTile.x*tileSize;
        scene.game.highlightBoxVert.y = Math.min(targetTile.y, adjacentTile.y)*tileSize;
        scene.game.highlightBoxSq.setVisible(false);
        scene.game.highlightBoxHoriz.setVisible(false);
      }
    } else { // tiles are horizontally related
      scene.game.highlightBoxHoriz.setVisible(true);
      scene.game.highlightBoxHoriz.x = Math.min(targetTile.x, adjacentTile.x)*tileSize;
      scene.game.highlightBoxHoriz.y = targetTile.y*tileSize;
      scene.game.highlightBoxSq.setVisible(false);
      scene.game.highlightBoxVert.setVisible(false);
    }
  } else {
    scene.game.highlightBoxSq.setVisible(false);
    scene.game.highlightBoxHoriz.setVisible(false);
    scene.game.highlightBoxVert.setVisible(false);
  }
}
