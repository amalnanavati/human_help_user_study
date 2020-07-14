#!/usr/bin/env python3

import os
import json
import pickle
import random
import string
import time
from flask import Flask, render_template, send_file, request, redirect
from flask_cors import CORS

numGIDs = 5
completedGIDsFilename = "outputs/completedGIDs.json"

completionCodesToUUIDFilename = "outputs/completionCodesToUUID.pkl"

app = Flask(__name__)
CORS(app, resources={r"*": {"origins": "*"}})

def get_random_alphaNumeric_string(stringLength=10):
    lettersAndDigits = string.ascii_letters + string.digits
    return ''.join((random.choice(lettersAndDigits) for i in range(stringLength)))

class FlaskExample:

    def run(self):
        app = Flask(
            __name__, static_url_path='/static', template_folder='./templates')
        app.secret_key = 'example_secret_key_change_this_later'

        def _check_and_send_file(filename, dirname):
            filename = filename.strip()
            target_filepath = os.path.join('./{}'.format(dirname), filename)
            if not os.path.exists(target_filepath):
                print("Could not find ", target_filepath)
                return json.dumps(
                    {'status': 'failed', 'msg': 'cannot find the file'})
            return send_file(target_filepath)

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
            print("Got new user, assigned UUID {}".format(uuidToAssign))

            return redirect('./consent/{}'.format(uuidToAssign))

        # The landing page for user with uid
        @app.route('/consent/<uuid>')
        def consent(uuid):
            print("Showing the consent form to UUID {}".format(uuid))

            dirname = "outputs/{}".format(uuid)
            if not os.path.exists(dirname):
                os.makedirs(dirname)

            # Save the startTime
            timestamp = time.time()
            fname = "outputs/{}/startTime.txt".format(uuid)
            with open(fname, "w") as f:
                f.write(str(timestamp))

            return render_template('consent.html', uuid=uuid)

        # Called when the consent form is submitted
        @app.route('/tutorial', methods=['POST'])
        def tutorial():
            uuid = request.form['uuid']

            print("Showing the tutorial to UUID {}".format(uuid))

            # Save the startTime
            timestamp = time.time()
            fname = "outputs/{}/tutorialTime.txt".format(uuid)
            with open(fname, "w") as f:
                f.write(str(timestamp))

            # Render the tutorial
            return render_template('game.html', uuid=uuid, gid=0, tutorial="true")

        # Called when the tutorial is completed
        @app.route('/game', methods=['POST'])
        def game():
            global completedGameIDs, minUUID

            uuid = request.form['uuid']

            # Save the startTime
            timestamp = time.time()
            fname = "outputs/{}/gameTime.txt".format(uuid)
            with open(fname, "w") as f:
                f.write(str(timestamp))

            # # Assign the user a game ID
            if int(uuid) == 18:
                gidWithMinNumUsers = 4
            elif int(uuid) < 100:
                gidWithMinNumUsers = random.randint(0, 4)
            else:
                gidWithMinNumUsers = None
                minNumUsers = None
                for gid in ["2","0","4"]:#completedGameIDs:
                    numUsers = 0
                    for tempUUID in completedGameIDs[gid]:
                        if int(tempUUID) >= minUUID: # only count actual users
                            numUsers += 1
                    if minNumUsers is None or numUsers < minNumUsers:
                        minNumUsers = numUsers
                        gidWithMinNumUsers = gid
            # Render the tutorial
            return render_template('game.html', uuid=uuid, gid=gidWithMinNumUsers)

        # Called when the game is completed
        @app.route('/survey', methods=['POST'])
        def survey():
            uuid = request.form['uuid']
            gid = request.form['gid']

            # Save the startTime
            timestamp = time.time()
            fname = "outputs/{}/surveyTime.txt".format(uuid)
            with open(fname, "w") as f:
                f.write(str(timestamp))

            return render_template('survey.html', uuid=uuid, gid=gid)

        # Called when the survey is submitted
        @app.route('/completionCode', methods=['POST'])
        def completionCode():
            global completedGameIDs

            uuid = request.form['uuid']
            gid = request.form['gid']

            # Generate and save completion code
            completionCode = None
            while completionCode is None or completionCode in completionCodes:
                completionCode = get_random_alphaNumeric_string()
            fname = "outputs/{}/completionCode.txt".format(uuid)
            with open(fname, "w") as f:
                f.write(completionCode)
            completionCodes[completionCode] = uuid
            with open(completionCodesToUUIDFilename, "wb") as f:
                pickle.dump(completionCodes, f)

            # Update and save the completedGameIDs
            completedGameIDs[gid].append(uuid)
            with open(completedGIDsFilename, "w") as f:
                json.dump(completedGameIDs, f)

            # Save the endTime
            timestamp = time.time()
            fname = "outputs/{}/endTime.txt".format(uuid)
            with open(fname, "w") as f:
                f.write(str(timestamp))

            return render_template('completionCode.html', completionCode=completionCode)

        # # Called when the demography questionairre is submitted
        # # TODO: make this make another post request for game so game has a proper URL
        # @app.route('/demography', methods=['POST'])
        # def demography():
        #     # age = request.form['age']
        #     # gender = request.form['gender']
        #     data = dict(request.form)
        #
        #     uuid = request.form['uuid']
        #     dirname = "outputs/{}".format(uuid)
        #     if not os.path.exists(dirname):
        #         os.makedirs(dirname)
        #
        #     fname ="outputs/{}/demography.json".format(uuid)
        #     with open(fname, "w") as f:
        #         json.dump(data, f)
        #         print("Wrote to ", fname)
        #
        #     return render_template('game.html', uuid=uuid, gid=0)

        # Load and replay a saved game
        @app.route('/load_game_<uuid>_<gid>')
        def load_game(uuid, gid):
            dataToLoad = []
            fname ="outputs/{}/{}_data.json".format(uuid, gid)
            # fname ="ec2_outputs/{}/{}_data.json".format(uuid, gid)
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

            # Remove duplicates
            # i = 1
            # while i < len(dataToLoad):
            #     if dataToLoad[i]['dtime'] == dataToLoad[i-1]['dtime']:
            #         dataToLoad.pop(i-1)
            #     else:
            #         i += 1
            return render_template('game.html', uuid=uuid, gid=gid, load="true", dataToLoad=dataToLoad)

        # Called to log the game state
        @app.route('/log_game_state', methods=['POST'])
        def log_game_state():
            return log_state(request, tutorial=False)

        @app.route('/log_tutorial_state', methods=['POST'])
        def log_tutorial_state():
            return log_state(request, tutorial=True)

        def log_state(request, tutorial):
            uuid = request.json['uuid']
            gid = request.json['gid']

            if tutorial:
                fname ="outputs/{}/{}_tutorial_data.json".format(uuid, gid)
            else:
                fname ="outputs/{}/{}_data.json".format(uuid, gid)
            with open(fname, "a") as f:
                dataJSON = json.dumps(request.json, separators=(',', ':'))
                f.write(dataJSON+"\n")
                print("Wrote to ", fname)

            return json.dumps(
                {'status': 'success', 'msg': 'saved'})

        # Called to log the game config
        @app.route('/log_game_config', methods=['POST'])
        def log_game_config():
            return log_config(request, tutorial=False)

        @app.route('/log_tutorial_config', methods=['POST'])
        def log_tutorial_config():
            return log_config(request, tutorial=True)

        def log_config(request, tutorial):
            uuid = request.json['uuid']
            gid = request.json['gid']

            dirname = "outputs/{}".format(uuid)
            if not os.path.exists(dirname):
                os.makedirs(dirname)

            if tutorial:
                fname = "outputs/{}/{}_tutorial_config.json".format(uuid, gid)
            else:
                fname = "outputs/{}/{}_config.json".format(uuid, gid)
            with open(fname, "w") as f:
                dataJSON = json.dumps(request.json, separators=(',', ':'))
                f.write(dataJSON+"\n")
                print("Wrote to ", fname)

            if tutorial:
                fname ="outputs/{}/{}_tutorial_data.json".format(uuid, gid)
            else:
                fname ="outputs/{}/{}_data.json".format(uuid, gid)
            with open(fname, "w") as f:
                f.write("")
                print("Wrote to ", fname)

            return json.dumps(
                {'status': 'success', 'msg': 'saved'})

        # Called when the tutorial is completed
        @app.route('/get_room_connection_graph')
        def get_room_connection_graph():
            return render_template('getRoomConnectionGraph.html')

        @app.route('/get_room_connection_graph_finished', methods=['POST'])
        def get_room_connection_graph_finished():
            fname = "assets/map_distances.json"
            with open(fname, "w") as f:
                dataJSON = json.dumps(request.json)#, separators=(',', ':'))
                f.write(dataJSON+"\n")
                print("Wrote to ", fname)

            return json.dumps(
                {'status': 'success', 'msg': 'saved'})

        # Called to access files in the assets folder
        @app.route('/assets/<source>', methods=['GET'])
        def get_file(source):
            return _check_and_send_file(source, "assets")

        # Called to access files in the assets folder
        @app.route('/assets/tasks/<source>', methods=['GET'])
        def get_task_file(source):
            return _check_and_send_file(source, "assets/tasks")

        app.debug = False
        app.run(host='0.0.0.0', port=8194, threaded=True)


if __name__ == '__main__':
    minUUID = 100

    if os.path.isfile(completedGIDsFilename):
        with open(completedGIDsFilename, "r") as f:
            completedGameIDs = json.load(f)
    else:
        completedGameIDs = {str(gid) : [] for gid in range(numGIDs)}
    print("completedGameIDs", completedGameIDs)

    if os.path.isfile(completionCodesToUUIDFilename):
        with open(completionCodesToUUIDFilename, "rb") as f:
            completionCodes = pickle.load(f)
    else:
        completionCodes = {}
    print("completionCodes", completionCodes)

    server = FlaskExample()

    server.run()
