import cv2
import os
import time
import config 
output_dir = 'training'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)
username = "admin"
password = "EGIBWC"
camera_ip = config.CAM_IP
port = "554"
rtsp_url = f"rtsp://{username}:{password}@{camera_ip}:{port}/h264_stream"
cap = cv2.VideoCapture(rtsp_url)
if not cap.isOpened():
    print("Cannot open camera")
    exit()
capture_interval = 2  
frame_count = 0 
resize_width, resize_height = 640, 360  
last_frame = None

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Cannot read frame...")
            break

        frame = cv2.resize(frame, (resize_width, resize_height))
        if last_frame is not None:
            diff = cv2.absdiff(last_frame, frame)
            non_zero_count = cv2.countNonZero(cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY))
            if non_zero_count < 1000:  
                continue
        last_frame = frame.copy()
        frame_count += 1
        img_path = os.path.join(output_dir, f'{frame_count:04d}.jpg')
        cv2.imwrite(img_path, frame)
        print(f"Saved {img_path}")

        cv2.imshow('frame', frame)
        if cv2.waitKey(1) == ord('q'):
            break
        time.sleep(capture_interval)

finally:
    cap.release()
    cv2.destroyAllWindows()
