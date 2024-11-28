import cv2
import dlib
import time
face_detector = dlib.get_frontal_face_detector()
eye_detector = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")  # Tải mô hình 68 điểm trên khuôn mặt
def is_eye_closed(eye):
    A = dist(eye[1], eye[5])
    B = dist(eye[2], eye[4])
    C = dist(eye[0], eye[3])
    eye_ratio = (A + B) / (2.0 * C)
    return eye_ratio < 0.2 
def dist(p1, p2):
    return ((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2) ** 0.5
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_detector(gray)
    for face in faces:
        landmarks = eye_detector(gray, face)
        left_eye = [(landmarks.part(i).x, landmarks.part(i).y) for i in range(36, 42)]
        right_eye = [(landmarks.part(i).x, landmarks.part(i).y) for i in range(42, 48)]

        if is_eye_closed(left_eye) or is_eye_closed(right_eye):
            cv2.putText(frame, "Warning: You are falling asleep!", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            print("Warning: You are falling asleep!")
    cv2.imshow("Anti Sleep System", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
