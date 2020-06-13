class SpeechBubble {
  constructor(scene, width, x, y, text, buttonsData) {
    // x, y is at the bottom of the arrow
    // buttonsData is a list of objects with "text" and "callbackFunction" attributes.
    this._scene = scene;
    this._width = width;
    this._x = y;
    this._y = y;
    this._text = text;
    this._buttonsData = buttonsData;
    this.createSpeechBubble();
    this._visibility = true;
  }
  getVisibile() {
    return this._bubble.visible;
  }
  getBubbleHeight() {
    var padding = this.getBubblePadding();
    return padding + this._speech.getBounds().height + padding + (this._buttons.length > 0 ? this._buttons[0].height + padding : 0);
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
    var xOffset = 0;
    for (i = 0; i < this._buttons.length; i++) {
      var button = this._buttons[i];
      button.x = this._speech.x + this._speech.width/2 - this.totalButtonWidth / 2 + xOffset;
      button.y = this._speech.y + this._speech.height + bubblePadding;
      xOffset = xOffset + button.width + bubblePadding;
    }
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
    var xOffset = 0;
    for (i = 0; i < this._buttons.length; i++) {
      var button = this._buttons[i];
      button.x = this._speech.x + this._speech.width/2 - this.totalButtonWidth / 2 + xOffset;
      button.y = this._speech.y + this._speech.height + bubblePadding;
      xOffset = xOffset + button.width + bubblePadding;
    }
  }
  setPosition(x, y) {
    // x, y is at the bottom of the arrow
    var bubblePadding = this.getBubblePadding();
    this._x = x;
    this._y = y;
    var b = this._speech.getBounds();
    this._bubble.x = x - this.getArrowXOffset();
    this._bubble.y = y - this.getHeight();
    this._speech.setPosition(this._bubble.x + (this._width / 2) - (b.width / 2), this._bubble.y + bubblePadding);
    var xOffset = 0;
    for (i = 0; i < this._buttons.length; i++) {
      var button = this._buttons[i];
      button.x = this._speech.x + this._speech.width/2 - this.totalButtonWidth / 2 + xOffset;
      button.y = this._speech.y + this._speech.height + bubblePadding;
      xOffset = xOffset + button.width + bubblePadding;
    }
  }
  setButtons(buttonsData) {
    var oldButtonsData = this._buttonsData;
    this._buttonsData = buttonsData;

    var bubblePadding = this.getBubblePadding();

    for (button of this._buttons) {
      button.destroy();
    }

    // Create the button(s)
    this._buttons = [];
    this.totalButtonWidth = 0.0;
    for (var buttonData of this._buttonsData) {
      var button = this._scene.add.text(0, 0, buttonData.text, { fontFamily: 'Arial', fontSize: 20, color: '#000000', align: 'center', backgroundColor: 'rgba(255,0,0,0.5)'});
      this.totalButtonWidth = this.totalButtonWidth + button.width;
      button.setInteractive();
      button.on('pointerdown', buttonData.callbackFunction);
      button.setDepth(12);
      this._buttons.push(button);
    }
    this.totalButtonWidth = this.totalButtonWidth + bubblePadding*(this._buttons.length - 1);

    var xOffset = 0;
    for (i = 0; i < this._buttons.length; i++) {
      var button = this._buttons[i];
      button.x = this._speech.x + this._speech.width/2 - this.totalButtonWidth / 2 + xOffset;
      button.y = this._speech.y + this._speech.height + bubblePadding;
      xOffset = xOffset + button.width + bubblePadding;
    }

    if ((oldButtonsData.length > 0) ^ (buttonsData.length > 0)) {
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
      this._speech = this._scene.add.text(0, 0, this._text, { fontFamily: 'Arial', fontSize: 20, color: '#000000', align: 'center', wordWrap: { width: this.getSpeechWidth() } });
      this._speech.setDepth(11);

      // Create the button(s)
      this._buttons = [];
      this.totalButtonWidth = 0.0;
      for (var buttonData of this._buttonsData) {
        var button = this._scene.add.text(0, 0, buttonData.text, { fontFamily: 'Arial', fontSize: 20, color: '#000000', align: 'center', backgroundColor: 'rgba(255,0,0,0.5)'});
        this.totalButtonWidth = this.totalButtonWidth + button.width;
        button.setInteractive();
        button.on('pointerdown', buttonData.callbackFunction);
        button.setDepth(12);
        this._buttons.push(button);
      }
      this.totalButtonWidth = this.totalButtonWidth + bubblePadding*(this._buttons.length - 1);

      var b = this._speech.getBounds();

      var bubbleWidth = this._width;//b.width * 12 / 10;//
      var bubbleHeight = this.getBubbleHeight();//this._height;
      var arrowHeight = this.getArrowHeight(bubbleHeight);

      this._originalWidth = bubbleWidth;
      this._originalHeight = bubbleHeight + arrowHeight;

      this._bubble = this._scene.add.graphics({ x: this._x, y: this._y - bubbleHeight - arrowHeight });
      this._bubble.setDepth(10);

      this._speech.setPosition(this._bubble.x + (bubbleWidth / 2) - (b.width / 2), this._bubble.y + bubblePadding);
      var xOffset = 0;
      for (i = 0; i < this._buttons.length; i++) {
        var button = this._buttons[i];
        button.x = this._speech.x + this._speech.width/2 - this.totalButtonWidth / 2 + xOffset;
        button.y = this._speech.y + this._speech.height + bubblePadding;
        xOffset = xOffset + button.width + bubblePadding;
      }

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
