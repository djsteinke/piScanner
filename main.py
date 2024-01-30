from picamera2 import Picamera2, Preview
from flask import Flask, render_template, Response, jsonify, request
from time import sleep
import json
import cv2
import subprocess


subprocess.run(['v4l2-ctl', '--set-ctrl', 'wide_dynamic_range=1', '-d', '/dev/v4l-subdev0'])

app = Flask(__name__)


picam2 = Picamera2()
picam2.start_preview(Preview.NULL)
#capture_config_preview = picam2.create_still_configuration(main={"size": (640, 360), "format": "XBGR8888"}, display="main")
capture_config_preview = picam2.create_still_configuration(main={"size": (640, 360)}, display="main")
picam2.align_configuration(capture_config_preview)
#capture_config_preview = picam2.create_still_configuration(main={"size": (640, 360)}, lores={"size": (640, 360)}, display="main")
capture_config_save = picam2.create_still_configuration
picam2.configure(capture_config_preview)
picam2.start()

sleep(1)
picam2.set_controls({"AfMode": 0, "LensPosition": 3.333})
sleep(5)

def gen_frames():
    while True:
        try:
            im = picam2.capture_array()
            im = cv2.cvtColor(im, cv2.COLOR_RGB2BGR)
            im = cv2.rotate(im, cv2.ROTATE_90_CLOCKWISE)
            ret, buffer = cv2.imencode('.jpg', im)
            frame = buffer.tobytes()
            yield(b'--frame\r\n'
                  b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        except:
            sleep(1)
            yield b''


@app.route('/')
def index():
    #return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
    return render_template('index.html')

@app.route('/setup')
def setup_frame():
    return render_template('setup.html')


@app.route('/video_feed')
def video_feed():
    #start_picam2()
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


def save_file(file_path, data):
    f = open(file_path, 'w')
    f.write(data)
    f.close()

def load_setup():
    global setup
    try:
        f = open('setup.json', 'r')
        setup = json.load(f)
    except:
        pass


if __name__ == '__main__':
    setup = {}
    load_setup()
    app.run(debug=False, host="192.168.0.154", port=3100)

