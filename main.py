
from flask import Flask, render_template, Response, jsonify, request
from time import sleep
import json
import accessories.camera as camera


app = Flask(__name__)


def gen_frames():
    camera.set_config('preview')
    while True:
        try:
            buffer = camera.get_jpg_buffer()
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

