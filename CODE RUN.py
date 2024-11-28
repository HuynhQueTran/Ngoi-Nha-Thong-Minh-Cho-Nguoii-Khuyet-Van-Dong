import pyfirmata
import cv2
from cvzone.HandTrackingModule import HandDetector
from ultralytics import YOLO
import math
import time


model_fire = YOLO('fire.pt')
model_person = YOLO('yolov10s.pt')

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
detector = HandDetector(detectionCon=0.8, maxHands=1)

video = cv2.VideoCapture(0)

classnames = ['fire']

prev_face_center_x = None
prev_face_center_y = None

comport='COM3'
board = pyfirmata.Arduino(comport)

led_1 = board.get_pin('d:8:o')
led_2 = board.get_pin('d:9:o')
led_3 = board.get_pin('d:10:o')
led_4 = board.get_pin('d:11:o')
led_5 = board.get_pin('d:12:o')
led_fire = board.get_pin('d:13:o')

pan_pin = 3
tilt_pin = 5
pan_servo = board.get_pin(f'd:{pan_pin}:s')
tilt_servo = board.get_pin(f'd:{tilt_pin}:s')
servo_4_pin = 7
servo_4 = board.get_pin(f'd:{servo_4_pin}:s')

prev_pan_angle = 90
prev_tilt_angle = 90
prev_servo_4_angle = 45
no_face_count = 0
max_no_face_count = 10

move_speed = 7

fire_detected_time = None 
fire_alarm_delay = 4

fire_alerted = False

def led(fingerUp, fire_detected):
    if not fire_detected:
        print("No fire detected.")

    if fingerUp == [0, 0, 0, 0, 0]:
        led_1.write(0)
        led_2.write(0)
    
    elif fingerUp == [0, 1, 0, 0, 0]:
        led_1.write(1)
        led_2.write(0)
        
    elif fingerUp == [0, 1, 1, 0, 0]:
        led_1.write(0)
        led_2.write(1)
        
    elif fingerUp == [0, 1, 1, 1, 0]:
        led_1.write(1)
        led_2.write(1)
        
    elif fingerUp == [0, 1, 1, 1, 1]:
        led_1.write(0)
        led_2.write(0)
        
    elif fingerUp == [1, 1, 1, 1, 1]:
        led_1.write(0)
        led_2.write(0)

def map_pan_angle(face_center_x, houseAI_width):
    if face_center_x is not None:
        return int(map_value(face_center_x, 0, houseAI_width, 60, 120))
    else:
        return prev_pan_angle

def map_tilt_angle(face_center_y, houseAI_height):
    if face_center_y is not None:
        return int(map_value(face_center_y, 0, houseAI_height, 40, 140))
    else:
        return prev_tilt_angle

def map_value(value, in_min, in_max, out_min, out_max):
    return (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

while True:
    ret, houseAI = video.read()
    #houseAI = cv2.resize(houseAI, (980, 740))
    hands, img = detector.findHands(houseAI)
    
    if hands:
        lmList = hands[0]
        fingerUp = detector.fingersUp(lmList)
        led(fingerUp, fire_detected_time is not None)
        cv2.putText(houseAI, f'Finger count: {sum(fingerUp)}', (20, 460), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 1, cv2.LINE_AA)
        if fingerUp == [0, 1, 1, 1, 1]:
            servo_4_angle = 0
        elif fingerUp == [0, 0, 0, 0, 0]:
            servo_4_angle = 45
        else:
            servo_4_angle = 45
        servo_4.write(servo_4_angle)
        prev_servo_4_angle = servo_4_angle
    gray = cv2.cvtColor(houseAI, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    
    if len(faces) > 0:
        no_face_count = 0
        (x, y, w, h) = faces[0]
        cv2.rectangle(houseAI, (x, y), (x + w, y + h), (255, 0, 0), 2)
        face_center_x = x + w // 2
        face_center_y = y + h // 2

        if prev_face_center_x is not None and prev_face_center_y is not None:
            pan_angle = 180 - map_pan_angle(face_center_x, houseAI.shape[1])
            tilt_angle = map_tilt_angle(face_center_y, houseAI.shape[0])
            pan_angle = prev_pan_angle + (pan_angle - prev_pan_angle) / move_speed
            tilt_angle = prev_tilt_angle + (tilt_angle - prev_tilt_angle) / move_speed

            pan_servo.write(int(pan_angle))
            tilt_servo.write(int(tilt_angle))

            prev_pan_angle = pan_angle
            prev_tilt_angle = tilt_angle

        else:
            prev_face_center_x = face_center_x
            prev_face_center_y = face_center_y

        if len(faces) > 0 and fire_detected_time is None:
            fire_detected_time = time.time()
    else:
        no_face_count += 1
        if no_face_count >= max_no_face_count:
            moving = False

    houseAI_resize = cv2.resize(houseAI, (640, 480))
    result_fire = model_fire(houseAI_resize, stream=True)

    fire_detected = False
    for info in result_fire:
        boxes = info.boxes
        for box in boxes:
            confidence = box.conf[0]
            confidence = math.ceil(confidence * 100)
            Class = int(box.cls[0])
            if confidence > 50:
                x1, y1, x2, y2 = box.xyxy[0]
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                cv2.rectangle(houseAI, (x1, y1), (x2, y2), (0, 0, 255), 5)
                cv2.putText(houseAI, f'{classnames[Class]} {confidence}%', (x1 + 8, y1 + 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
                fire_detected = True
    if fire_detected:
        board.digital[13].write(1)
    else:
        board.digital[13].write(0)
        results = model_person(houseAI)
        for info in results:
            parameters = info.boxes
            for box in parameters:
                x1, y1, x2, y2 = box.xyxy[0]
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                confidence = box.conf[0]
                class_detect = box.cls[0]
                class_detect = int(class_detect)
                conf = math.ceil(confidence * 100)
                height = y2 - y1
                width = x2 - x1
                threshold = height - width
    cv2.imshow("houseAI", houseAI)
    k = cv2.waitKey(1)
    if k == ord("o"):
        break
video.release()
cv2.destroyAllWindows()
