#!/usr/bin/env python3

# Standard Library Imports
import logging
import os
import json
import random
import string
import time
import traceback
import datetime
import copy
from threading import Lock, Timer, Thread

# Local Imports
from logger import Logger
from robot import Robot
from users import Users
from helpers import get_random_alpha_numeric_string

# Glask Imports
from flask import Flask, render_template, send_file, request, redirect
from flask_cors import CORS
from flask_socketio import SocketIO, send, emit



# Create the Server
app = Flask(__name__, static_url_path='/static', template_folder='./templates')
app.secret_key = 'example_secret_key_change_this_later'
CORS(app, resources={r"*": {"origins": "*"}})
socketio = SocketIO(app, logger = False, engineio_logger = False)



# Enable to Logger
logger = Logger()

# Concurrency Literals
isRunningLock = Lock()
isRunning = False
usersLock = Lock()

# Variables to maintain game state
robot = Robot()
users = Users()

def controlLoop():
    loopDuration = 0.02 # sec
    currLoopStartTime, prevLoopStartTime = None, None
    while (True):
        # Sync the loop duration
        currLoopStartTime = time.time()
        if prevLoopStartTime is not None and currLoopStartTime-prevLoopStartTime<loopDuration:
            time.sleep(loopDuration-(currLoopStartTime-prevLoopStartTime))
        prevLoopStartTime = time.time()

        # Only continue the loop while the server is running
        isRunningLock.acquire()
        if (isRunning):
            isRunningLock.release()
            usersLock.acquire()
            userLocations = users.getUserLocations()
            userStatesToSend = users.getStatesToSend()
            usersLock.release()
            robot.update(userLocations)
            dataToSend = {
                "users" : userStatesToSend,
                "robot" : robot.getDict(),
            }
            #logger.logPrint("dataToSend", dataToSend)
            socketio.emit("updateStates", dataToSend)
        else:
            isRunningLock.release()
            break
    logger.logPrint("in controlLoop out of while")

def _check_and_send_file(filename, dirname):
    logger.logPrint("{}: _check_and_send_file({}, {})".format(request.remote_addr, filename, dirname), printToOutput=False)
    filename = filename.strip()
    target_filepath = os.path.join('./{}'.format(dirname), filename)
    if not os.path.exists(target_filepath):
        logger.logPrint("Could not find ", target_filepath)
        return json.dumps(
            {'status': 'failed', 'msg': 'cannot find the file'}), 500
    return send_file(target_filepath)

@app.route('/')
def root():
    """
    Assign this user a new unique user ID
    """
    return "Hello World"

@app.route('/<uuid>')
def game(uuid):
    return render_template('game.html', uuid=uuid)

@socketio.on("log_game_state")
def handle_log_game_state(msg):
    timestamp = time.time()
    uuid = int(msg["uuid"])
    usersLock.acquire()
    users.addUserState(uuid, timestamp, msg)
    usersLock.release()
    logger.logPrint("msg", msg)

# Called to access files in the assets folder
@app.route('/assets/<source>', methods=['GET'])
def get_file(source):
    logger.logPrint("{}: _check_and_send_file({})".format(request.remote_addr, source), printToOutput=False)
    return _check_and_send_file(source, "assets")

# Called to access files in the assets folder
@app.route('/assets/tasks/<source>', methods=['GET'])
def get_task_file(source):
    logger.logPrint("{}: get_task_file({})".format(request.remote_addr, source), printToOutput=False)
    return _check_and_send_file(source, "assets/tasks")

def run():
    global isRunningLock, isRunning

    isRunningLock.acquire()
    isRunning = True
    isRunningLock.release()
    controlLoopThread = Thread(target=controlLoop)
    controlLoopThread.start()

    app.debug = False
    socketio.run(app, host='localhost', port=8194)# threaded=True)

run()

logger.close()
