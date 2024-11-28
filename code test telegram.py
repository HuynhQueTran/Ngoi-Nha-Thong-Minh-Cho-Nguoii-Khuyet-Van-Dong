from flask import Flask, Response, render_template, request, jsonify
import cv2
import mediapipe as mp
import numpy as np
import pygame
from fer import FER
from PIL import Image, ImageDraw, ImageFont
import os
import requests
from cvzone.HandTrackingModule import HandDetector
from ultralytics import YOLO
import math
import time
import telebot
import threading

bot_token = '7837480809:AAH538Eptco2p08H_j0C_M-_86mO_teXLsM'
bot = telebot.TeleBot(bot_token)
live_stream_url = 'http://192.168.137.237:5000/'
chat_id = '-1002384540377'
fire_detected_threshold = 80
start_time = None
alert_played = False
app = Flask(__name__)

class FallDetectionApp:

    def __init__(self):
        pygame.mixer.init()
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose()
        self.mp_drawing = mp.solutions.drawing_utils
        self.emotion_detector = FER()
        self.detector = HandDetector(detectionCon=0.8, maxHands=1)
        self.model_fire = YOLO('fire.pt')
        self.esp_ip = 'http://192.168.137.16'
        self.cap = cv2.VideoCapture(9)
        self.camera_running = True
        self.frame_count = 0
        self.frame_interval = 1
        self.drawing = False
        self.start_point = None
        self.end_point = None
        self.safety_zones = self.load_safety_zones('safety_zones.txt')
        self.fire_detected_time = None
        self.fire_alerted = False
        self.finger_control_active = True
        self.photo_dir = "fall_detected_photos"
        if not os.path.exists(self.photo_dir):
            os.makedirs(self.photo_dir)

    def save_image(self, frame, issue):
        filename = f"{self.photo_dir}/{issue}_{time.strftime('%Y%m%d_%H%M%S')}.jpg"
        cv2.imwrite(filename, frame)
        return filename

    def send_image_to_telegram(self, image_path):
        with open(image_path, 'rb') as photo:
            bot.send_photo(chat_id, photo)

    def load_safety_zones(self, filename):
        if not os.path.exists(filename):
            return []

        zones = []
        with open(filename, 'r') as f:
            for line in f:
                x1, y1, x2, y2 = map(int, line.strip().split(','))
                zones.append((x1, y1, x2, y2))

        return zones

    def check_safety(self, x, y):
        if not self.safety_zones:
            return False, "Chưa đặt khung an toàn"

        for box in self.safety_zones:
            x1, y1, x2, y2 = box
            if x1 <= x <= x2 and y1 <= y <= y2:
                return True, "An toàn"

        return False, "Nguy hiểm: Có nguy cơ rơi khỏi giường!"

    def put_text(self, img, text, position, font_size=30, color=(255, 255, 255)):
        pil_img = Image.fromarray(img)
        draw = ImageDraw.Draw(pil_img)
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except IOError:
            font = ImageFont.load_default()
        draw.text(position, text, font=font, fill=color)
        return np.array(pil_img)

    def save_safety_zones(self, filename, zones):
        with open(filename, 'w') as f:
            for zone in zones:
                f.write(f"{zone[0]},{zone[1]},{zone[2]},{zone[3]}\n")

    def led_control(self, fingerUp, fire_detected):
        if self.finger_control_active:
            if fingerUp == [0, 1, 0, 0, 0]:
                requests.get(f"{self.esp_ip}/led1/on")
                requests.get(f"{self.esp_ip}/led2/off")
            elif fingerUp == [0, 1, 1, 0, 0]:
                requests.get(f"{self.esp_ip}/led1/off")
                requests.get(f"{self.esp_ip}/led2/on")
            elif fingerUp == [0, 1, 1, 1, 0]:
                requests.get(f"{self.esp_ip}/led1/on")
                requests.get(f"{self.esp_ip}/led2/on")
            elif fingerUp == [0, 1, 1, 1, 1]:
                requests.get(f"{self.esp_ip}/led1/off")
                requests.get(f"{self.esp_ip}/led2/off")
            elif fingerUp == [1, 0, 0, 0, 0]:
                requests.get(f"{self.esp_ip}/led3/on")
            elif fingerUp == [0, 0, 1, 1, 0]:
                requests.get(f"{self.esp_ip}/led3/off")
        else:
            if fingerUp == [1, 1, 0, 0, 1]:
                pass

    def move_servo(self, angle):
        requests.get(f"{self.esp_ip}/servo?angle={angle}")

    def gen_frames(self):
        while True:
            if not self.camera_running:
                continue

            ret, frame = self.cap.read()
            if ret:
                self.frame_count += 1
                if self.frame_count % self.frame_interval == 0:
                    small_frame = cv2.resize(frame, (640, 480))
                    frame_rgb = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
                    result = self.pose.process(frame_rgb)

                    fall_detected = False

                    # Draw safety zones
                    for zone in self.safety_zones:
                        cv2.rectangle(frame, (zone[0], zone[1]), (zone[2], zone[3]), (255, 255, 0), 2)

                    hands, img = self.detector.findHands(frame)
                    if hands:
                        lmList = hands[0]
                        fingerUp = self.detector.fingersUp(lmList)
                        self.led_control(fingerUp, self.fire_detected_time is not None)
                        cv2.putText(frame, f'Finger count: {sum(fingerUp)}', (20, 460),
                                    cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 1, cv2.LINE_AA)
                        if fingerUp == [1, 1, 1, 0, 0]:
                            self.move_servo(0)
                        elif fingerUp == [1, 0, 0, 0, 1]:
                            self.move_servo(180)

                    # Detect fire
                    fire_detected = False
                    fire_result = self.model_fire(frame)
                    for info in fire_result:
                        boxes = info.boxes
                        for box in boxes:
                            confidence = box.conf[0]
                            confidence = math.ceil(confidence * 100)
                            if confidence > fire_detected_threshold:
                                x1, y1, x2, y2 = box.xyxy[0]
                                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 5)
                                cv2.putText(frame, f'Fire {confidence}%', (x1 + 8, y1 + 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
                                fire_detected = True

                    if fire_detected and confidence >= fire_detected_threshold:
                        pygame.mixer.Sound("fire.wav").play()
                        image_path = self.save_image(frame, "fire_detected")
                        self.send_image_to_telegram(image_path)

                    if result.pose_landmarks:
                        self.mp_drawing.draw_landmarks(frame, result.pose_landmarks, self.mp_pose.POSE_CONNECTIONS)
                        landmarks = result.pose_landmarks.landmark

                        shoulder_left = [landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER].x, landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER].y]
                        shoulder_right = [landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER].x, landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER].y]
                        hip_left = [landmarks[self.mp_pose.PoseLandmark.LEFT_HIP].x, landmarks[self.mp_pose.PoseLandmark.LEFT_HIP].y]
                        hip_right = [landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP].x, landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP].y]
                        head = [landmarks[self.mp_pose.PoseLandmark.NOSE].x, landmarks[self.mp_pose.PoseLandmark.NOSE].y]
                        nose_x = int(head[0] * frame.shape[1])
                        nose_y = int(head[1] * frame.shape[0])
                        shoulder_left_x = int(shoulder_left[0] * frame.shape[1])
                        shoulder_right_x = int(shoulder_right[0] * frame.shape[1])
                        shoulder_y = int((shoulder_left[1] + shoulder_right[1]) / 2 * frame.shape[0])
                        hip_left_x = int(hip_left[0] * frame.shape[1])
                        hip_right_x = int(hip_right[0] * frame.shape[1])
                        hip_y = int((hip_left[1] + hip_right[1]) / 2 * frame.shape[0])

                        # Calculate angles and detect fall
                        shoulder_angle = math.atan2(shoulder_y - nose_y, shoulder_right_x - shoulder_left_x) * 180 / math.pi
                        hip_angle = math.atan2(hip_y - nose_y, hip_right_x - hip_left_x) * 180 / math.pi

                        # Adjusting the thresholds for stability
                        if abs(shoulder_angle) > 70 or abs(hip_angle) > 70:
                            fall_detected = True

                        if fall_detected:
                            self.drawing = True
                            if not alert_played:
                                pygame.mixer.Sound("fall.wav").play()
                                alert_played = True
                            image_path = self.save_image(frame, "fall_detected")
                            self.send_image_to_telegram(image_path)
                        else:
                            alert_played = False

                        # Safety zone check
                        safe, status = self.check_safety(shoulder_left_x, shoulder_y)
                        cv2.putText(frame, status, (20, 430), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)

                    ret, buffer = cv2.imencode('.jpg', frame)
                    frame = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    def start_camera(self):
        self.camera_running = True
        self.gen_frames()

    def stop_camera(self):
        self.camera_running = False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(FallDetectionApp().gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
