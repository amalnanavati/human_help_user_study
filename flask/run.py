#!/usr/bin/env python3

import os
import json
import random
import string
import time
import traceback
import datetime

from flask import Flask, render_template, send_file, request, redirect
from flask_cors import CORS

numGIDs = 3
gidsToTest = ["0", "1"]
minUUID = 3000
completedGIDsFilename = "outputs/completedGIDs.json"

completionCodesToUUIDFilename = "outputs/completionCodesToUUID.json"

app = Flask(__name__)
CORS(app, resources={r"*": {"origins": "*"}})

def get_random_alphaNumeric_string(stringLength=10):
    lettersAndDigits = string.ascii_letters + string.digits
    return ''.join((random.choice(lettersAndDigits) for i in range(stringLength)))

class Logger(object):
    def __init__(self, logDir="outputs/", filename="log.txt"):
        self.f = open(logDir+filename, "a")
        self.datetimeFormatStr = "{:%b %d, %Y %Z %H:%M:%S:%f}"
        beginningStr = """
********************************************************************************
[{}] BEGIN LOGGING
********************************************************************************
""".format(self.datetimeFormatStr.format(datetime.datetime.now()))
        print(beginningStr)
        self.f.write(beginningStr)

        self.timesSinceLastFlush = 0
        self.flushEveryNTimes = 3000 # roughly once every two minutes when there is one user playing the tutorial/game

    def logPrint(self, *args, printToOutput=True, **kwargs):
        self.timesSinceLastFlush += 1
        headerStr = "[{}] ".format(self.datetimeFormatStr.format(datetime.datetime.now()))
        self.f.write(headerStr)
        for argument in args:
            self.f.write(str(argument))
            self.f.write(", ")
        self.f.write("\n")

        if (self.timesSinceLastFlush >= self.flushEveryNTimes):
            self.f.flush()
            os.fsync(self.f.fileno())
            self.timesSinceLastFlush = 0
            print("Cleared logfile buffer")

        if (printToOutput):
            printArgs = [headerStr, *args]
            print(*printArgs, **kwargs)

    def logRaiseException(self, *args, **kwargs):
        self.timesSinceLastFlush += 1
        headerStr = "[{}] ".format(self.datetimeFormatStr.format(datetime.datetime.now()))
        self.f.write(headerStr)
        for argument in args:
            self.f.write(str(argument))
            self.f.write(", ")
        self.f.write("\n")

        if (self.timesSinceLastFlush >= self.flushEveryNTimes):
            self.f.flush()
            os.fsync(self.f.fileno())
            self.timesSinceLastFlush = 0
            print("Cleared logfile buffer")

        printArgs = [headerStr, *args]
        raise Exception(*printArgs, **kwargs)

    def close(self):
        endingStr = """
********************************************************************************
[{}] END LOGGING
********************************************************************************
""".format(self.datetimeFormatStr.format(datetime.datetime.now()))
        print(endingStr)
        self.f.write(endingStr)
        self.f.close()

