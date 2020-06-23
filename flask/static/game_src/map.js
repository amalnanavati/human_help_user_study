// tileSize is defined in game.html
function tileToGameXY(tile) {
  return {x : (tile.x + 0.5) * tileSize, y : (tile.y + 0.5) * tileSize};
}

// tileSize is defined in game.html
function gameToTileXY(gameXY) {
  return {x : Math.floor(gameXY.x / tileSize), y : Math.floor(gameXY.y / tileSize)};
}

function createMap(scene) {
  // Create the map and its layers
  scene.game.map = scene.make.tilemap({ key: "map" });
  scene.game.tileset = scene.game.map.addTilesetImage("tiles2", "tiles");
  scene.game.belowLayer = scene.game.map.createStaticLayer("Below Player", scene.game.tileset, 0, 0);
  scene.game.worldLayer = scene.game.map.createStaticLayer("World", scene.game.tileset, 0, 0);
  // scene.game.worldLayer.setCollisionByProperty({ collides: true });
  // scene.game.aboveLayer = scene.game.map.createStaticLayer("Above Player", scene.game.tileset, 0, 0);
  // scene.game.aboveLayer.setDepth(10);
  // TODO (amal): preprocess this and save it in an assets json file
  scene.game.roomLabels = {};
  scene.game.xyToSemanticLabels = {};
  scene.game.semanticLabelToRoomRectBounds = {};
  for (var i = 0; i < scene.game.map.objects.length; i++) {
    if (scene.game.map.objects[i].name == "Objects") {
      for (var j = 0; j < scene.game.map.objects[i].objects.length; j++) {
        if (scene.game.map.objects[i].objects[j].point) {
          var point = scene.game.map.objects[i].objects[j];
          var wasLabel = false;

          if (scene.game.map.objects[i].objects[j].properties && scene.game.map.objects[i].objects[j].properties.length > 0) {
            for (var k = 0; k < scene.game.map.objects[i].objects[j].properties.length; k++) {
              var property = scene.game.map.objects[i].objects[j].properties[k];
              if (property.name == "label" && property.value) {
                scene.game.roomLabels[point.name] = scene.add.text(
                  Math.floor(point.x/tileSize)*tileSize + tileSize/2,
                  Math.floor(point.y/tileSize)*tileSize + tileSize/2,
                  point.name,
                  {
                    font: "32px monospace",
                    fill: "#ececec",
                    padding: { x: 0, y: 0 },
                    align: "center",
                  },
              ).setOrigin(0.5, 0.5);
              wasLabel = true;
              break;
              }
            }
          }

          if (!wasLabel) {
            var tileX = Math.floor(point.x/tileSize);
            var tileY = Math.floor(point.y/tileSize);
            var key = String([tileX, tileY]);
            if (!(key in scene.game.xyToSemanticLabels)) {
              scene.game.xyToSemanticLabels[String([tileX, tileY])] = new Set();
            }
            scene.game.xyToSemanticLabels[String([tileX, tileY])].add(point.name);
          }
        } else { // If its not a point, it is a rectangle
          var rect = scene.game.map.objects[i].objects[j];
          for (tileX = Math.ceil(rect.x/tileSize); tileX < Math.floor((rect.x+rect.width)/tileSize); tileX++) {
            for (tileY = Math.ceil(rect.y/tileSize); tileY < Math.floor((rect.y+rect.height)/tileSize); tileY++) {
              var key = String([tileX, tileY]);
              if (!(key in scene.game.xyToSemanticLabels)) {
                scene.game.xyToSemanticLabels[key] = new Set();
              }
              scene.game.xyToSemanticLabels[key].add(rect.name);
            }
          }
          scene.game.semanticLabelToRoomRectBounds[rect.name] = {
            x : rect.x,
            y : rect.y,
            width : rect.width,
            height : rect.height,
          };
        }
      }
      break;
    }
  }
  scene.game.semanticLabelsToXY = {};
  for (xyStr in scene.game.xyToSemanticLabels) {
    var semanticLabels = scene.game.xyToSemanticLabels[xyStr];
    var nums = xyStr.split(",");
    var x = parseFloat(nums[0]);
    var y = parseFloat(nums[1]);
    semanticLabels.forEach(function (semanticLabel) {
      if (!(semanticLabel in scene.game.semanticLabelsToXY)) {
        scene.game.semanticLabelsToXY[semanticLabel] = [];
      }
      scene.game.semanticLabelsToXY[semanticLabel].push({x : x, y : y});
    });
  }
  console.log("semantic label maps", scene.game.xyToSemanticLabels, scene.game.semanticLabelsToXY);
}
