from flask import Flask, render_template, Response, jsonify, request
from time import sleep
import json
from accessories.camera import camera, get_jpg_buffer
from configuration.configuration import ScannerConfiguration
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


@app.route('/setup', methods=['POST', 'GET'])
def setup_frame():
    error = None
    if request.method == 'POST':
        scanner_config.camera.f = request.form['input_f_px']
        scanner_config.camera.f_mm = float(request.form['input_f_mm'])
        scanner_config.camera.cx = int(request.form['input_cx'])
        scanner_config.camera.cy = int(request.form['input_cy'])
        scanner_config.camera.cz = float(request.form['input_cz'])
        scanner_config.right_laser.pin = int(request.form['input_right_pin'])
        scanner_config.right_laser.angle = float(request.form['input_right_angle'])
        scanner_config.left_laser.pin = int(request.form['input_left_pin'])
        scanner_config.left_laser.angle = float(request.form['input_left_angle'])
        scanner_config.camera.grid_size = float(request.form['input_block_size'])
        scanner_config.camera.nx = int(request.form['input_x_cnt'])
        scanner_config.camera.ny = int(request.form['input_y_cnt'])
        scanner_config.stepper_motor.micro_steps = int(request.form['input_micro_steps'])
        scanner_config.stepper_motor.step_size = float(request.form['input_step_size'])
        scanner_config.stepper_motor.enable_pin = int(request.form['input_enable'])
        scanner_config.stepper_motor.dir_pin = int(request.form['input_direction'])
        scanner_config.stepper_motor.pulse_pin = int(request.form['input_pulse'])
        scanner_config.save()

    return render_template('setup.html', config=scanner_config, error=error)


@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/load_setup', methods=["GET"])
def setup_load_setup():
    return jsonify(message=json.dumps({}), statusCode=200), 200


@app.route('/run_calibration', methods=["GET", "POST"])
def run_calibration():
    #scanner_config.camera.run_calibration(stepper)
    return jsonify(message=scanner_config.camera.calibration_values(), statusCode=200), 200


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
    scanner_config = ScannerConfiguration.load()
    camera.start()
    app.run(debug=False, host="192.168.0.154", port=3100)

