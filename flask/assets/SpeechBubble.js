class SpeechBubble {
  constructor(scene, width, x, y, text) {
    // x, y is at the bottom of the arrow
    this._scene = scene;
    this._width = width;
    this._x = y;
    this._y = y;
    this._text = text;
    this.createSpeechBubble();
    this._visibility = true;
  }
  setVisibile(visible) {
    this._bubble.visible = visible;
    this._speech.visible = visible;
  }
  getVisibile() {
    return this._bubble.visible;
  }
  getBubbleHeight() {
    return this._speech.getBounds().height * 12 / 10;
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
    return this._width/10;
  }
  getSpeechWidth() {
    return this._width - (this.getBubblePadding() * 2);
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
    var b = this._speech.getBounds();
    this._speech.x = this._bubble.x + (this._width / 2) - (b.width / 2); // the horizontal centering has changed
    this._speech.y = this._bubble.y + (this.getBubbleHeight() / 2) - (b.height / 2);
  }
  setText(text) {
    this._text = text;
    this._speech.text = text;
    // Adjust the height for the new text
    var newHeight = this.getHeight();
    this._bubble.scaleY = newHeight / this._originalHeight;
    this._bubble.y = this._y - newHeight;
    var b = this._speech.getBounds();
    this._speech.x = this._bubble.x + (this._width / 2) - (b.width / 2); // the horizontal centering has changed
    this._speech.y = this._bubble.y + (this.getBubbleHeight() / 2) - (b.height / 2);
  }
  setPosition(x, y) {
    // x, y is at the bottom of the arrow
    this._x = x;
    this._y = y;
    var b = this._speech.getBounds();
    this._bubble.x = x - this.getArrowXOffset();
    this._bubble.y = y - this.getHeight();
    this._speech.setPosition(this._bubble.x + (this._width / 2) - (b.width / 2), this._bubble.y + (this.getBubbleHeight() / 2) - (b.height / 2));
  }
  createSpeechBubble ()
  {
      var bubblePadding = this.getBubblePadding();
      this._speech = this._scene.add.text(0, 0, this._text, { fontFamily: 'Arial', fontSize: 20, color: '#000000', align: 'center', wordWrap: { width: this.getSpeechWidth() } });
      this._speech.setDepth(11);

      var b = this._speech.getBounds();

      var bubbleWidth = this._width;//b.width * 12 / 10;//
      var bubbleHeight = b.height * 12 / 10;//this._height;
      var arrowHeight = this.getArrowHeight(bubbleHeight);

      this._originalWidth = bubbleWidth;
      this._originalHeight = bubbleHeight + arrowHeight;

      this._bubble = this._scene.add.graphics({ x: this._x, y: this._y - bubbleHeight - arrowHeight });

      this._speech.setPosition(this._bubble.x + (bubbleWidth / 2) - (b.width / 2), this._bubble.y + (bubbleHeight / 2) - (b.height / 2));

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
