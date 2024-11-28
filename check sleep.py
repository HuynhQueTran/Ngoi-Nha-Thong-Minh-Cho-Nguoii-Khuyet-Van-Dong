import cv2
import mediapipe as mp
import time
import subprocess
import os
import signal
import config
mp_face_detection = mp.solutions.face_detection
mp_pose = mp.solutions.pose
face_detection = mp_face_detection.FaceDetection(min_detection_confidence=0.2)
pose = mp_pose.Pose()
last_eye_open_time = time.time()
no_motion_time = time.time()
eye_closed_duration = 0
no_motion_duration = 0
motion_threshold = 0
eye_closed_threshold = 3
def is_eye_closed(eye):
   eye_area = (eye.x - eye.y)
   return eye_area < 0.01
def check_sleep_status(eye_closed_duration, no_motion_duration):
   if eye_closed_duration > eye_closed_threshold and no_motion_duration > motion_threshold:
       return "sleep"
   else:
       return "no sleep"
username = "admin"
password = "EGIBWC"
camera_ip = config.CAM_IP
port = "554"
rtsp_url = f"rtsp://{username}:{password}@{camera_ip}:{port}/h264_stream"


cap = cv2.VideoCapture(rtsp_url)
sleep_process = None




while cap.isOpened():
   ret, frame = cap.read()
   if not ret:
       break
   rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)


   frame = cv2.resize(frame, (640, 360))
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


   if pose_results.pose_landmarks:
       last_motion_time = time.time()
       no_motion_duration = time.time() - no_motion_time - 1
   else:
       no_motion_time = time.time()
   sleep_status = check_sleep_status(eye_closed_duration, no_motion_duration)
  
   cv2.putText(frame, f"Trang Thai: {sleep_status}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
   if sleep_status == "sleep" and sleep_process is None:
       print("Người dùng đang ngủ. Mở tệp goodjobsleep.py.")
       sleep_process = subprocess.Popen(["python", "goodjobslepp.py"])
   elif sleep_status == "no sleep":
            if sleep_process is not None:
                print("Người dùng thức. Đóng tệp goodjobsleep.py.")
                sleep_process.terminate()
   # Kiểm tra phím Esc để đóng tiến trình goodjobsleep.py
                key = cv2.waitKey(1) & 0xFF
                if key == 27:  # 27 là mã ASCII của phím Esc
                    if sleep_process is not None:
                        print("Đang đóng tệp goodjobsleep.py.")
                        sleep_process.terminate()  # Dừng tiến trình an toàn
                        sleep_process = None




   cv2.imshow("Eye and Motion Detection", frame)




   if cv2.waitKey(1) & 0xFF == ord('q'):
       break


cap.release()
cv2.destroyAllWindows()