class FlaskExample:

    def run(self):
        app = Flask(
            __name__, static_url_path='/static', template_folder='./templates')
        app.secret_key = 'example_secret_key_change_this_later'

        def _check_and_send_file(filename, dirname):
            logger.logPrint("{}: _check_and_send_file({}, {})".format(request.remote_addr, filename, dirname), printToOutput=False)
            filename = filename.strip()
            target_filepath = os.path.join('./{}'.format(dirname), filename)
            if not os.path.exists(target_filepath):
                logger.logPrint("Could not find ", target_filepath)
                return json.dumps(
                    {'status': 'failed', 'msg': 'cannot find the file'}), 500
            return send_file(target_filepath)

        def updateInProgressUUIDs():
            # Remove UUIDs that have not been updated for maxWaitTimeBeforeDeletingUUID
            logger.logPrint("Update in progress UUIDs")
            uuidsToDelete = []
            for uuidTemp in inProgressUUIDs:
                if time.time() >= inProgressUUIDs[uuidTemp][1] + maxWaitTimeBeforeDeletingUUID:
                    uuidsToDelete.append(uuidTemp)
            for uuidTemp in uuidsToDelete:
                del inProgressUUIDs[uuidTemp]
                if uuidTemp in inProgressUUIDLogStateFiles:
                    inProgressUUIDLogStateFiles[uuidTemp].flush()
                    os.fsync(inProgressUUIDLogStateFiles[uuidTemp].fileno())
                    inProgressUUIDLogStateFiles[uuidTemp].close()
                    del inProgressUUIDLogStateFiles[uuidTemp]
            uuidsToDelete = []
            for uuidTemp in inProgressUUIDLogStateFiles:
                if uuidTemp not in inProgressUUIDs:
                    uuidsToDelete.append(uuidTemp)
            for uuidTemp in uuidsToDelete:
                del inProgressUUIDLogStateFiles[uuidTemp]
            logger.logPrint("inProgressUUIDs", inProgressUUIDs)
            logger.logPrint("inProgressUUIDLogStateFiles", inProgressUUIDLogStateFiles)

        @app.route('/')
        def root():
            """
            Assign this user a new unique user ID
            """
            global minUUID
            # Get all pre-assigned user IDs as ints
            uuids = []
            for uuid in os.listdir("./outputs"):
                try:
                    uuids.append(int(uuid))
                except:
                    continue
            uuids.sort()

            # Get the lowest free user ID
            uuidToAssign = minUUID # the UUIDs below this cannot be automatically assigned
            for uuid in uuids:
                if uuid == uuidToAssign:
                    uuidToAssign += 1
            logger.logPrint("{}: Got new user, assigned UUID {}".format(request.remote_addr, uuidToAssign))

            updateInProgressUUIDs()

            return redirect('./consent/{}'.format(uuidToAssign))

        # The landing page for user with uid
        @app.route('/consent/<uuid>')
        def consent(uuid):
            logger.logPrint("{}: Showing the consent form to UUID {}".format(request.remote_addr, uuid))

            dirname = "outputs/{}".format(uuid)
            if not os.path.exists(dirname):
                os.makedirs(dirname)

            updateInProgressUUIDs()

            # Save the startTime
            timestamp = time.time()
            fname = "outputs/{}/startTime.txt".format(uuid)
            with open(fname, "w") as f:
                f.write(str(timestamp))

            return render_template('consent.html', uuid=uuid)

        # The progression image for user with uuid
        @app.route('/progression', methods=['POST'])
        def progression():
            uuid = request.form['uuid']

            logger.logPrint("{}: Showing the progression page to UUID {}".format(request.remote_addr, uuid))

            updateInProgressUUIDs()

            # Save the startTime
            timestamp = time.time()
            fname = "outputs/{}/progressionTime.txt".format(uuid)
            with open(fname, "w") as f:
                f.write(str(timestamp))

            return render_template('progression.html', uuid=uuid)

        # Called when the consent form is submitted
        @app.route('/tutorial', methods=['POST'])
        def tutorial():
            uuid = request.form['uuid']

            logger.logPrint("{}: Showing the tutorial to UUID {}".format(request.remote_addr, uuid))

            updateInProgressUUIDs()

            # Save the tutorialTime
            timestamp = time.time()
            fname = "outputs/{}/tutorialTime.txt".format(uuid)
            with open(fname, "w") as f:
                f.write(str(timestamp))

            gid = 0

            fname ="outputs/{}/{}_tutorial_data.json".format(uuid, gid)
            try:
                if uuid in inProgressUUIDLogStateFiles:
                    logger.logPrint("tutorial closing old logStateFile {}".format(inProgressUUIDLogStateFiles[uuid]))
                    inProgressUUIDLogStateFiles[uuid].flush()
                    os.fsync(inProgressUUIDLogStateFiles[uuid].fileno())
                    inProgressUUIDLogStateFiles[uuid].close()
                    del inProgressUUIDLogStateFiles[uuid]

                inProgressUUIDLogStateFiles[uuid] = open(fname, "w")
                inProgressUUIDLogStateFiles[uuid].write("")

                logger.logPrint("Wrote initial tutorial log_state for UUID {} GID {} to {}".format(uuid, gid, fname))
            except Exception as err:
                logger.logPrint("tutorial failure to create state file for UUID {} GID {}: {}\n{}".format(uuid, gid, err, traceback.format_exc()))
                gotError = True

            # Render the tutorial
            return render_template('game.html', uuid=uuid, gid=0, tutorial="true")

        # Called when the tutorial is completed
        @app.route('/game', methods=['POST'])
        def game():
            global completedGameIDs, minUUID, gidsToTest

            uuid = request.form['uuid']
            order = request.form['order']

            logger.logPrint("{}: Showing the game to UUID {} order {}".format(request.remote_addr, uuid, order))

            # Save the gameTime
            timestamp = time.time()
            fname = "outputs/{}/gameTime_{}.txt".format(uuid, order)
            with open(fname, "w") as f:
                f.write(str(timestamp))

            updateInProgressUUIDs()

            logger.logPrint("completedGameIDs", completedGameIDs)

            # # Assign the user a game ID
            if (order == "a"):
                # gidWithMinNumUsers = 4
                if int(uuid) == 18:
                    gidWithMinNumUsers = "0"
                elif int(uuid) == 19:
                    gidWithMinNumUsers = "1"
                elif int(uuid) == 20:
                    gidWithMinNumUsers = "2"
                else:
                    gidAndUsersList = [] # (numRealAndInProgressUsers, numRealUsers, gid)
                    for i in range(len(gidsToTest)):
                        gid = gidsToTest[i]
                        numRealUsers = 0
                        numInProgressUsers = 0
                        for tempUUID in completedGameIDs[gid]:
                            if int(tempUUID) >= minUUID: # only count actual users
                                numRealUsers += 1
                        for uuidTemp in inProgressUUIDs:
                            # If the user is still playing the game or the game is finished
                            # if time.time() <= inProgressUUIDs[uuidTemp][1] + maxBreaktime or inProgressUUIDs[uuidTemp][2]:
                            if inProgressUUIDs[uuidTemp][0] == gid:
                                numInProgressUsers += 1
                        gidAndUsersList.append((numRealUsers+numInProgressUsers, numRealUsers, i, gid))
                    gidAndUsersList.sort()
                    logger.logPrint("gidAndUsersList", gidAndUsersList)
                    gidWithMinNumUsers = gidAndUsersList[0][3]
            else: # For order b, pick the GID you did not do for order a
                gid = request.form['gid']
                logger.logPrint("UUID {} order {} old GID {}".format(request.remote_addr, uuid, order, gid))
                if str(gid) == gidsToTest[0]:
                    gidWithMinNumUsers = gidsToTest[1]
                else:
                    gidWithMinNumUsers = gidsToTest[0]

            logger.logPrint("Assigned UUID {} order {} GID {}".format(uuid, order, gidWithMinNumUsers))

            fname ="outputs/{}/{}_data.json".format(uuid, gidWithMinNumUsers)
            try:
                if uuid in inProgressUUIDLogStateFiles:
                    logger.logPrint("game closing old logStateFile {}".format(inProgressUUIDLogStateFiles[uuid]))
                    inProgressUUIDLogStateFiles[uuid].flush()
                    os.fsync(inProgressUUIDLogStateFiles[uuid].fileno())
                    inProgressUUIDLogStateFiles[uuid].close()
                    del inProgressUUIDLogStateFiles[uuid]

                inProgressUUIDLogStateFiles[uuid] = open(fname, "w")
                inProgressUUIDLogStateFiles[uuid].write("")

                logger.logPrint("Wrote initial log_state for UUID {} order {} GID {} to {}".format(uuid, order, gid, fname))
            except Exception as err:
                logger.logPrint("game failure to create state file for UUID {} order {} GID {}: {}\n{}".format(uuid, order, gid, err, traceback.format_exc()))

            if (order == "a"): inProgressUUIDs[uuid] = [gidWithMinNumUsers, time.time()]#, False]
            # Render the tutorial
            return render_template('game.html', uuid=uuid, gid=gidWithMinNumUsers, order=order)

        # Called when the game is completed
        @app.route('/survey', methods=['POST'])
        def survey():
            uuid = request.form['uuid']
            gid = request.form['gid']
            order = request.form['order']

            logger.logPrint("{}: Showing survey to UUID {} order {} GID {}".format(request.remote_addr, uuid, order, gid))

            updateInProgressUUIDs()

            if uuid in inProgressUUIDLogStateFiles:
                logger.logPrint("survey UUID {} order {} closing old logStateFile {}".format(uuid, order, inProgressUUIDLogStateFiles[uuid]))
                inProgressUUIDLogStateFiles[uuid].flush()
                os.fsync(inProgressUUIDLogStateFiles[uuid].fileno())
                inProgressUUIDLogStateFiles[uuid].close()
                del inProgressUUIDLogStateFiles[uuid]
            else:
                logger.logPrint("ERROR survey UUID {} order {} no old logStateFile exists".format(uuid, order))

            if uuid in inProgressUUIDs and order == "a":
                inProgressUUIDs[uuid] = [gid, time.time()]

            # Save the surveyTime
            timestamp = time.time()
            fname = "outputs/{}/surveyTime_{}.txt".format(uuid, order)
            with open(fname, "w") as f:
                f.write(str(timestamp))

            return render_template('survey.html', uuid=uuid, gid=gid, order=order)

        @app.route('/survey_test/<uuid>/<order>', methods=['GET'])
        def survey_test(uuid, order):
            gid = -1
            return render_template('survey.html', uuid=uuid, gid=gid, order=order)

        @app.route('/game_test/<uuid>/<gid>/<order>', methods=['GET'])
        def game_test(uuid, gid, order):
            return render_template('game.html', uuid=uuid, gid=gid, order=order)

        # Called when the survey is submitted
        @app.route('/completionCode', methods=['POST'])
        def completionCode():
            global completedGameIDs

            uuid = request.form['uuid']
            gid = request.form['gid']

            logger.logPrint("{}: Showing completion code to UUID {} GID {}".format(request.remote_addr, uuid, gid))

            updateInProgressUUIDs()

            # Generate and save completion code
            completionCode = None
            while completionCode is None or completionCode in completionCodes:
                completionCode = get_random_alphaNumeric_string()
            fname = "outputs/{}/completionCode.txt".format(uuid)
            with open(fname, "w") as f:
                f.write(completionCode)
            completionCodes[completionCode] = uuid
            with open(completionCodesToUUIDFilename, "w") as f:
                json.dump(completionCodes, f)

            # Update and save the completedGameIDs; completedGameIDs contains the first GID
            if str(gid) == gidsToTest[0]:
                completedGameIDs[str(gidsToTest[1])].append(uuid)
            else:
                completedGameIDs[str(gidsToTest[0])].append(uuid)

            with open(completedGIDsFilename, "w") as f:
                json.dump(completedGameIDs, f)

            if uuid in inProgressUUIDs:
                del inProgressUUIDs[uuid]
            # TODO check that this works!!
            if uuid in inProgressUUIDLogStateFiles:
                inProgressUUIDLogStateFiles[uuid].flush()
                os.fsync(inProgressUUIDLogStateFiles[uuid].fileno())
                inProgressUUIDLogStateFiles[uuid].close()
                del inProgressUUIDLogStateFiles[uuid]

            # Save the endTime
            timestamp = time.time()
            fname = "outputs/{}/endTime.txt".format(uuid)
            with open(fname, "w") as f:
                f.write(str(timestamp))

            return render_template('completionCode.html', completionCode=completionCode)

        # Load and replay a saved game
        @app.route('/load_game_<uuid>_<gid>_<starting_dtime>')
        def load_game(uuid, gid, starting_dtime):

            logger.logPrint("{}: Loading game for UUID {} GID {} starting_dtime {}".format(request.remote_addr, uuid, gid, starting_dtime))

            starting_dtime = int(starting_dtime)

            dataToLoad = []
            # fname ="outputs/{}/{}_data.json".format(uuid, gid)
            fname ="ec2_outputs_evaluation/{}/{}_data.json".format(uuid, gid)
            with open(fname, "r") as f:
                for cnt, line in enumerate(f):
                    if len(line.strip()) == 0:
                        break
                    dataToLoad.append(json.loads(line))
                # Sometimes, the data arrives a few ms out of order
                if "gameStateID" in dataToLoad[0]:
                    dataToLoad.sort(key=lambda x : int(x['gameStateID']))
                else:
                    dataToLoad.sort(key=lambda x : int(x['dtime']))

            # Remove duplicates dtimes -- removed because multiple logs *can* happen in the same ms
            # i = 1
            # while i < len(dataToLoad):
            #     if dataToLoad[i]['dtime'] == dataToLoad[i-1]['dtime']:
            #         dataToLoad.pop(i-1)
            #     else:
            #         i += 1

            return render_template('game.html', uuid=uuid, gid=gid, load="true", dataToLoad=dataToLoad, starting_dtime=starting_dtime)

        # Called to log the game state
        @app.route('/log_game_state', methods=['POST'])
        def log_game_state():
            logger.logPrint("{}: log_game_state".format(request.remote_addr))
            return log_state(request, tutorial=False)

        @app.route('/log_tutorial_state', methods=['POST'])
        def log_tutorial_state():
            logger.logPrint("{}: log_tutorial_state".format(request.remote_addr))
            return log_state(request, tutorial=True)

        def log_state(request, tutorial):
            successGameStateIDs = []
            failedGameStateIDs = []
            largestGameStateID = None
            numReceivedLogs = len(request.json);
            logger.logPrint("Received game state log of batch size {}".format(len(request.json)))
            for data in request.json:
                uuid = data['uuid']
                gid = data['gid']

                logger.logPrint("Log state for UUID {} GID {} gameStateID {} dtime {} eventType {} tutorial {}".format(uuid, gid, data['gameStateID'], data['dtime'], data['eventType'], tutorial))

                if largestGameStateID is None or int(data['gameStateID']) > largestGameStateID:
                    largestGameStateID = int(data['gameStateID'])

                if (not tutorial):
                    # Either the user is in COMPLETED_TASKS or the eventType is SHIFT_GAME_KILL
                    # isGameComplete = (request.json["player"]["currentState"] == "2" or
                    #                   request.json["eventType"] == "11")
                    if uuid in inProgressUUIDs: # to mainly keep just the first GID
                        inProgressUUIDs[uuid] = [inProgressUUIDs[uuid][0], time.time()]#, isGameComplete]
                    else:
                        inProgressUUIDs[uuid] = [gid, time.time()]#, isGameComplete]

                if tutorial:
                    fname ="outputs/{}/{}_tutorial_data.json".format(uuid, gid)
                else:
                    fname ="outputs/{}/{}_data.json".format(uuid, gid)
                try:
                    dataJSON = json.dumps(data, separators=(',', ':'))

                    if uuid not in inProgressUUIDLogStateFiles:
                        logger.logPrint("log_state reopen logFile for UUID {} GID {} gameStateID {} tutorial {}".format(uuid, gid, data['gameStateID'], tutorial))
                        inProgressUUIDLogStateFiles[uuid] = open(fname, "a")

                    inProgressUUIDLogStateFiles[uuid].write(dataJSON+"\n")
                    logger.logPrint("Wrote log for UUID {} GID {} gameStateID {} to {}".format(uuid, gid, data['gameStateID'], fname))
                    successGameStateIDs.append(data['gameStateID'])
                except Exception as err:
                    logger.logPrint("log_state failure for UUID {} GID {} gameStateID {}: {}\n{}".format(uuid, gid, data['gameStateID'], err, traceback.format_exc()))
                    failedGameStateIDs.append(data['gameStateID'])
            if len(successGameStateIDs) > 0:
                retval = json.dumps({
                    'status': 'success',
                    'msg': 'saved',
                    'successGameStateIDs': successGameStateIDs,
                    'failedGameStateIDs': failedGameStateIDs,
                    'largestGameStateID': largestGameStateID,
                    'numReceivedLogs': numReceivedLogs,
                })
                # time.sleep(5);
                return retval
            else:
                retval = json.dumps({
                    'status': 'failed',
                    'msg': 'error writing',
                    'successGameStateIDs': successGameStateIDs,
                    'failedGameStateIDs': failedGameStateIDs,
                    'largestGameStateID': largestGameStateID,
                    'numReceivedLogs': numReceivedLogs,
                })
                return retval, 500


        # Called to log the game config
        @app.route('/log_game_config', methods=['POST'])
        def log_game_config():
            logger.logPrint("{}: log_game_config".format(request.remote_addr))
            return log_config(request, tutorial=False)

        @app.route('/log_tutorial_config', methods=['POST'])
        def log_tutorial_config():
            logger.logPrint("{}: log_tutorial_config".format(request.remote_addr))
            return log_config(request, tutorial=True)

        def log_config(request, tutorial):
            uuid = request.json['uuid']
            gid = request.json['gid']

            logger.logPrint("Log config for UUID {} GID {} tutorial {}".format(uuid, gid, tutorial))

            dirname = "outputs/{}".format(uuid)
            if not os.path.exists(dirname):
                os.makedirs(dirname)

            gotError = False

            if tutorial:
                fname = "outputs/{}/{}_tutorial_config.json".format(uuid, gid)
            else:
                fname = "outputs/{}/{}_config.json".format(uuid, gid)
            try:
                with open(fname, "w") as f:
                    dataJSON = json.dumps(request.json, separators=(',', ':'))
                    f.write(dataJSON+"\n")
                    logger.logPrint("Wrote log_config for UUID {} GID {} to {}".format(uuid, gid, fname))
                return json.dumps({'status': 'success', 'msg': 'saved'})
            except Exception as err:
                logger.logPrint("log_config failure for UUID {} GID {}: {}\n{}".format(uuid, gid, err, traceback.format_exc()))
                traceback.print_exc()
                return json.dumps({'status': 'failed', 'msg': 'error writing'}), 500

        @app.route('/get_room_connection_graph')
        def get_room_connection_graph():
            return render_template('getRoomConnectionGraph.html')

        @app.route('/get_room_connection_graph_finished', methods=['POST'])
        def get_room_connection_graph_finished():
            fname = "assets/map_distances.json"
            with open(fname, "w") as f:
                dataJSON = json.dumps(request.json)#, separators=(',', ':'))
                f.write(dataJSON+"\n")
                logger.logPrint("Wrote room connection graph to {}".format(fname))

            return json.dumps({'status': 'success', 'msg': 'saved'})

        @app.route('/get_min_task_time')
        def get_min_task_time():
            return render_template('getMinTaskTime.html')

        @app.route('/get_min_task_time_finished', methods=['POST'])
        def get_min_task_time_finished():
            fname = "assets/min_task_time.json"
            with open(fname, "w") as f:
                dataJSON = json.dumps(request.json)#, separators=(',', ':'))
                f.write(dataJSON+"\n")
                logger.logPrint("Wrote minTaskTime to {}".format(fname))

            return json.dumps({'status': 'success', 'msg': 'saved'})

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

        app.debug = False
        app.run(host='0.0.0.0', port=8194, threaded=True)


