# Dependencies
```
pip3 install flask
pip3 install flask_cors
```

# Usage
```
cd flask
python3 run_example.py
```

Go to `http://0.0.0.0:8194/index/30` to see what a participant with unique user ID 30 would see.

# Code Explained

The main game code is in `flask/templates/game.html`. It refers to numerous helper code files in `flask/static/game_src`. Those helper files are organized roughly thematically, but due to the nature of Phaser3 it is hard to make the code fully modular. So code in some of the helper files refers to variables/attributes in other files. 
