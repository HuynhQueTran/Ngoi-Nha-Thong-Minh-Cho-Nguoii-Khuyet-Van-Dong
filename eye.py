import cv2
import mediapipe as mp
import time

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True)


def calculate_ear(landmarks, eye_points):
    eye = [landmarks[i] for i in eye_points]
    vertical_1 = ((eye[1].x - eye[5].x) ** 2 + (eye[1].y - eye[5].y) ** 2) ** 0.5
    vertical_2 = ((eye[2].x - eye[4].x) ** 2 + (eye[2].y - eye[4].y) ** 2) ** 0.5
    horizontal = ((eye[0].x - eye[3].x) ** 2 + (eye[0].y - eye[3].y) ** 2) ** 0.5
    return (vertical_1 + vertical_2) / (2.0 * horizontal)

LEFT_EYE = [362, 385, 387, 263, 373, 380]
RIGHT_EYE = [33, 160, 158, 133, 153, 144]
EAR_THRESHOLD = 0.2
blink_times = []
blink_flag = False

cap = cv2.VideoCapture(0)

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        print("Cannot read frame.")
        break

    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb_frame)

    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            left_ear = calculate_ear(face_landmarks.landmark, LEFT_EYE)
            right_ear = calculate_ear(face_landmarks.landmark, RIGHT_EYE)
            ear = (left_ear + right_ear) / 2.0
            if ear < EAR_THRESHOLD:
                if not blink_flag:
                    blink_flag = True
                    blink_times.append(time.time())
            else:
                blink_flag = False
            if len(blink_times) >= 3:
                if blink_times[-1] - blink_times[-3] <= 2:  # 2 seconds
                    cv2.putText(frame, "Warning: You blinked 3 times in a row!",
                                (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                    blink_times = []
            cv2.putText(frame, f"Blink Count: {len(blink_times)}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

    cv2.imshow('Eye Gesture Detection', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