if __name__ == '__main__':
    logger = Logger()

    if os.path.isfile(completedGIDsFilename):
        with open(completedGIDsFilename, "r") as f:
            completedGameIDs = json.load(f)
    else:
        completedGameIDs = {str(gid) : [] for gid in range(numGIDs)}
    logger.logPrint("completedGameIDs", completedGameIDs)

    if os.path.isfile(completionCodesToUUIDFilename):
        with open(completionCodesToUUIDFilename, "r") as f:
            completionCodes = json.load(f)
    else:
        completionCodes = {}
    logger.logPrint("completionCodes", completionCodes)

    inProgressUUIDs = {} # uuid -> [GID, lastTimestepGotGameState, isFinished]
    # maxBreaktime = 90 # Max time to wait for a game state log before reassigning the GID
    maxWaitTimeBeforeDeletingUUID = 40*60 # if no new log states are received within this much time, delete this uuid from inProgressUUIDs
    inProgressUUIDLogStateFiles = {}

    server = FlaskExample()

    server.run()

    for uuid in inProgressUUIDLogStateFiles:
        inProgressUUIDLogStateFiles[uuid].flush()
        os.fsync(inProgressUUIDLogStateFiles[uuid].fileno())
        inProgressUUIDLogStateFiles[uuid].close()

    logger.close()
