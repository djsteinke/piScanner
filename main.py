from flask import Flask, render_template, Response, jsonify, request
from time import sleep
import json
from accessories.camera import camera, get_jpg_buffer, get_full_jpg_buffer
from configuration.configuration import ScannerConfiguration
from scan import Scan

app = Flask(__name__)


def gen_frames():
    camera.set_focus_mm(scanner_config.camera.cz)
    while True:
        try:
            buffer = get_jpg_buffer(scanner_config.camera.cx, scanner_config.camera.cy)
            frame = buffer.tobytes()
            yield(b'--frame\r\n'
                  b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        except:
            sleep(1)
            yield b''


def gen_full_frames():
    while True:
        try:
            buffer = get_full_jpg_buffer(scanner_config.camera.cx, scanner_config.camera.cy)
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


@app.route('/scan', methods=['POST', 'GET'])
def scan_frame():
    if request.method == 'POST':
        color = request.form['color'] == 'on' if 'color' in request.form else False
        left_laser = request.form['left_laser'] == 'on' if 'left_laser' in request.form else False
        right_laser = request.form['right_laser'] == 'on' if 'right_laser' in request.form else False
        left_laser_val = int(request.form['left_laser_val']) if 'left_laser_val' in request.form else 0
        right_laser_val = int(request.form['right_laser_val']) if 'right_laser_val' in request.form else 0
        deg_per_stp = int(request.form['deg_per_step']) if 'deg_per_step' in request.form else 10
        degrees = int(request.form['deg_total']) if 'deg_total' in request.form else 360

        scan = Scan(scanner_config, camera, right_laser, left_laser, color, deg_per_stp, degrees)
        scan.start()

    return render_template('scan.html', config=scanner_config)


@app.route('/setup', methods=['POST', 'GET'])
def setup_frame():
    error = None
    if request.method == 'POST':
        scanner_config.camera.f = float(request.form['input_f_mm'])
        #scanner_config.camera.fx = float(request.form['input_f_mm'])
        #scanner_config.camera.fy = float(request.form['input_f_mm'])
        scanner_config.camera.cx = float(request.form['input_cx'])
        scanner_config.camera.cy = float(request.form['input_cy'])
        scanner_config.camera.cz = int(request.form['input_cz'])
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


@app.route('/video_feed_full')
def video_feed_full():
    return Response(gen_full_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/load_setup', methods=["GET"])
def setup_load_setup():
    return jsonify(message=json.dumps({}), statusCode=200), 200


@app.route('/run_calibration', methods=["GET", "POST"])
def run_calibration():
    scanner_config.camera.run_calibration()
    scanner_config.save()
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

