import cv2
import mediapipe as mp
import time
import subprocess
import os
import signal
import config
import math
import requests
import matplotlib.pyplot as plt
import telebot
from head_position import HeadPosition

# Cấu hình thông tin camera và Telegram bot
username = "admin"
password = "EGIBWC"
camera_ip = config.CAM_IP
port = "554"
rtsp_url = f"rtsp://{username}:{password}@{camera_ip}:{port}/h264_stream"
bot_token = '7837480809:AAH538Eptco2p08H_j0C_M-_86mO_teXLsM'
chat_id = '-1002384540377'

# Khởi tạo các đối tượng
mp_face_detection = mp.solutions.face_detection
mp_pose = mp.solutions.pose
face_detection = mp_face_detection.FaceDetection(min_detection_confidence=0.2)
pose = mp_pose.Pose()
last_eye_open_time = time.time()
no_motion_time = time.time() 
eye_closed_duration = 0 
no_motion_duration = 0 
motion_threshold = 1 
eye_closed_threshold = 5  
sleep_process = None

# Khởi tạo đối tượng HeadPosition
hp = HeadPosition()
classes = ["Trái", "Phải", "Chính diện", "Ngửa đầu"]
head_position = [0, 0, 0, 0]
head_distance_movement = []
total_frames = 0
center_prev = (0, 0)
frame_counter = 0
frame_interval = 10

# Mở camera RTSP
cap = cv2.VideoCapture(rtsp_url)

# Hàm kiểm tra mắt nhắm
def is_eye_closed(eye):
    eye_area = (eye.x - eye.y)
    return eye_area < 0.02 

# Hàm kiểm tra trạng thái ngủ
def check_sleep_status(eye_closed_duration, no_motion_duration):
    if eye_closed_duration > eye_closed_threshold and no_motion_duration > motion_threshold:
        return "Ngủ"
    else:
        return "Thức"

# Vòng lặp chính
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Kiểm tra khuôn mặt và mắt
    face_results = face_detection.process(rgb_frame)
    pose_results = pose.process(rgb_frame)

    if face_results.detections:
        for detection in face_results.detections:
            bboxC = detection.location_data.relative_keypoints
            left_eye = bboxC[1]  
            right_eye = bboxC[2]  

            if is_eye_closed(left_eye) and is_eye_closed(right_eye):
                eye_closed_duration = time.time() - last_eye_open_time  
            else:
                last_eye_open_time = time.time() 

    # Kiểm tra tư thế và chuyển động đầu
    if pose_results.pose_landmarks:
        last_motion_time = time.time()
        no_motion_duration = time.time() - no_motion_time
    else:
        no_motion_time = time.time()

    # Kiểm tra trạng thái ngủ
    sleep_status = check_sleep_status(eye_closed_duration, no_motion_duration)
    cv2.putText(frame, f"Trang Thai: {sleep_status}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    # Nếu trạng thái là ngủ, mở chương trình goodjobsleep.py
    if sleep_status == "Ngủ" and sleep_process is None:
        print("Người dùng đang ngủ. Mở tệp goodjobsleep.py.")
        sleep_process = subprocess.Popen(["python", "/mnt/mydisk/RUN/goodjobsleep.py"])

    # Nếu trạng thái là thức, đóng chương trình goodjobsleep.py
    if sleep_status == "Thức" and sleep_process is not None:
        print("Người dùng thức. Đóng tệp goodjobsleep.py.")
        sleep_process.terminate()  # Dừng tiến trình an toàn
        sleep_process = None

    # Phân tích tư thế đầu và chuyển động đầu
    ret, class_id, box, center = hp.get_head_position(frame)
    if ret:
        x, y, w, h = box
        cv2.putText(frame, classes[class_id], (x, y - 15), 0, 1.3, hp.colors[class_id], 3)
        cv2.rectangle(frame, (x, y), (x + w, y + h), hp.colors[class_id], 3)
        cv2.circle(frame, center, 5, hp.colors[class_id], 3)
        head_position[class_id] += 1
        total_frames += 1

        # Tính khoảng cách chuyển động đầu
        x, y = center
        distance = math.hypot(x - center_prev[0], y - center_prev[1])
        head_distance_movement.append(distance)
        center_prev = center

    # Hiển thị khung hình
    frame_counter += 1
    if frame_counter % frame_interval == 0:
        cv2.imshow("Khung hình", frame)

    # Xử lý khi nhấn ESC
    key = cv2.waitKey(1)
    if key == 27:  # ESC key
        print("ESC được nhấn. Đóng chương trình.")
        # Gửi thông báo qua Telegram
        message = "Chương trình giám sát giấc ngủ đã bị đóng thủ công."
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message
        }
        response = requests.post(url, data=payload)

        if response.status_code == 200:
            print("Thông điệp thông báo đã được gửi qua Telegram.")
        else:
            print("Gửi thông điệp thất bại.")
        break

# Giải phóng tài nguyên
cap.release()
hp.release()
cv2.destroyAllWindows()
