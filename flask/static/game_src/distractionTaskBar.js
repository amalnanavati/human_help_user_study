function createDistractionTaskBar(scene) {
  var w = scene.game.config.width*4/5;
  var h = scene.game.config.height/7;
  var x = -w/2;
  var y = -h/2;
  scene.game.distractionTaskBar = scene.add.graphics({ x: scene.game.config.width/2, y: scene.game.config.height/2 });
  scene.game.distractionTaskBar.width = w;
  scene.game.distractionTaskBar.height = h;
  scene.game.distractionTaskBar.fillStyle(0xececec, 0.9);
  scene.game.distractionTaskBar.lineStyle(4, 0x000000, 0.9);
  scene.game.distractionTaskBar.strokeRoundedRect(x, y, w, h, 16);
  scene.game.distractionTaskBar.fillRoundedRect(x, y, w, h, 16);
  scene.game.distractionTaskBar.setDepth(13);
  scene.game.distractionTaskText = scene.add.text(scene.game.distractionTaskBar.x, w/40, "", {
    font: "18px monospace",
    fill: "rgba(0, 0, 0, 0.9)",
  }).setOrigin(0.5, 0.5);
  scene.game.distractionTaskText.y = scene.game.distractionTaskBar.y-scene.game.distractionTaskBar.height/2 + scene.game.distractionTaskBar.width/40 +scene.game.distractionTaskText.height/2;
  scene.game.distractionTaskText.setDepth(20);//13);//
}

function setDistractionTaskBarVisible(scene, visible) {
  scene.game.distractionTaskBar.setVisible(visible);
  scene.game.distractionTaskText.setVisible(visible);
  if (visible) {
    scene.game.distractionTaskBar.x = scene.game.config.width/2+scene.game.camera.scrollX;
    scene.game.distractionTaskBar.y = scene.game.config.height/2+scene.game.camera.scrollY;
    scene.game.distractionTaskText.x = scene.game.config.width/2+scene.game.camera.scrollX;
    scene.game.distractionTaskText.y = scene.game.distractionTaskBar.y-scene.game.distractionTaskBar.height/2 + scene.game.distractionTaskBar.width/40 +scene.game.distractionTaskText.height/2;
  } else if (scene.game.distractionTaskBar.progressBar != null) {
    scene.game.distractionTaskBar.progressBar.destroy();
    scene.game.distractionTaskBar.progressBar = null;
  }
}

function drawDistractionTaskBarProgress(scene) {
  if (scene.game.distractionTaskBar.progressBar != null) {
    scene.game.distractionTaskBar.progressBar.destroy();
  }
  var w = scene.game.distractionTaskBar.width*38/40;
  var h = scene.game.distractionTaskBar.height/3;
  var x = scene.game.distractionTaskText.x-w/2;
  var y = ((scene.game.distractionTaskText.y + scene.game.distractionTaskText.height/2)*2/3 + (scene.game.distractionTaskBar.y + scene.game.distractionTaskBar.height/2)*1/3);
  scene.game.distractionTaskBar.progressBar = scene.add.graphics({ x: x, y: y });
  scene.game.distractionTaskBar.progressBar.fillStyle(0x898989, 0.9);
  // scene.game.distractionTaskBar.progressBar.fillRoundedRect(0, 0, w*scene.game.distractionTaskTimer.getOverallProgress(), h, 4);
  scene.game.distractionTaskBar.progressBar.fillRoundedRect(0, 0, w*scene.game.distractionTaskTimerSecs/timeForDistractionTask, h, 4);
  scene.game.distractionTaskBar.progressBar.setDepth(13);
}
