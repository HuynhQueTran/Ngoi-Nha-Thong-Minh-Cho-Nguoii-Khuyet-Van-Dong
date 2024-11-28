import cv2
import mediapipe as mp
import numpy as np
import pygame
from PIL import Image, ImageDraw, ImageFont
import os
import time
from cvzone.HandTrackingModule import HandDetector
from ultralytics import YOLO
import math
import telebot
import config
import threading
import csv
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()
bot_token = '7837480809:AAH538Eptco2p08H_j0C_M-_86mO_teXLsM'
bot = telebot.TeleBot(bot_token)
chat_id = '-1002384540377'
fire_detected_threshold = 80
start_time = None
alert_played = False

class FallDetectionApp:

    def __init__(self):
        pygame.mixer.init()
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose()
        self.mp_drawing = mp.solutions.drawing_utils
        self.detector = HandDetector(detectionCon=0.7, maxHands=1)
        self.model_fire = YOLO('fire.pt')
        self.esp_ip = config.ESP_IP
        username = "admin"
        password = "EGIBWC"
        camera_ip = config.CAM_IP
        port = "554"
        rtsp_url = f"rtsp://{username}:{password}@{camera_ip}:{port}/h264_stream"
        self.cap = cv2.VideoCapture(0)
        self.camera_running = True
        self.frame_count = 0
        self.frame_interval = 5 
        self.safety_zones = self.load_safety_zones('safety_zones.txt')
        self.fire_detected_time = None
        self.fire_alerted = False
        self.finger_control_active = True
        self.photo_dir = "fall_detected_photos"
        if not os.path.exists(self.photo_dir):
            os.makedirs(self.photo_dir)
        self.alert_log_file = "alert_log.csv"  
        self.initialize_alert_log()


    def save_image(self, frame, issue):
        filename = f"{self.photo_dir}/{issue}_{time.strftime('%Y%m%d_%H%M%S')}.jpg"
        cv2.imwrite(filename, frame)
        return filename

    def send_image_to_telegram(self, image_path):
        def send_alert():
            with open(image_path, 'rb') as photo:
                bot.send_photo(chat_id, photo)
        threading.Thread(target=send_alert).start()

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
    def initialize_alert_log(self):
        if not os.path.exists(self.alert_log_file):
            with open(self.alert_log_file, mode='w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'alert_type', 'image_path']) 

    def log_alert(self, alert_type, image_path):
        with open(self.alert_log_file, mode='a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([time.strftime('%Y-%m-%d %H:%M:%S'), alert_type, image_path])
    def gen_frames(self):
        while True:
            if not self.camera_running:
                continue
            ret, frame = self.cap.read()
            if not ret:
                continue
            frame = cv2.resize(frame, (700, 480)) 

            self.frame_count += 1
            if self.frame_count % self.frame_interval == 0:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                result = self.pose.process(frame_rgb)
                for zone in self.safety_zones:
                    cv2.rectangle(frame, (zone[0], zone[1]), (zone[2], zone[3]), (255, 255, 0), 2)

                fire_detected = False
                fire_result = self.model_fire(frame)
                for info in fire_result:
                    boxes = info.boxes
                    for box in boxes:
                        confidence = box.conf[0]
                        confidence = math.ceil(confidence * 100)
                        if confidence > 50:
                            x1, y1, x2, y2 = box.xyxy[0]
                            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 5)
                            cv2.putText(frame, f'fire {confidence}%', (x1 + 8, y1 + 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
                            fire_detected = True

                if fire_detected and confidence >= fire_detected_threshold:
                    pygame.mixer.Sound("fire.wav").play()
                    image_path = self.save_image(frame, "fire_detected")
                    self.send_image_to_telegram(image_path)

                if result.pose_landmarks:
                    self.mp_drawing.draw_landmarks(frame, result.pose_landmarks, self.mp_pose.POSE_CONNECTIONS)
                    landmarks = result.pose_landmarks.landmark

                    head = [landmarks[self.mp_pose.PoseLandmark.NOSE].x, landmarks[self.mp_pose.PoseLandmark.NOSE].y]
                    nose_x = int(head[0] * frame.shape[1])
                    nose_y = int(head[1] * frame.shape[0])
                    in_safe_zone, safety_status = self.check_safety(nose_x, nose_y)

                    frame = self.put_text(frame, safety_status, (10, 30), font_size=30, color=(0, 255, 0) if in_safe_zone else (0, 0, 255))
                    cv2.circle(frame, (nose_x, nose_y), 10, (0, 255, 0) if in_safe_zone else (0, 0, 255), -1)

                    if abs(landmarks[self.mp_pose.PoseLandmark.LEFT_HIP].y - landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER].y) < 0.2 and head[1] > landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER].y:
                        if not in_safe_zone:
                            cv2.putText(frame, "Fall Detected!", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                            pygame.mixer.Sound("fall_sound.wav").play()
                            image_path = self.save_image(frame, "fall_detected")
                            self.send_image_to_telegram(image_path)

                else:
                    frame = self.put_text(frame, "No person detected!", (50, 50), font_size=30, color=(0, 0, 255))
                cv2.imshow('Fall Detection', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        self.cap.release()
        cv2.destroyAllWindows()
if __name__ == "__main__":
    app = FallDetectionApp()
    app.gen_frames()
