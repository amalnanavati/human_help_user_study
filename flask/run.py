#!/usr/bin/env python3

import os
import json

from flask import Flask, render_template, send_file, request

from flask_cors import CORS
app = Flask(__name__)
CORS(app, resources={r"*": {"origins": "*"}})

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

        # The landing page for user with uid
        @app.route('/index/<uuid>')
        def index(uuid):
            return render_template('index.html', uuid=uuid)

        # Called when the consent form is submitted
        @app.route('/consent', methods=['POST'])
        def consent():
            agree = request.form['agree']
            if (agree != "agree"): # should not reach here due to javascript logic at the consent form
                return "Please go back and agree to the consent form to proceed"

            uuid = request.form['uuid']

            # The demographic questionairre
            return render_template('demography.html', uuid=uuid)

        # Called when the demography questionairre is submitted
        # TODO: make this make another post request for game so game has a proper URL
        @app.route('/demography', methods=['POST'])
        def demography():
            # age = request.form['age']
            # gender = request.form['gender']
            data = dict(request.form)

            uuid = request.form['uuid']
            dirname = "outputs/{}".format(uuid)
            if not os.path.exists(dirname):
                os.makedirs(dirname)

            fname ="outputs/{}/demography.json".format(uuid)
            with open(fname, "w") as f:
                json.dump(data, f)
                print("Wrote to ", fname)

            return render_template('game.html', uuid=uuid, gid=0)

        # Called load_game_state
        @app.route('/load_game_<uuid>_<gid>')
        def load_game(uuid, gid):
            dataToLoad = []
            fname ="outputs/{}/{}_data.json".format(uuid, gid)
            with open(fname, "r") as f:
                for cnt, line in enumerate(f):
                    if len(line.strip()) == 0:
                        break
                    dataToLoad.append(json.loads(line))
            return render_template('game.html', uuid=uuid, gid=gid, load="true", dataToLoad=dataToLoad)


        # Called to log the game state
        @app.route('/log_game_state', methods=['POST'])
        def log_game_state():
            data = dict(request.form)

            uuid = request.form['uuid']
            gid = request.form['gid']

            dirname = "outputs/{}".format(uuid)
            if not os.path.exists(dirname):
                os.makedirs(dirname)

            fname ="outputs/{}/{}_data.json".format(uuid, gid)
            with open(fname, "a") as f:
                dataJSON = json.dumps(data, separators=(',', ':'))
                f.write(dataJSON+"\n")
                print("Wrote to ", fname)

            return json.dumps(
                {'status': 'success', 'msg': 'saved'})

        # Called to log the game config
        @app.route('/log_game_config', methods=['POST'])
        def log_game_config():
            data = dict(request.form)

            uuid = request.form['uuid']
            gid = request.form['gid']

            dirname = "outputs/{}".format(uuid)
            if not os.path.exists(dirname):
                os.makedirs(dirname)

            fname ="outputs/{}/{}_config.json".format(uuid, gid)
            with open(fname, "w") as f:
                dataJSON = json.dumps(data, separators=(',', ':'))
                f.write(dataJSON+"\n")
                print("Wrote to ", fname)
            fname ="outputs/{}/{}_data.json".format(uuid, gid)
            with open(fname, "w") as f:
                f.write("")
                print("Wrote to ", fname)

            return json.dumps(
                {'status': 'success', 'msg': 'saved'})

        # Called to access files in the assets folder
        @app.route('/assets/<source>', methods=['GET'])
        def get_file(source):
            return _check_and_send_file(source, "assets")

        app.debug = False
        app.run(host='0.0.0.0', port=8193, threaded=True)


if __name__ == '__main__':

    server = FlaskExample()

    server.run()
