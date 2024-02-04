from flask import Flask, render_template, Response, jsonify, request
from time import sleep
import json
from accessories.camera import camera, get_jpg_buffer
import configuration.camera as camera_calibration
from accessories.stepper_motor import stepper

app = Flask(__name__)


def gen_frames():
    camera.set_focus_mm(350.0)
    camera.set_config('preview')
    while True:
        try:
            buffer = get_jpg_buffer(535, 964)
            frame = buffer.tobytes()
            yield(b'--frame\r\n'
                  b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        except:
            sleep(1)
            yield b''


class Test(object):
    def __init__(self):
        self.value = 'Some Value.'


@app.route('/test')
def test():
    t = Test()
    return render_template('test.html', test=t)


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
    return jsonify(message=json.dumps(camera_calibration.camera_configuration.configuration), statusCode=200), 200


@app.route('/save_setup', methods=["POST"])
def setup_save_click():
    content_type = request.headers.get('Content-Type')
    if content_type == 'application/json':
        setup = request.json
        camera_calibration.camera_configuration.configuration['f'] = setup['f']
        camera_calibration.camera_configuration.configuration['cx'] = setup['cx']
        camera_calibration.camera_configuration.configuration['cy'] = setup['cy']
        camera_calibration.camera_configuration.configuration['cz'] = setup['cz']
        camera_calibration.camera_configuration.configuration['f_mm'] = setup['f_mm']
        camera_calibration.camera_configuration.save_calibration()
        # save_file('setup.json', json.dumps(setup))
        return jsonify(message='Success', statusCode=200), 200
    else:
        return jsonify(message='Content-Type not supported!', statusCode=400), 400


@app.route('/run_calibration', methods=["GET"])
def run_calibration():
    camera_calibration.run_calibration(stepper)
    return jsonify(message=json.dumps(camera_calibration.camera_configuration.configuration), statusCode=200), 200


"""
@app.route('/static/<filename>')
def scripts(filename):
    f = open('static/' + filename, 'r')
    return f.read()
"""

def save_file(file_path, data):
    f = open(file_path, 'w')
    f.write(data)
    f.close()


def load_setup():
    try:
        f = open('setup.json', 'r')
        setup = json.load(f)
    except:
        pass


if __name__ == '__main__':
    camera.start()
    app.run(debug=False, host="192.168.0.154", port=3100)

