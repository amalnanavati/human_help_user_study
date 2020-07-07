class TimeProgressBar {
  constructor(scene, x, y, width, height, warningCallback) {
    this.scene = scene;
    this.x = x;
    this.y = y;
    this.width = width;
    this.height = height;
    this.createTimeProgressBar();
    this.warningCallback = warningCallback;
    this.progress = null;
    this.timeLastDestroyedAtProgress = null;
  }

  setText(text) {
    this.text.text = text;
  }

  setX(x) {
    this.x = x;

    this.timeProgressBar.x = x;
    this.timeProgressBarStroke.x = x;
    this.text.x = x;
    this.remainingTimeText.x = x;
    if (this.coloredBar != null) {
      this.coloredBar.x = x;
    }
  }

  setWidth(width) {
    this.width = width;

    var scaleX = width / this.originalWidth;

    this.timeProgressBar.scaleX = scaleX;
    this.timeProgressBarStroke.scaleX = scaleX;
    if (this.coloredBar != null) {
      this.coloredBar.scaleX = scaleX;
    }

  }

  destroyTimer() {
    // console.log("destroyTimer", this.coloredBarTimer);
    if (this.coloredBarTimer != null) {
      this.coloredBarTimer.destroy();
      this.coloredBarTimer = null;

      this.isColoredBarVisible = true;
      this.coloredBar.setVisible(this.isColoredBarVisible);
      this.warningCallback(this.scene, false);
    }
    if (this.timeLastDestroyedAtProgress == null) {
      this.timeLastDestroyedAtProgress = this.progress;
    }
  }

  isTimerActive() {
    return this.coloredBarTimer != null;
  }

  drawBar(progress, delay) {
    this.progress = progress;

    if (this.coloredBar != null) {
      this.coloredBar.destroy();
    }
    if (this.timeLastDestroyedAtProgress != null && progress < this.timeLastDestroyedAtProgress) {
      this.destroyTimer();
      this.timeLastDestroyedAtProgress = null;
    }

    this.coloredBar = this.scene.add.graphics({ x : this.x, y : this.y});
    this.coloredBar.setVisible(this.isColoredBarVisible);

    if (progress <= 0.5) {
      this.coloredBar.fillStyle(0x008000, 1);
    } else if (progress <= 0.80) {
      this.coloredBar.fillStyle(0xff7518, 1);
    } else {
      this.coloredBar.fillStyle(0xff0000, 1);
      if (progress > 0.80 && this.timeLastDestroyedAtProgress == null) {
        // the colored bar should flash in and out
        if (this.coloredBarTimer == null) {
          this.isColoredBarVisible = true;
          var self = this;
          this.coloredBarTimer = this.scene.time.addEvent({
            delay: 500, // 0.5 sec
            loop: true,
            callback: function() {
              self.isColoredBarVisible = !self.isColoredBarVisible;
              self.coloredBar.setVisible(self.isColoredBarVisible);
              self.warningCallback(self.scene, self.isColoredBarVisible);
              // console.log("callback", self.isColoredBarVisible);
              // self.text.setVisible(self.isColoredBarVisible);
              // self.remainingTimeText.setVisible(self.isColoredBarVisible);
            },
          });
        }
      }
    }

    var remainingSecs = Math.round((delay - progress*delay)/1000);
    this.remainingTimeText.text = remainingSecs.toString();

    // if (progress != 1.0) {
    var roundedRectVal = this.getRoundedRectVal();
    var width = 2*roundedRectVal+(this.width-2*roundedRectVal)*(progress);
    this.coloredBar.fillRoundedRect(0, 0, width, (this.height), roundedRectVal);

    if (width >= this.remainingTimeText.width+this.text.width) {
      this.remainingTimeText.setOrigin(1.0, 0.5);
      this.remainingTimeText.x = this.coloredBar.x + width;
    } else {
      this.remainingTimeText.setOrigin(0.0, 0.5);
      this.remainingTimeText.x = this.text.x + this.text.width;
    }
    // }
    this.coloredBar.setScrollFactor(0.0, 0.0).setDepth(7);

  }

  removeBar() {
    if (this.coloredBar != null) {
      this.coloredBar.destroy();
    }
    this.destroyTimer();
    this.timeLastDestroyedAtProgress = null;
    this.remainingTimeText.text = "";
  }

  setAlpha(alpha) {
    if (this.timeProgressBar != null) {
      this.timeProgressBar.setAlpha(alpha);
    }
    if (this.timeProgressBarStroke != null) {
      this.timeProgressBarStroke.setAlpha(alpha);
    }
    if (this.coloredBar != null) {
      this.coloredBar.setAlpha(alpha);
    }
    if (this.text != null) {
      this.text.setAlpha(alpha);
    }
    if (this.remainingTimeText != null) {
      this.remainingTimeText.setAlpha(alpha);
    }
  }

  getOffset() {
    return this.width/200;
  }

  getRoundedRectVal() {
    return 0;//this.height/2;
  }

  createTimeProgressBar() {
    this.originalWidth = this.width;

    var roundedRectVal = this.getRoundedRectVal();

    this.timeProgressBar = this.scene.add.graphics({ x : this.x, y : this.y});
    this.timeProgressBar.setDepth(7);
    this.timeProgressBar.fillStyle(0x000000, 1);
    this.timeProgressBar.fillRoundedRect(0, 0, this.width, this.height, roundedRectVal);
    this.timeProgressBar.setScrollFactor(0.0, 0.0);

    this.timeProgressBarStroke = this.scene.add.graphics({ x : this.x, y : this.y});
    this.timeProgressBarStroke.setDepth(9);
    this.timeProgressBarStroke.lineStyle(2, 0xffffff, 1);
    this.timeProgressBarStroke.strokeRoundedRect(0, 0, this.width, this.height, roundedRectVal);
    this.timeProgressBarStroke.setScrollFactor(0.0, 0.0);

    var offset = this.getOffset();

    this.isColoredBarVisible = true;

    var fontSize = 26;

    this.text = this.scene.add.text(
      this.x+offset,
      this.y+this.height/2,
      "Time: ",
      {
        font: fontSize.toString()+"px monospace",
        fill: '#ffffff',
        padding: {x : 5, y : 0},
      },
    ).setOrigin(0.0, 0.5).setScrollFactor(0.0, 0.0).setDepth(8);

    this.remainingTimeText = this.scene.add.text(
      offset,
      this.y+this.height/2,
      "",
      {
        font: fontSize.toString()+"px monospace",
        fill: '#ffffff',
      },
    ).setOrigin(1.0, 0.5).setScrollFactor(0.0, 0.0).setDepth(8);
  }
}
