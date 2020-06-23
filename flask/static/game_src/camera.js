const cameraPadding = 1; // the robot must spawn more than these units away from the camera bounds

function createCamera(scene) {
  scene.game.camera = scene.cameras.main;
  scene.game.camera.startFollow(scene.game.player);
  scene.game.camera.setBounds(0, 0, scene.game.map.widthInPixels, scene.game.map.heightInPixels);
}

function getCameraBounds(scene) {
  var cameraCenterTileI = {
      x : Math.floor(scene.game.camera.scrollX / tileSize),
      y : Math.floor(scene.game.camera.scrollY / tileSize),
  }
  var cameraLeft = cameraCenterTileI.x; // inclusive
  var cameraRight = cameraCenterTileI.x + scene.game.camera.width / tileSize; // exclusive
  var cameraUp = cameraCenterTileI.y; // inclusive
  var cameraDown = cameraCenterTileI.y + scene.game.camera.height / tileSize; // exclusive

  return {
    left: cameraLeft,
    right: cameraRight,
    up: cameraUp,
    down: cameraDown,
  }
}

function isOffCamera(scene, tile, padding) {
  if (padding == null) {
    padding = cameraPadding;
  }
  var cameraBounds = getCameraBounds(scene);
  return (tile.x < cameraBounds.left - padding ||
          tile.x >= cameraBounds.right + padding ||
          tile.y < cameraBounds.up - padding ||
          tile.y >= cameraBounds.down + padding);
}
