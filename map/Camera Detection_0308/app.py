from flask import Response, Flask, render_template
import threading
import argparse 
import datetime, time
import imutils
import cv2
import flask
from urllib.request import Request, urlopen
from urllib.parse import urlencode, quote_plus, quote
import json


outputFrame = None
lock = threading.Lock()
 
app = Flask(__name__)
 
source =  'rtsp://183.107.31.51:556/'
cap = cv2.VideoCapture(source)
time.sleep(2.0)

@app.route("/")
def index():
    # return the rendered template
    return render_template("map.html")

def stream(frameCount):
    global outputFrame, lock
    if cap.isOpened():
        # cv2.namedWindow(('IP camera DEMO'), cv2.WINDOW_AUTOSIZE)
        while True:
            ret_val, frame = cap.read()
            if frame.shape:
                frame = cv2.resize(frame, (640,360))
                with lock:
                    outputFrame = frame.copy()
            else:
                continue 
    else:
        print('camera open failed')

def generate():
    global outputFrame, lock
 
    while True:
        with lock:
            if outputFrame is None:
                continue
 
            (flag, encodedImage) = cv2.imencode(".jpg", outputFrame)
 
            if not flag:
                continue
 
        yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + 
            bytearray(encodedImage) + b'\r\n')

@app.route("/video_feed")
def video_feed():
    return Response(generate(),
        mimetype = "multipart/x-mixed-replace; boundary=frame")


@app.route('/get_addr_point', methods=['POST'])
def get_addr_point():
    addr = flask.request.form['addr']

    vworld_apikey = '67C81659-E626-3F10-AF38-6F9888C57651'
    url = "http://api.vworld.kr/req/address?service=address&request=getCoord&type=ROAD&refine=false&key=%s&" % (
        vworld_apikey) + urlencode({quote_plus('address'): addr}, encoding='UTF-8')

    request = Request(url)
    response = urlopen(request)
    rescode = response.getcode()
    if rescode == 200:
        response_body = response.read().decode('utf-8')
    else:
        print('error code:', rescode)

    jsonData = json.loads(response_body)
    lat = float(jsonData['response']['result']['point']['y'])
    lng = float(jsonData['response']['result']['point']['x'])
    # print('lat:{}, lng:{}'.format(lat, lng))
    result = {'lat': lat,'lng': lng,'success': True}

    return result



@app.route('/vworld')
def vword():
    return render_template('vworld.html')

@app.route('/sample_marker')
def sample_marker():
    return render_template('sample_marker.html')

@app.route('/sample_marker_3d')
def sample_marker_3d():
    return render_template('sample_marker_3d.html')


@app.route('/map')
def map():
    return render_template('map.html'|'sample_marker_3d.html')


if __name__ == '__main__':
    print(__name__)
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--ip", type=str, required=False, default='192.168.0.70',
        help="ip address of the device")
    ap.add_argument("-o", "--port", type=int, required=False, default=5000, 
        help="ephemeral port number of the server (1024 to 65535)")
    ap.add_argument("-f", "--frame-count", type=int, default=32,
        help="# of frames used to construct the background model")
    args = vars(ap.parse_args())

    t = threading.Thread(target=stream, args=(args["frame_count"],))
    t.daemon = True
    t.start()
 
    app.run(host=args["ip"], port=args["port"], debug=True,
        threaded=True, use_reloader=False)
 
cap.release()
cv2.destroyAllWindows()