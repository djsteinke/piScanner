from flask import Flask, render_template, Response, jsonify, request
from time import sleep
import json
import io

from helper import save_file, load_setup

app = Flask(__name__)
picam2 = None
setup = {}


def gen_frames():
    while True:
        sleep(1)
        frame = b''
        if picam2 is not None:
            data = io.BytesIO()
            picam2.capture_file(data, format='jpeg')
            data.seek(0)
            frame = data.read()
            data.truncate()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/setup')
def setup_frame():
    return render_template('setup.html')


@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/load_setup', methods=["GET"])
def setup_load_setup():
    return jsonify(message=json.dumps(setup), statusCode=200), 200


@app.route('/save_setup', methods=["POST"])
def setup_save_click():
    global setup
    content_type = request.headers.get('Content-Type')
    if content_type == 'application/json':
        setup = request.json
        save_file('setup.json', json.dumps(setup))
        return jsonify(message='Success', statusCode=200), 200
    else:
        return jsonify(message='Content-Type not supported!', statusCode=400), 400


@app.route('/scripts/<filename>')
def scripts(filename):
    f = open('scripts/' + filename, 'r')
    return f.read()


def start_app():
    global setup
    setup = load_setup()
    app.run(debug=True, host="192.168.0.154", port=31000)
