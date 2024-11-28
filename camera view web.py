from flask import Flask, render_template, Response, jsonify
import cv2
import config
app = Flask(__name__)

camera_ip = config.CAM_IP
port = "554"
username = "admin"
password = "EGIBWC"
camera_url = f"rtsp://{username}:{password}@{camera_ip}:{port}/stream1"

camera = None
is_camera_active = False

def get_video_stream():
    global camera
    camera = cv2.VideoCapture(camera_url)
    while camera.isOpened():
        ret, frame = camera.read()
        if not ret:
            break
        _, jpeg = cv2.imencode('.jpg', frame)
        frame = jpeg.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(get_video_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    return render_template('index3.html')

@app.route('/toggle_camera', methods=['POST'])
def toggle_camera():
    global is_camera_active, camera
    if is_camera_active:
        camera.release()
        is_camera_active = False
        return jsonify({'message': 'Camera stopped'})
    else:
        camera = cv2.VideoCapture(camera_url)
        is_camera_active = True
        return jsonify({'message': 'Camera started'})

@app.route('/send_alert', methods=['POST'])
def send_alert():
    return jsonify({'message': 'Alert sent'})

@app.route('/update_settings', methods=['POST'])
def update_settings():
    return jsonify({'message': 'Settings updated'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
