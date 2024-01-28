import picamera2
#from libcamera import controls
from time import sleep
from threading import Condition
from flask import Flask, Response
from flask_restful import Resource, Api
import io


app = Flask(__name__)
api = Api(app)

class Camera:
    def __init__(self):
        self.camera = picamera2.Picamera2()
        self.camera.configure(self.camera.create_video_configuration(main={"size": (640, 480)}))
        self.streamOut = StreamingOutput()
        self.camera.start()

    def get_frame(self):
        self.camera.start()
        with self.streamOut.condition:
            self.streamOut.condition.wait()
            self.frame = self.streamOut.frame
        return self.frame


class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()


# defines the function that generates our frames
camera = Camera()


def genFrames():
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')


# defines the route that will access the video feed and call the feed function
class VideoFeed(Resource):
    def get(self):
        return Response(genFrames(),
                        mimetype='multipart/x-mixed-replace; boundary=frame')


api.add_resource(VideoFeed, '/cam')

if __name__ == '__main__':

    app.run(debug=True, host="192.168.0.154", port=31000)


