import cv2
from deepface import DeepFace
import config

username = "admin"
password = "EGIBWC"
camera_ip = config.CAM_IP
port = "554"
rtsp_url = f"rtsp://{username}:{password}@{camera_ip}:{port}/h264_stream"

# Tải mô hình Haar Cascade cho phát hiện khuôn mặt
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

cap = cv2.VideoCapture(rtsp_url)

if not cap.isOpened():
    print("Không thể mở camera")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        print("Không thể nhận diện hình ảnh")
        break

    # Giảm kích thước khung hình để tăng tốc
    frame = cv2.resize(frame, (640, 360))
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Phát hiện khuôn mặt
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(50, 50))

    for (x, y, w, h) in faces:
        face_roi = frame[y:y+h, x:x+w]

        try:
            # Phân tích cảm xúc chỉ trên khuôn mặt
            result = DeepFace.analyze(face_roi, actions=['emotion'], enforce_detection=False)

            if isinstance(result, list):
                result = result[0]

            dominant_emotion = result['dominant_emotion']
            emotions = result['emotion']

            # Hiển thị cảm xúc chính trên khung hình
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(frame, f"{dominant_emotion}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        except Exception as e:
            print("Lỗi phân tích cảm xúc:", e)

    # Hiển thị video
    cv2.imshow("Emotion Detection", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
