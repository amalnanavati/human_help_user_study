class SpeechBubble {
  constructor(scene, width, x, y, text, buttonsData, hasArrow) {
    // x, y is at the bottom of the arrow
    // buttonsData is a list of objects with "text" and "callbackFunction" attributes.
    this._scene = scene;
    this._width = width;
    this._x = x;
    this._y = y;
    this._text = text;
    this._buttonsData = buttonsData;
    this._visibility = true;
    if (hasArrow == null) {
      this._hasArrow = true;
    } else {
      this._hasArrow = false;
    }
    this.createSpeechBubble();
  }
  getVisible() {
    return this._bubble.visible;
  }
  getBubbleHeight() {
    var padding = this.getBubblePadding();
    return padding + this._speech.getBounds().height + padding + (this.maxRowI != null ? (this._buttons[0].height + padding) * (this.maxRowI + 1) : 0);
  }
  getArrowHeight(bubbleHeight) {
    return bubbleHeight / 4;
  }
  getHeight() {
    var bubbleHeight = this.getBubbleHeight();
    return bubbleHeight + this.getArrowHeight(bubbleHeight);
  }
  getArrowXOffset() {
    return this._width / 7;
  }
  getArrowWidth(bubbleHeight) {
    return this._width / 7;
  }
  getBubblePadding() {
    return this._width/20;
  }
  getSpeechWidth() {
    return this._width - (this.getBubblePadding() * 2);
  }
  setScrollFactor(x, y) {
    this._bubble.setScrollFactor(x, y);
    this._speech.setScrollFactor(x, y);
    for (var button of this._buttons) {
      button.setScrollFactor(x, y);
    }
  }
  setVisible(visible) {
    this._bubble.visible = visible;
    this._speech.visible = visible;
    for (var button of this._buttons) {
      button.visible = visible;
      if (visible) {
        button.setInteractive();
      } else {
        button.removeInteractive();
      }
    }
  }
  setWidth(width) {
    this._width = width;
    // Scale the bubble horizontally
    this._bubble.scaleX = width / this._originalWidth;

    // Set the speech width
    this._speech.setWordWrapWidth(this.getSpeechWidth());

    // Because the speech width changed, the speech height could have also changed
    var newHeight = this.getHeight();
    this._bubble.scaleY = newHeight / this._originalHeight;
    this._bubble.y = this._y - newHeight;

    // The x position will likely have to change to keep the arrow point stationary
    this._bubble.x = this._x - this.getArrowXOffset();

    // The speech position will have to change to remain centered
    var bubblePadding = this.getBubblePadding();
    var b = this._speech.getBounds();
    this._speech.x = this._bubble.x + (this._width / 2) - (b.width / 2); // the horizontal centering has changed
    this._speech.y = this._bubble.y + bubblePadding;

    // The button position has also changed
    // var xOffset = 0;
    // for (var i = 0; i < this._buttons.length; i++) {
    //   var button = this._buttons[i];
    //   button.x = this._speech.x + this._speech.width/2 - this.totalButtonWidth / 2 + xOffset;
    //   button.y = this._speech.y + this._speech.height + bubblePadding;
    //   xOffset = xOffset + button.width + bubblePadding;
    // }
    this.placeButtons();
  }
  setText(text) {
    this._text = text;
    this._speech.text = text;
    // Adjust the height for the new text
    var newHeight = this.getHeight();
    this._bubble.scaleY = newHeight / this._originalHeight;
    this._bubble.y = this._y - newHeight;
    var b = this._speech.getBounds();
    var bubblePadding = this.getBubblePadding();
    this._speech.x = this._bubble.x + (this._width / 2) - (b.width / 2); // the horizontal centering has changed
    this._speech.y = this._bubble.y + bubblePadding;

    // The button position has also changed
    // var xOffset = 0;
    // for (var i = 0; i < this._buttons.length; i++) {
    //   var button = this._buttons[i];
    //   button.x = this._speech.x + this._speech.width/2 - this.totalButtonWidth / 2 + xOffset;
    //   button.y = this._speech.y + this._speech.height + bubblePadding;
    //   xOffset = xOffset + button.width + bubblePadding;
    // }
    this.placeButtons();
  }
  setPosition(x, y) {
    // console.log("setPosition", x, y);
    // x, y is at the bottom of the arrow
    var bubblePadding = this.getBubblePadding();
    this._x = x;
    this._y = y;
    var b = this._speech.getBounds();
    if (this._hasArrow) {
      this._bubble.x = x - this.getArrowXOffset();
      this._bubble.y = y - this.getHeight();
    } else {
      this._bubble.x = x;
      this._bubble.y = y
    }
    this._speech.setPosition(this._bubble.x + (this._width / 2) - (b.width / 2), this._bubble.y + bubblePadding);
    // var xOffset = 0;
    // for (var i = 0; i < this._buttons.length; i++) {
    //   var button = this._buttons[i];
    //   button.x = this._speech.x + this._speech.width/2 - this.totalButtonWidth / 2 + xOffset;
    //   button.y = this._speech.y + this._speech.height + bubblePadding;
    //   xOffset = xOffset + button.width + bubblePadding;
    // }
    this.placeButtons();
  }
  placeButtons() {
    var bubblePadding = this.getBubblePadding();

    var xOffset = [];
    for (var i = 0; i < this._buttons.length; i++) {
      var rowI = this._buttonsData[i].rowI != null ? this._buttonsData[i].rowI : 0;
      while (rowI >= xOffset.length) {
        xOffset.push(0.0);
      }
      var button = this._buttons[i];
      button.x = this._speech.x + this._speech.width/2 - this.totalButtonWidth[rowI]/2 + xOffset[rowI];
      button.y = this._speech.y + this._speech.height + bubblePadding*(rowI+1) + button.height*rowI;
      // console.log("_speech", this._speech.x, this._speech.y, this._speech.width, this._speech.height);
      // console.log("button", button.x, button.y, rowI, this.totalButtonWidth[rowI], xOffset[rowI]);
      xOffset[rowI] = xOffset[rowI] + button.width + bubblePadding;
    }
  }
  createButtons() {
    var bubblePadding = this.getBubblePadding();

    // Create the button(s)
    this.maxRowI = null;
    this._buttons = [];
    this.totalButtonWidth = [];
    this.buttonsPerRow = [];
    for (var buttonData of this._buttonsData) {
      var rowI = buttonData.rowI != null ? buttonData.rowI : 0;
      if (this.maxRowI == null || rowI > this.maxRowI) {
        this.maxRowI = rowI;
      }
      while (rowI >= this.totalButtonWidth.length) {
        this.totalButtonWidth.push(0.0);
        this.buttonsPerRow.push(0);
      }
      var button = this._scene.add.text(
        0,
        0,
        buttonData.text,
        {
          font: '20px monospace',
          fill: '#000000',
          align: 'center',
          backgroundColor: 'rgba(255,0,0,0.5)',
        },
      );
      this.totalButtonWidth[rowI] = this.totalButtonWidth[rowI] + button.width;
      this.buttonsPerRow[rowI] += 1;
      button.setInteractive();
      button.on('pointerdown', buttonData.callbackFunction, button);
      button.setDepth(12);
      this._buttons.push(button);
    }
    if (this.maxRowI != null) {
      for (var rowI = 0; rowI <= this.maxRowI; rowI++) {
        this.totalButtonWidth[rowI] = this.totalButtonWidth[rowI] + bubblePadding*(this.buttonsPerRow[rowI] - 1);
      }
    }
  }
  setButtons(buttonsData) {
    var oldButtonsData = this._buttonsData;
    this._buttonsData = buttonsData;

    var bubblePadding = this.getBubblePadding();

    for (var button of this._buttons) {
      button.destroy();
    }

    var oldMaxRowI = this.maxRowI;
    this.createButtons();

    this.placeButtons();

    console.log("setButtons", this.maxRowI, oldMaxRowI);

    if (((oldButtonsData.length > 0) ^ (buttonsData.length > 0)) || this.maxRowI != oldMaxRowI) {
      // Adjust the height for the new text
      var newHeight = this.getHeight();
      this._bubble.scaleY = newHeight / this._originalHeight;
      this._bubble.y = this._y - newHeight;
      var b = this._speech.getBounds();
      var bubblePadding = this.getBubblePadding();
      this._speech.x = this._bubble.x + (this._width / 2) - (b.width / 2); // the horizontal centering has changed
      this._speech.y = this._bubble.y + bubblePadding;
    }
  }
  createSpeechBubble ()
  {
      // Create the bubble speech
      var bubblePadding = this.getBubblePadding();
      this._speech = this._scene.add.text(
        0,
        0,
        this._text,
        {
          font: '20px monospace',
          fill: '#000000',
          align: 'center',
          wordWrap: {
            width: this.getSpeechWidth(),
          },
        },
      );
      this._speech.setDepth(11);

      // Create the button(s)
      this.createButtons();

      var b = this._speech.getBounds();

      var bubbleWidth = this._width;//b.width * 12 / 10;//
      var bubbleHeight = this.getBubbleHeight();//this._height;
      var arrowHeight = this.getArrowHeight(bubbleHeight);

      this._originalWidth = bubbleWidth;
      this._originalHeight = bubbleHeight + arrowHeight;

      this._bubble = this._scene.add.graphics({ x: this._x, y: this._y - bubbleHeight - (this._hasArrow ? arrowHeight : 0) });
      this._bubble.setDepth(10);

      this._speech.setPosition(this._bubble.x + (bubbleWidth / 2) - (b.width / 2), this._bubble.y + bubblePadding);

      this.placeButtons();

      // //  Bubble shadow
      // this._bubble.fillStyle(0x222222, 0.5);
      // this._bubble.fillRoundedRect(6, 6, bubbleWidth, bubbleHeight, 16);

      //  Bubble color
      this._bubble.fillStyle(0xffffff, 1);

      //  Bubble outline line style
      this._bubble.lineStyle(4, 0x565656, 1);

      //  Bubble shape and outline
      this._bubble.strokeRoundedRect(0, 0, bubbleWidth, bubbleHeight, 16);
      this._bubble.fillRoundedRect(0, 0, bubbleWidth, bubbleHeight, 16);

      //  Calculate arrow coordinates
      if (this._hasArrow) {
        var point1X = this.getArrowXOffset();
        var point1Y = bubbleHeight;
        var point2X = point1X + this.getArrowWidth();
        var point2Y = bubbleHeight;
        var point3X = point1X;
        var point3Y = bubbleHeight + arrowHeight;

        // //  Bubble arrow shadow
        // this._bubble.lineStyle(4, 0x222222, 0.5);
        // this._bubble.lineBetween(point2X - 1, point2Y + 6, point3X + 2, point3Y);

        //  Bubble arrow fill
        this._bubble.fillTriangle(point1X, point1Y, point2X, point2Y, point3X, point3Y);
        this._bubble.lineStyle(2, 0x565656, 1);
        this._bubble.lineBetween(point2X, point2Y, point3X, point3Y);
        this._bubble.lineBetween(point1X, point1Y, point3X, point3Y);
      }
    }
}
