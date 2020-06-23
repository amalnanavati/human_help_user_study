// Create the red outline around the screen when you run out of time
function createNegativeScoreOutline(scene) {
  scene.game.negativeScoreRedOutline = scene.add.graphics({ x: 0, y: 0 });
  scene.game.negativeScoreRedOutline.lineStyle(tileSize, 0xff0000, 0.75);
  scene.game.negativeScoreRedOutline.strokeRect(0, 0, scene.game.config.width, scene.game.config.height);
  scene.game.negativeScoreRedOutline.setScrollFactor(0.0, 0.0);
  scene.game.negativeScoreRedOutline.setVisible(false);
}

// Returns true if the two objects overlap
function objectsOverlaps(obj0, obj1) {
  var w0 = obj0.width*obj0.scale;
  var h0 = obj0.height*obj0.scale;
  var x0 = obj0.x-obj0.originX*w0+(1-obj0.scrollFactorX)*game.camera.scrollX;
  var y0 = obj0.y-obj0.originY*h0+(1-obj0.scrollFactorY)*game.camera.scrollY;
  var w1 = obj1.width*obj1.scale;
  var h1 = obj1.height*obj1.scale;
  var x1 = obj1.x-obj1.originX*w1+(1-obj1.scrollFactorX)*game.camera.scrollX;
  var y1 = obj1.y-obj1.originY*h1+(1-obj1.scrollFactorY)*game.camera.scrollY;

  var topLeft0 = (
    x1 <= x0 && x0 <= x1 + w1 &&
    y1 <= y0 && y0 <= y1 + h1
  );
  var topRight0 = (
    x1 <= x0 + w0 && x0 + w0 <= x1 + w1 &&
    y1 <= y0 && y0 <= y1 + h1
  );
  var bottomLeft0 = (
    x1 <= x0 && x0 <= x1 + w1 &&
    y1 <= y0 + h0 && y0 + h0 <= y1 + h1
  );
  var bottomRight0 = (
    x1 <= x0 + w0 && x0 + w0 <= x1 + w1 &&
    y1 <= y0 + h0 && y0 + h0 <= y1 + h1
  );

  var topLeft1 = (
    x0 <= x1 && x1 <= x0 + w0 &&
    y0 <= y1 && y1 <= y0 + h0
  );
  var topRight1 = (
    x0 <= x1 + w1 && x1 + w1 <= x0 + w0 &&
    y0 <= y1 && y1 <= y0 + h0
  );
  var bottomLeft1 = (
    x0 <= x1 && x1 <= x0 + w0 &&
    y0 <= y1 + h1 && y1 + h1 <= y0 + h0
  );
  var bottomRight1 = (
    x0 <= x1 + w1 && x1 + w1 <= x0 + w0 &&
    y0 <= y1 + h1 && y1 + h1 <= y0 + h0
  );
  return topLeft0 || topRight0 || bottomLeft0 || bottomRight0 || topLeft1 || topRight1 || bottomLeft1 || bottomRight1;
}

function post_form(path, params, method='post') {

  // The rest of this code assumes you are not using a library.
  // It can be made less wordy if you use one.
  const form = document.createElement('form');
  form.method = method;
  form.action = path;

  for (const key in params) {
    if (params.hasOwnProperty(key)) {
      const hiddenField = document.createElement('input');
      hiddenField.type = 'hidden';
      hiddenField.name = key;
      hiddenField.value = params[key];

      form.appendChild(hiddenField);
    }
  }

  document.body.appendChild(form);
  form.submit();
}
