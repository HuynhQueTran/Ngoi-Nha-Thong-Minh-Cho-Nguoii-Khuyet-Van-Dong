# Ngoi-Nha-Thong-Minh-Cho-Nguoii-Khuyet-Van-Dong
PHẦN GIẢI THÍCH CHI TIẾT CODE CHƯƠNG TRÌNH
Phần 1: Code nhận diện cử chỉ điều khiển:
1. Thư viện Sử dụng
Giải thích
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
import config
Flask: Là một framework web  dùng để xây dựng ứng dụng web. Ở đây, Flask được sử dụng để tạo và quản lý các route và giao diện web.
cv2 (OpenCV): Thư viện xử lý ảnh và video, được sử dụng để đọc, xử lý và hiển thị video.
mediapipe: Thư viện từ Google, được sử dụng để nhận diện pose (dáng người) và cử chỉ.
numpy: Thư viện tính toán số học, đặc biệt hữu ích trong việc xử lý mảng và ma trận.
pygame: Thư viện để xử lý âm thanh và chơi nhạc, được sử dụng ở đây để phát các âm thanh cảnh báo.
FER: Thư viện nhận diện cảm xúc trong hình ảnh, dùng để nhận diện cảm xúc khuôn mặt.
PIL ( Imaging Library): Thư viện xử lý ảnh, đặc biệt trong việc vẽ chữ lên hình ảnh.
os: Thư viện để làm việc với hệ thống tập tin, như kiểm tra sự tồn tại của thư mục hoặc tạo thư mục mới.
requests: Thư viện để gửi HTTP request, dùng để điều khiển các thiết bị qua giao thức HTTP.
cvzone: Thư viện bổ trợ cho OpenCV, đặc biệt cho việc nhận diện cử chỉ tay.
YOLO (You Only Look Once): Một mô hình học sâu dùng để phát hiện đối tượng (trong trường hợp này là phát hiện lửa).
math: Thư viện toán học, được sử dụng để tính toán một số phép toán như làm tròn giá trị.
time: Thư viện xử lý thời gian, đặc biệt trong việc đánh dấu thời gian và đặt tên cho các hình ảnh lưu trữ.
telebot: Thư viện cho phép tương tác với API Telegram để gửi tin nhắn hoặc hình ảnh.
threading: Thư viện hỗ trợ xử lý đa luồng, cho phép thực hiện các tác vụ song song.
config: Một module chứa các cấu hình, chẳng hạn như địa chỉ IP của ESP (một thiết bị ngoại vi trong hệ thống).
2. Cấu hình các đối tượng và khởi tạo Flask App
Giải thích
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()
bot_token = '7837480809:AAH538Eptco2p08H_j0C_M-_86mO_teXLsM'
bot = telebot.TeleBot(bot_token)
live_stream_url = 'http://192.168.137.237:5000/'
chat_id = '-1002384540377'
fire_detected_threshold = 80
start_time = None
alert_played = False
app = Flask(__name__)
mp_pose: Khởi tạo bộ xử lý để nhận diện pose.
pose: Tạo đối tượng Pose từ MediaPipe để thực hiện nhận diện pose trên ảnh hoặc video.
bot_token: Token xác thực cho bot Telegram.
bot: Đối tượng bot Telegram được khởi tạo để gửi tin nhắn.
live_stream_url: Địa chỉ URL của stream video trực tiếp (ở đây giả định là stream từ Flask server).
chat_id: ID của chat Telegram để gửi thông báo.
fire_detected_threshold: Ngưỡng xác định lửa (ví dụ: nhận diện lửa khi độ tin cậy trên 80%).
start_time và alert_played: Biến dùng để theo dõi thời gian và trạng thái cảnh báo.
app: Khởi tạo ứng dụng Flask.
3. Lớp FallDetectionApp
Lớp này quản lý các chức năng của ứng dụng như nhận diện cử chỉ tay, phát hiện ngã, điều khiển thiết bị, và gửi cảnh báo.
Giải thích
class FallDetectionApp:
	def __init__(self):
    	pygame.mixer.init()  # Khởi tạo pygame mixer để chơi âm thanh
    	self.mp_pose = mp.solutions.pose  # Định nghĩa pose của MediaPipe
    	self.pose = self.mp_pose.Pose()  # Tạo đối tượng nhận diện pose
    	self.mp_drawing = mp.solutions.drawing_utils  # Dùng để vẽ landmarks lên ảnh
    	self.emotion_detector = FER()  # Khởi tạo detector cảm xúc
    	self.detector = HandDetector(detectionCon=0.8, maxHands=1)  # Cấu hình detector cử chỉ tay
    	self.model_fire = YOLO('fire.pt')  # Mô hình YOLO để phát hiện lửa
    	self.esp_ip = config.ESP_IP  # Địa chỉ IP của ESP
    	self.cap = cv2.VideoCapture(10)  # Khởi tạo camera, đây là chỉ số thiết bị video
    	self.camera_running = True  # Biến để kiểm soát việc bật/tắt camera
    	self.frame_count = 0  # Đếm số khung hình đã xử lý
    	self.frame_interval = 1  # Tần suất xử lý frame
    	self.drawing = False  # Biến kiểm tra nếu có vẽ vùng an toàn
    	self.start_point = None
    	self.end_point = None
    	self.safety_zones = self.load_safety_zones('safety_zones.txt')  # Đọc vùng an toàn từ file
    	self.fire_detected_time = None  # Thời gian phát hiện lửa
    	self.fire_alerted = False  # Cảnh báo lửa đã được phát
    	self.finger_control_active = True  # Kiểm tra điều khiển bằng cử chỉ tay có đang hoạt động
    	self.photo_dir = "fall_detected_photos"  # Thư mục lưu ảnh khi phát hiện ngã
    	if not os.path.exists(self.photo_dir):
        	os.makedirs(self.photo_dir)  # Tạo thư mục nếu chưa có
Phương thức trong lớp FallDetectionApp:
save_image: Lưu ảnh vào thư mục khi phát hiện sự cố như ngã hoặc lửa.
send_image_to_telegram: Gửi hình ảnh đến Telegram sau khi phát hiện sự cố.
gen_frames: Chức năng chính để lấy các khung hình từ camera, xử lý chúng (phát hiện ngã, phát hiện lửa, nhận diện cử chỉ tay) và trả về khung hình cho Flask để phát trực tuyến.
load_safety_zones: Đọc các vùng an toàn từ file và trả về danh sách các vùng.
check_safety: Kiểm tra xem vị trí (tọa độ) có nằm trong vùng an toàn hay không.
put_text: Vẽ chữ lên ảnh (chẳng hạn như "An toàn" hoặc "Nguy hiểm").
save_safety_zones: Lưu các vùng an toàn vào file.
led_control: Điều khiển đèn LED (qua ESP) dựa trên cử chỉ tay.
move_servo: Điều khiển động cơ servo qua ESP.
update_safety_zones: Cập nhật các vùng an toàn mới.
toggle_camera: Bật/tắt camera.
send_alert: Gửi cảnh báo âm thanh.
update_settings: Cập nhật cài đặt hệ thống.
4. Flask Routes
index: Trang chủ, trả về template HTML.
video_feed: Trả về stream video cho Flask client (HTML page).
toggle_camera_route: Đổi trạng thái bật/tắt camera.
get_safety_zones: Lấy danh sách các vùng an toàn.
play_alert_sound: Phát âm thanh cảnh báo.
set_safety_zone: Cài đặt vùng an toàn mới thông qua các tọa độ từ form.
5. Hàm run
def run(self):
	app.run(debug=True, host='0.0.0.0')
run: Chạy ứng dụng Flask.
6. Tạo đối tượng và chạy ứng dụng
if __name__ == '__main__':
	fall_detection_app = FallDetectionApp()
	fall_detection_app.run()
Khởi tạo đối tượng FallDetectionApp và chạy ứng dụng Flask.

Các Phân Tích Chi Tiết
1.     Nhận diện tư thế người (Pose Detection)
o    Phần này sử dụng thư viện mediapipe để phát hiện các điểm (landmarks) trên cơ thể con người trong video.
o    Các điểm cột sống và khớp cơ thể như shoulder_left, shoulder_right, hip_left, hip_right, knee_left, head.
2.     Tính toán và kiểm tra an toàn (Safety Check)
o    Kiểm tra nếu đầu (head) của người nằm trong vùng an toàn bằng cách so sánh tọa độ với các biên giới của những vùng đã được định nghĩa.
3.     Nhận diện ngã (Fall Detection)
o    Để xác định một người có bị ngã hay không, cần kiểm tra vị trí của các điểm quan trọng như vai, hông và đầu gối.
4.     Nhận diện điều khiển cử chỉ bằng tay (Hand Gesture Control)
o    Sử dụng thư viện cvzone.HandTrackingModule để nhận diện các ngón tay và cử chỉ.
5.     Nhận diện và cảnh báo cháy (Fire Detection)
o    Mô hình YOLO (You Only Look Once) được sử dụng để nhận diện các vùng có khả năng cháy với độ tin cậy nhất định.
6.     Xử lý âm thanh cảnh báo (Alert Sound)
o    Khi phát hiện một sự kiện như ngã hoặc cháy, âm thanh cảnh báo sẽ được phát bằng thư viện pygame.
7.     Hệ thống điều khiển qua Telegram
o    Sau khi phát hiện sự kiện, hình ảnh sẽ được lưu lại và gửi qua Telegram thông qua API TeleBot.

Phần 2:
Hệ Thống Điều Khiển Thiết Bị Bằng Giọng Nói
Code bạn gửi là một hệ thống điều khiển thiết bị trong nhà bằng giọng nói. Sau đây là giải thích chi tiết về các phần của mã này:
1. Thư viện và cấu hình
Giải thích
import os
import time
import requests
import speech_recognition as sr
from gtts import gTTS
import pygame
import config
os: Quản lý các thao tác với hệ điều hành, ví dụ như kiểm tra sự tồn tại của file hoặc xóa file.
time: Quản lý thời gian, ví dụ như trì hoãn chương trình hoặc đợi các sự kiện.
requests: Gửi các yêu cầu HTTP để điều khiển các thiết bị IoT (như bật/tắt đèn, quạt).
speech_recognition: Thư viện nhận diện giọng nói, cho phép chuyển đổi âm thanh thành văn bản.
gTTS: Thư viện chuyển văn bản thành giọng nói, sử dụng Google Text-to-Speech.
pygame: Dùng để phát âm thanh (feedback âm thanh sau khi nhận lệnh).
config: Chứa các cấu hình, ví dụ như địa chỉ IP của ESP (cảm biến, thiết bị IoT).
2. Các hàm điều khiển thiết bị
Giải thích
def turn_on_led1():
	requests.get(f"{esp_ip}/led1/on")
 
def turn_off_led1():
	requests.get(f"{esp_ip}/led1/off")
# Tương tự với các đèn khác, quạt và servo
Mỗi hàm sử dụng requests.get() để gửi yêu cầu HTTP đến ESP8266 (hoặc bất kỳ thiết bị IoT nào khác) để điều khiển các thiết bị như đèn, quạt hoặc servo.
3. Cung cấp phản hồi bằng âm thanh
Giải thích
def provide_feedback(message):
	print(f"Tôi rõ: {message}")
	tts = gTTS(text=message, lang='vi')
    tts.save(file_to_save)
    pygame.mixer.init()
    pygame.mixer.music.load(file_to_save)
    pygame.mixer.music.play()
	while pygame.mixer.music.get_busy(): 
        pygame.time.Clock().tick(10)
    pygame.mixer.music.stop()
    os.remove(file_to_save)
Dùng gTTS để chuyển văn bản thành giọng nói. Giọng nói này được lưu vào file .mp3 và phát lại bằng pygame. Sau khi âm thanh phát xong, file âm thanh sẽ được xóa.
4
def listen_for_command():
	recognizer = sr.Recognizer()
	with sr.Microphone() as source:
    	print("Đang nghe...")
    	recognizer.adjust_for_ambient_noise(source)
    	audio = recognizer.listen(source)
 
	try:
    	command = recognizer.recognize_google(audio, language='vi-VN').lower()
    	print(f"Đã nghe: {command}")
    	return command
	except sr.UnknownValueError:
    	print("Không nghe được lệnh.")
	except sr.RequestError:
    	print("Lỗi kết nối đến dịch vụ nhận diện giọng nói.")
    	provide_feedback("Có lỗi xảy ra khi kết nối đến dịch vụ nhận diện giọng nói.")
 
	return ""
Sử dụng speech_recognition để nghe âm thanh từ microphone và chuyển thành văn bản bằng Google Speech Recognition.
5. Xử lý lệnh
def execute_command(command):
	if 'chào' in command:
    	provide_feedback("Chào bạn! Tôi đã sẵn sàng nhận lệnh.")
	elif 'cảm ơn' in command:
    	provide_feedback("Không có gì. Tôi sẽ ngừng nhận lệnh.")
	elif 'bật đèn 1' in command:
    	turn_on_led1()
    	provide_feedback("OK, đèn 1 đã được bật.")
	# Các lệnh khác tương tự...
Dựa trên văn bản nhận diện từ giọng nói, hệ thống thực thi các hành động tương ứng.
6. Lấy thông tin nhiệt độ và độ ẩm từ ESP
def get_temperature_humidity():
	try:
    	response = requests.get(f"{esp_ip}/temperature")
    	if response.status_code == 200:
        	return response.text
    	else:
        	return "Không thể lấy dữ liệu từ cảm biến."
	except requests.RequestException:
    	return "Lỗi kết nối đến ESP8266."
Gửi yêu cầu HTTP đến ESP để lấy thông tin về nhiệt độ và độ ẩm.
7. Vòng lặp chính
def main():
	while True:
    	command = listen_for_command()
    	if command:
        	execute_command(command)
Chạy vòng lặp liên tục, lắng nghe các lệnh giọng nói và thực thi các lệnh này nếu có.
8. Kiểm tra điều kiện khi bắt đầu chương trình
Copyif __name__ == "__main__":
	main()
Đảm bảo rằng main() chỉ chạy khi script được chạy trực tiếp, không phải khi module được nhập vào từ nơi khác.

Tổng Kết
Phần cứng: ESP8266 hoặc thiết bị IoT khác điều khiển các thiết bị (đèn, quạt, servo).
Giọng nói: Hệ thống sử dụng speech_recognition để nhận diện các lệnh giọng nói từ người dùng và thực thi các hành động điều khiển thiết bị.
Phản hồi: Sau khi nhận lệnh và thực thi, hệ thống cung cấp phản hồi bằng giọng nói thông qua gTTS và phát lại qua pygame.
Điều khiển từ xa: Các yêu cầu HTTP được gửi từ máy tính đến ESP để điều khiển thiết bị (bật/tắt đèn, quạt, kiểm tra nhiệt độ).

Phần 3: Điều Khiển LED và Cảm Biến qua Bot Telegram
1.     Cấu hình Bot Telegram:
o	Đoạn mã sử dụng thư viện telebot để tạo một bot Telegram. Bot này nhận lệnh từ người dùng qua tin nhắn và thực hiện các hành động điều khiển thiết bị (như bật/tắt đèn, điều khiển servo, quạt,...) dựa trên các lệnh nhận được.
o	bot_token là token của bot, dùng để nhận và gửi tin nhắn qua API Telegram.
o	chat_id là ID của nhóm hoặc cá nhân mà bot sẽ gửi tin nhắn.
2.     Điều khiển Servo và Cảm biến Nhiệt Độ và Độ ẩm:
o	move_servo(angle): Hàm này điều khiển servo qua ESP8266 bằng cách gửi yêu cầu HTTP để thay đổi góc servo (từ 0 đến 180 độ).
o	get_temperature_humidity(): Hàm này gửi yêu cầu HTTP tới ESP8266 để lấy dữ liệu cảm biến nhiệt độ và độ ẩm. Nếu thành công, nó trả về dữ liệu từ cảm biến.
3.     Phản hồi qua Bot Telegram:
o	provide_feedback(message): Hàm gửi phản hồi về kết quả của lệnh điều khiển (ví dụ: "LED 1 đã bật", "Quạt đã tắt",...).
4.     Xử lý lệnh điều khiển thiết bị qua Bot:
o	handle_device_control(command, chat_id): Nhận lệnh từ người dùng qua tin nhắn Telegram, sau đó điều khiển các thiết bị tương ứng (bật/tắt đèn, quạt, servo, hoặc gửi liên kết video stream từ camera).
o	Các lệnh như '1', '2', '3' dùng để bật/tắt LED, '4', '04' dùng để điều khiển servo (mở/đóng cửa), '5', '05' để bật/tắt quạt.
5.     Chạy Bot:
o	bot.message_handler(func=lambda message: True): Hàm này là nơi bot nhận và xử lý mọi tin nhắn gửi đến. Sau khi nhận được lệnh từ người dùng, bot sẽ gọi handle_device_control() để thực hiện.
6.     Chạy Bot:
o	bot.polling(none_stop=True): Bot sẽ tiếp tục chạy và lắng nghe tin nhắn từ người dùng.
Phần 4: Cài Đặt và Cập Nhật Vị Trí (Phát hiện ngã với khu vực an toàn)
1.     Cấu hình Video Stream và Webcam:
o	cv2.VideoCapture(10): Dùng OpenCV để mở webcam hoặc camera IP. Dòng lệnh này mở webcam và lấy dữ liệu video từ đó.
o	rtsp_url: Cấu hình cho việc truyền trực tiếp video từ camera IP, nếu sử dụng RTSP.
2.     Vẽ Khu Vực An Toàn:
o	Trong phương thức draw_rectangle, người dùng có thể vẽ một hình chữ nhật để xác định khu vực an toàn trên màn hình. Khi người dùng nhấn chuột, hệ thống sẽ bắt đầu vẽ một hình chữ nhật, và khi nhả chuột, khu vực đó sẽ được lưu lại.
3.     Lưu và Tải Khu Vực An Toàn:
o	save_safety_zone và save_safety_zones: Lưu thông tin các khu vực an toàn vào một tệp văn bản. Mỗi khu vực an toàn được lưu dưới dạng tọa độ của hai góc đối diện.
o	load_safety_zones: Hàm này đọc dữ liệu từ tệp và khôi phục lại các khu vực an toàn khi ứng dụng khởi động lại.
4.     Hiển Thị Khu Vực An Toàn:
o	Trong phương thức gen_frames, video từ webcam sẽ được hiển thị, đồng thời các khu vực an toàn đã được xác định sẽ được vẽ lên màn hình (màu sắc là màu vàng).
o	Nếu người dùng đang vẽ một khu vực an toàn, nó sẽ hiển thị trên màn hình với màu xanh lá cây.
5.     Dừng ứng dụng:
o	Khi người dùng nhấn phím 'q', ứng dụng sẽ dừng lại và đóng tất cả các cửa sổ hiển thị OpenCV.
 
Phần 5 Cảnh báo té ngã trong nhà vệ sinh
1. Cài đặt ban đầu
import cv2
import mediapipe as mp
import numpy as np
import pygame
import telebot
from datetime import datetime
import os
cv2: Thư viện OpenCV để xử lý video và hình ảnh.
mediapipe: Thư viện của Google để xử lý và nhận diện các tư thế cơ thể.
numpy: Thư viện tính toán số học cho các phép toán ma trận, ví dụ như tính toán góc.
pygame: Dùng để phát âm thanh khi phát hiện té ngã.
telebot: Dùng để gửi thông báo qua Telegram khi phát hiện té ngã.
datetime: Lấy thời gian hiện tại để đặt tên cho ảnh.
os: Quản lý các thư mục và tệp tin.
2. Khởi tạo MediaPipe và các công cụ
 
 
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
pose = mp_pose.Pose()
pygame.mixer.init()
fall_sound = pygame.mixer.Sound("fall_sound.wav")
bot_token = '7837480809:AAH538Eptco2p08H_j0C_M-_86mO_teXLsM'
bot = telebot.TeleBot(bot_token)
chat_id = '-1002384540377'
output_folder = "fall_detected_photos"
os.makedirs(output_folder, exist_ok=True)
mp_pose.Pose(): Khởi tạo đối tượng Pose của MediaPipe để theo dõi và nhận diện tư thế cơ thể.
pygame.mixer.init(): Khởi tạo hệ thống âm thanh của pygame để phát âm thanh khi té ngã.
fall_sound: Tải tệp âm thanh cảnh báo khi phát hiện té ngã.
bot_token và bot: Khởi tạo bot Telegram để gửi thông báo.
chat_id: ID của nhóm hoặc người nhận thông báo.
output_folder: Thư mục lưu trữ ảnh khi phát hiện té ngã.
3. Mở camera
 
 
cap = cv2.VideoCapture(1)
cv2.VideoCapture(1): Mở camera (thường là camera thứ hai trong hệ thống).
4. Hàm gửi cảnh báo té ngã qua Telegram
def send_fall_alert(image_path):
	with open(image_path, 'rb') as photo:
        bot.send_photo(chat_id, photo)
send_fall_alert(image_path): Hàm gửi ảnh qua Telegram khi phát hiện té ngã.
Ảnh được mở bằng open() trong chế độ nhị phân ('rb').
Sử dụng phương thức send_photo của telebot để gửi ảnh.
5. Hàm phát hiện té ngã
def detect_fall(landmarks):
    shoulder_left = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
    shoulder_right = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]
	hip_left = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
	hip_right = landmarks[mp_pose.PoseLandmark.RIGHT_HIP]
	nose = landmarks[mp_pose.PoseLandmark.NOSE]
	shoulder_y = (shoulder_left.y + shoulder_right.y) / 2
	hip_y = (hip_left.y + hip_right.y) / 2
	torso_angle = np.arctan2(hip_y - shoulder_y, hip_right.x - shoulder_left.x) * 180 / np.pi
	if abs(shoulder_y - hip_y) < 0.15 and abs(torso_angle) < 30:
    	return True
	return False
detect_fall(landmarks): Phát hiện té ngã dựa vào các điểm đặc trưng của cơ thể (được lấy từ landmarks).
shoulder_left, shoulder_right, hip_left, hip_right, nose: Các điểm trên cơ thể được xác định bởi MediaPipe Pose (vai, hông, mũi).
shoulder_y và hip_y: Tính toán vị trí trung bình của vai và hông.
torso_angle: Tính toán góc của thân người dựa trên vị trí của vai và hông.
Nếu shoulder_y và hip_y cách nhau dưới 0.15 và torso_angle nhỏ hơn 30 độ, hệ thống cho rằng người dùng đang trong tình trạng té ngã.
6. Vòng lặp chính để nhận diện và phát hiện té ngã
fall_detected_frames = 0
fall_confirmation_frames = 5
 
while cap.isOpened():
	ret, frame = cap.read()
	if not ret:
    	break
 
	rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
	results = pose.process(rgb_frame)
 
    skeleton_frame = np.zeros_like(frame)
 
	if results.pose_landmarks:
        mp_drawing.draw_landmarks(
            skeleton_frame,
            results.pose_landmarks,
            mp_pose.POSE_CONNECTIONS,
            mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=3)
    	)
    	if detect_fall(results.pose_landmarks.landmark):
            fall_detected_frames += 1
    	else:
            fall_detected_frames = 0
    	if fall_detected_frames >= fall_confirmation_frames:
            fall_sound.play()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            skeleton_image_path = os.path.join(output_folder, f"skeleton_fall_detected_{timestamp}.jpg")
            cv2.imwrite(skeleton_image_path, skeleton_frame)
            send_fall_alert(skeleton_image_path)
            fall_detected_frames = 0 
 
    cv2.imshow("OUT DETCTED", skeleton_frame)
 
	if cv2.waitKey(1) & 0xFF == ord('q'):
    	break
 
cap.release()
fall_detected_frames: Đếm số frame liên tiếp phát hiện té ngã.
fall_confirmation_frames: Số frame cần phát hiện té ngã liên tiếp để xác nhận là té ngã thật sự.
results.pose_landmarks: Lấy các điểm tư thế cơ thể từ MediaPipe.
mp_drawing.draw_landmarks(): Vẽ các điểm tư thế cơ thể lên hình ảnh.
detect_fall(): Kiểm tra nếu người dùng đang té ngã.
Nếu phát hiện té ngã trong fall_confirmation_frames frame, hệ thống sẽ phát âm thanh cảnh báo, lưu ảnh và gửi ảnh qua Telegram.
cv2.imshow(): Hiển thị video với các điểm tư thế cơ thể.
cv2.waitKey(1): Đợi người dùng nhấn 'q' để thoát khỏi vòng lặp.
Tóm tắt:
Hệ thống sử dụng camera để theo dõi người dùng trong nhà vệ sinh, nhận diện các điểm cơ thể và tính toán các chỉ số như góc của thân người.
Nếu người dùng té ngã (theo các chỉ số này), hệ thống sẽ phát âm thanh cảnh báo và gửi ảnh qua Telegram.
Sau khi xác nhận té ngã trong một số frame liên tiếp, hệ thống sẽ gửi thông báo và hình ảnh té ngã qua Telegram.


 Phần 6: Hàm Dùng để tạo luồng qua địa chỉ ip vs file là config.py
Định nghĩa địa chỉ IP của ESP:
ESP_IP = 'http://192.168.137.66': Đây là địa chỉ IP của ESP trong mạng, giúp các chương trình khác liên lạc với nó khi cần.
Phần 7: Phân ra 4 luồng để chạy các file. Nghĩa là 1 file sẽ chạy 1 luồng hàm này tương ứng với hàm main toàn chương trình
  Hàm run_file1, run_file2, run_file3, run_file4:
Mỗi hàm dùng subprocess.run() để chạy một tệp  riêng:
run_file1(): Chạy tệp telegram call image.py để gọi tính năng gọi và gửi hình ảnh qua Telegram.
run_file2(): Chạy tệp control led và nhiệt độ.py để điều khiển LED và đọc nhiệt độ từ các thiết bị.
run_file3(): Chạy tệp voiceweb.py để thực hiện chức năng điều khiển bằng giọng nói và quản lý giao diện web.
run_file4(): Chạy tệp wc.py để quản lý các chức năng liên quan đến phát hiện té ngã hoặc giám sát khu vực vệ sinh.
Khởi tạo các luồng (threads):
Mỗi tệp sẽ chạy trong một luồng riêng, cho phép các chương trình hoạt động đồng thời mà không phải chờ đợi lẫn nhau.
Các luồng được tạo với:
thread1 = threading.Thread(target=run_file1)
thread2 = threading.Thread(target=run_file2)
thread3 = threading.Thread(target=run_file3)
thread4 = threading.Thread(target=run_file4)
Bắt đầu và đợi các luồng hoàn thành:
start(): Bắt đầu từng luồng, khiến các tệp  chạy song song.
join(): Đợi cho đến khi các luồng hoàn thành trước khi tiếp tục (hoặc kết thúc) chương trình chính.
Phần 8: Phát hiện người lạ.
 1. Cấu hình Telegram
TELEGRAM_TOKEN = '7837480809:AAH538Eptco2p08H_j0C_M-_86mO_teXLsM'
CHAT_ID = '-1002384540377'
TELEGRAM_TOKEN: Đây là mã token của bot Telegram, dùng để xác thực bot khi gửi tin nhắn.
CHAT_ID: ID của nhóm hoặc người nhận tin nhắn trên Telegram. Tin nhắn sẽ được gửi đến chat này.
2. Hàm gửi ảnh qua Telegram
def send_telegram_photo(photo_path):
	url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
	with open(photo_path, 'rb') as photo_file:
    	params = {
        	'chat_id': CHAT_ID,
    	}
    	response = requests.post(url, params=params, files={'photo': photo_file})
	return response
send_telegram_photo(photo_path): Hàm này dùng để gửi ảnh qua Telegram.
photo_path: Đường dẫn đến ảnh cần gửi.
requests.post(): Gửi ảnh qua API của Telegram. Ảnh sẽ được mở bằng open() dưới chế độ nhị phân ('rb').
params chứa chat_id (địa chỉ nhận tin nhắn).
files là tham số chứa ảnh cần gửi.
3. Tải và xử lý các ảnh khuôn mặt đã biết
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
known_faces = []
known_face_names = []
 
path = 'training'
for filename in os.listdir(path):
	if filename.endswith('.jpg') or filename.endswith('.png'):
    	image_path = os.path.join(path, filename)
    	image = cv2.imread(image_path)
    	gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    	faces = face_cascade.detectMultiScale(gray, 1.1, 4)
 
    	for (x, y, w, h) in faces:
        	face_roi = gray[y:y+h, x:x+w]
        	known_faces.append(face_roi)
        	name = os.path.splitext(filename)[0]
        	known_face_names.append(name)
face_cascade: Tải mô hình phát hiện khuôn mặt Haar Cascade để nhận diện khuôn mặt trong ảnh.
known_faces: Danh sách lưu các khuôn mặt đã biết dưới dạng mảng ảnh grayscale.
known_face_names: Danh sách lưu tên tương ứng của các khuôn mặt đã biết.
path = 'training': Đọc ảnh từ thư mục training.
os.listdir(path): Duyệt qua tất cả các tệp trong thư mục training.
cv2.imread(): Đọc ảnh từ đĩa.
cv2.cvtColor(): Chuyển ảnh sang grayscale để việc nhận diện khuôn mặt dễ dàng hơn.
face_cascade.detectMultiScale(): Phát hiện khuôn mặt trong ảnh.
4. Mở camera và nhận diện khuôn mặt trong video
video_capture = cv2.VideoCapture(0)
 
while True:
	ret, frame = video_capture.read()
	gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
 
	faces = face_cascade.detectMultiScale(gray_frame, 1.1, 4)
 
	for (x, y, w, h) in faces:
    	face_roi = gray_frame[y:y+h, x:x+w]
    	name = "Unknown"
    	for i, known_face in enumerate(known_faces):
        	result = cv2.compareHist(
            	cv2.calcHist([face_roi], [0], None, [256], [0, 256]),
            	cv2.calcHist([known_face], [0], None, [256], [0, 256]),
            	cv2.HISTCMP_CORREL
        	)
        	if result > 0.2:
            	name = known_face_names[i]
            	ak
video_capture = cv2.VideoCapture(0): Mở camera để nhận diện khuôn mặt trong thời gian thực.
ret, frame = video_capture.read(): Đọc mỗi frame từ camera.
cv2.cvtColor(): Chuyển đổi frame sang grayscale.
face_cascade.detectMultiScale(): Phát hiện khuôn mặt trong mỗi frame.
cv2.compareHist(): So sánh các histogram giữa khuôn mặt phát hiện được và các khuôn mặt đã biết để nhận diện khuôn mặt. Nếu sự tương đồng lớn hơn 0.2, đó là khuôn mặt đã biết.
5. Chụp ảnh và gửi qua Telegram nếu không nhận diện được khuôn mặt
if name == "Unknown":
	timestamp = time.strftime("%Y%m%d-%H%M%S")
	screenshot_path = f"unknown_face_{timestamp}.jpg"
	cv2.imwrite(screenshot_path, frame) 
	send_telegram_photo(screenshot_path)
	os.remove(screenshot_path) 
if name == "Unknown":: Nếu không nhận diện được khuôn mặt (tên là "Unknown"), hệ thống sẽ chụp ảnh và gửi ảnh đó qua Telegram.
time.strftime(): Lấy thời gian hiện tại để tạo tên ảnh.
cv2.imwrite(): Lưu ảnh chụp vào tệp.
send_telegram_photo(): Gửi ảnh qua Telegram.
os.remove(): Xóa ảnh tạm sau khi đã gửi.
6. Vẽ hình chữ nhật và hiển thị tên khuôn mặt
cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
cv2.putText(frame, name, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
cv2.rectangle(): Vẽ một hình chữ nhật quanh khuôn mặt trong mỗi frame.
cv2.putText(): Hiển thị tên khuôn mặt (hoặc "Unknown" nếu không nhận diện được).
7. Hiển thị video và dừng khi nhấn 'q'
cv2.imshow('Video', frame)
if cv2.waitKey(1) & 0xFF == ord('q'):
	break
cv2.imshow(): Hiển thị video trong cửa sổ.
cv2.waitKey(1): Chờ người dùng nhấn phím. Nếu phím 'q' được nhấn, vòng lặp sẽ dừng lại.
8. Giải phóng tài nguyên khi kết thúc
 
 
video_capture.release()
cv2.destroyAllWindows()
video_capture.release(): Giải phóng tài nguyên camera.
cv2.destroyAllWindows(): Đóng tất cả các cửa sổ OpenCV.
Phần 9: Chụp nhận diện khuôn mặt.
1. Tạo thư mục lưu ảnh
 
 
output_dir = 'training'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)
output_dir = 'training': Đặt tên thư mục lưu ảnh là training.
os.makedirs(output_dir): Kiểm tra xem thư mục này có tồn tại hay không. Nếu không, thư mục training sẽ được tạo ra.
2. Khởi tạo camera
 
 
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Cannot open camera")
	exit()
cap = cv2.VideoCapture(0): Mở camera với chỉ số 0 (thường là camera mặc định của máy tính).
cap.isOpened(): Kiểm tra xem camera có mở thành công không. Nếu không, sẽ in ra thông báo lỗi và kết thúc chương trình bằng exit().
3. Các biến cần thiết
 
 
capture_interval = 2
frame_count = 0
capture_interval = 2: Đặt thời gian chờ giữa mỗi lần chụp ảnh là 2 giây.
frame_count = 0: Khởi tạo biến đếm số lượng ảnh đã chụp.
4. Vòng lặp chụp ảnh
 
 
while True:
	ret, frame = cap.read()
	if not ret:
        print("Khong doc duoc ...")
    	break
    cv2.imshow('frame', frame)
	frame_count += 1
	img_path = os.path.join(output_dir, f'Que Tran_{frame_count:04d}.jpg')
    cv2.imwrite(img_path, frame)
    print(f"Saved {img_path}")
    time.sleep(capture_interval)
	if cv2.waitKey(1) == ord('q'):
    	break
while True:: Bắt đầu vòng lặp vô hạn để liên tục lấy ảnh từ camera.
ret, frame = cap.read(): Đọc một frame từ camera. Nếu không thể đọc, chương trình sẽ in thông báo lỗi và dừng lại.
cv2.imshow('frame', frame): Hiển thị ảnh vừa chụp trong một cửa sổ tên là 'frame'.
frame_count += 1: Tăng số đếm frame lên 1 mỗi khi chụp ảnh.
img_path = os.path.join(output_dir, f'Que Tran_{frame_count:04d}.jpg'): Đặt đường dẫn để lưu ảnh, tên ảnh sẽ theo định dạng Que Tran_XXXX.jpg, với XXXX là số thứ tự của ảnh (được định dạng 4 chữ số).
cv2.imwrite(img_path, frame): Lưu ảnh vào đường dẫn đã định.
print(f"Saved {img_path}"): In ra thông báo đã lưu ảnh tại đường dẫn này.
time.sleep(capture_interval): Tạm dừng chương trình trong 2 giây (theo giá trị capture_interval) giữa mỗi lần chụp ảnh.
if cv2.waitKey(1) == ord('q'):: Kiểm tra xem người dùng có nhấn phím q không. Nếu có, vòng lặp sẽ dừng lại.
5. Dọn dẹp tài nguyên khi kết thúc
 
 
finally:
    cap.release()
    cv2.destroyAllWindows()
cap.release(): Giải phóng tài nguyên của camera khi chương trình kết thúc.
cv2.destroyAllWindows(): Đóng tất cả cửa sổ OpenCV khi chương trình kết thúc.
Tóm lại:
Đoạn mã này sẽ:
1.     Mở camera.
2.     Chụp ảnh mỗi 2 giây và lưu ảnh vào thư mục training với tên là Que Tran_XXXX.jpg.
3.     Hiển thị ảnh đang được chụp trên cửa sổ frame.
4.     Dừng chụp khi người dùng nhấn phím q.
5.     Giải phóng tài nguyên khi kết thúc.
Chương trình này có thể hữu ích để thu thập dữ liệu hình ảnh cho các dự án học máy hoặc nhận dạng đối tượng.
 
Phần 10: Nhắc hẹn
1. Lớp ReminderSystem
Lớp này có vai trò quản lý và thực hiện các nhắc nhở trong hệ thống.
Thuộc tính self.reminders: Lưu trữ các nhắc nhở. Mỗi nhắc nhở sẽ có thời gian (dạng "HH
"), thông điệp và một cờ repeat cho biết liệu nhắc nhở có được lặp lại vào ngày hôm sau hay không.
2. Các phương thức trong ReminderSystem
add_reminder(time_str, message, repeat=False): Thêm một nhắc nhở vào từ điển self.reminders với thời gian, thông điệp và cờ repeat (mặc định là False).
show_reminders(): Hiển thị tất cả các nhắc nhở đã thêm.
speak_message(message): Dùng gTTS để chuyển văn bản thành giọng nói và phát thông báo qua loa.
check_reminders(): Kiểm tra nhắc nhở mỗi phút. Nếu thời gian hiện tại khớp với một nhắc nhở, hệ thống sẽ thông báo và hỏi người dùng có muốn lặp lại nhắc nhở vào ngày hôm sau không.
ask_for_repeat(message): Hỏi người dùng có muốn lặp lại nhắc nhở vào ngày hôm sau.
wait_for_reminder_time(): Chờ đến giờ nhắc nhở và thoát khỏi lắng nghe lệnh mới khi nhắc nhở đến giờ.
schedule_repeat(message): Lên lịch để lặp lại nhắc nhở vào ngày hôm sau.
start_reminder_check(): Bắt đầu kiểm tra nhắc nhở trong một luồng riêng biệt.
listen_for_commands(): Lắng nghe các lệnh giọng nói từ người dùng. Nếu người dùng nói "nhắc hẹn", hệ thống sẽ yêu cầu người dùng cung cấp thời gian và thông điệp nhắc nhở.
listen_for_reminder_details(): Lắng nghe chi tiết về thời gian và thông điệp nhắc nhở từ giọng nói, sau đó thêm nhắc nhở vào hệ thống.
3. Sử dụng thư viện ngoài
speech_recognition: Dùng để nhận diện giọng nói của người dùng.
playsound: Phát âm thanh nhắc nhở bằng giọng nói.
gTTS: Chuyển văn bản thành giọng nói (Text-to-Speech).
os: Quản lý các tệp, ví dụ như xóa tệp âm thanh sau khi phát.
4. Quy trình hoạt động
Bước 1: Khi chương trình khởi chạy, phương thức start_reminder_check() sẽ được gọi trong một luồng riêng biệt để kiểm tra các nhắc nhở mỗi phút.
Bước 2: Phương thức listen_for_commands() sẽ liên tục lắng nghe lệnh giọng nói từ người dùng. Khi người dùng nói "nhắc hẹn", hệ thống sẽ yêu cầu họ cung cấp chi tiết nhắc nhở.
Bước 3: Khi người dùng cung cấp thời gian và thông điệp, phương thức add_reminder() sẽ thêm nhắc nhở vào hệ thống.
Bước 4: Nếu thời gian của một nhắc nhở khớp với thời gian thực, hệ thống sẽ phát thông báo và hỏi người dùng có muốn lặp lại nhắc nhở vào ngày hôm sau.
Bước 5: Các nhắc nhở sẽ được lặp lại nếu người dùng chọn "có" khi hỏi về việc lặp lại.
5. Chạy chương trình
Sau khi khởi tạo đối tượng ReminderSystem, phương thức start_reminder_check() sẽ bắt đầu kiểm tra nhắc nhở trong một luồng riêng, trong khi phương thức listen_for_commands() lắng nghe các lệnh giọng nói.
6. Vấn đề tiềm ẩn
Tiếng ồn xung quanh: Hệ thống có thể gặp khó khăn trong việc nhận diện giọng nói nếu có quá nhiều tiếng ồn.
Định dạng thời gian: Người dùng cần phải nói thời gian đúng định dạng (ví dụ: "23 giờ 15"). Nếu không, chương trình có thể không nhận diện được.
Phần 11: Xử lí bàn tay:
1.     Thông tin cơ bản về gói:
o	name='cvzone': Tên của gói là cvzone.
o	packages=['cvzone']: Danh sách các gói  cần bao gồm. Ở đây, chỉ có một gói là cvzone.
o	version='1.6': Phiên bản của gói là 1.6.
o	license='MIT': Gói này sử dụng giấy phép MIT, cho phép sử dụng mã nguồn mở với ít hạn chế.
2.     Mô tả và thông tin tác giả:
o	description='Computer Vision Helping Library': Mô tả ngắn gọn về gói, nêu rõ đây là một thư viện hỗ trợ về Thị giác máy tính.
o	author='Computer Vision Zone': Tên tác giả hoặc tổ chức phát triển gói.
o	author_email='contact@computervision.zone': Email liên hệ của tác giả hoặc tổ chức phát triển.
o	url='https://github.com/cvzone/cvzone.git': URL đến kho lưu trữ mã nguồn trên GitHub.
3.     Keywords và yêu cầu cài đặt:
o	keywords=['ComputerVision', 'HandTracking', 'FaceTracking', 'PoseEstimation']: Từ khóa giúp người dùng tìm thấy gói khi tìm kiếm.
o	install_requires=[ 'opencv-', 'numpy']: Liệt kê các gói phụ thuộc cần được cài đặt cùng với gói cvzone. Ở đây, gói yêu cầu opencv- và numpy.
o	_requires='>=3.6': Gói yêu cầu  phiên bản 3.6 hoặc cao hơn.
4.     Phân loại (classifiers):
o	Development Status :: 3 - Alpha: Trạng thái phát triển là Alpha, cho thấy gói đang ở giai đoạn thử nghiệm.
o	Intended Audience :: Developers: Đối tượng sử dụng chính là các nhà phát triển.
o	Topic :: Software Development :: Build Tools: Chủ đề của gói là phát triển phần mềm, công cụ xây dựng.
o	License :: OSI Approved :: MIT License: Xác nhận gói được cấp phép MIT.
o	Programming Language ::  :: 3: Gói hỗ trợ  3.
Tóm tắt:
File setup.py này cấu hình để người dùng có thể dễ dàng cài đặt gói cvzone và các phụ thuộc liên quan bằng lệnh pip install cvzone.
Phần 12: Web
 1. Phần head
Cấu trúc tài liệu HTML5: Tài liệu bắt đầu bằng <!DOCTYPE html>, định nghĩa cấu trúc tài liệu là HTML5.
Metadata và CSS:
<meta charset="UTF-8">: Thiết lập mã hóa ký tự UTF-8.
<meta name="viewport" content="width=device-width, initial-scale=1.0">: Tạo responsive cho trang web bằng cách tối ưu hiển thị trên các thiết bị.
<title>Camera AI Home</title>: Tiêu đề của trang.
CSS: Định dạng giao diện của trang.
body: Định dạng nền trắng và font chữ Arial.
#header: Header với nền trắng, màu chữ xám đậm, canh giữa và padding.
#video-container: Đặt video ở giữa trang, bo tròn góc, đổ bóng, và có thể thay đổi kích thước để phù hợp với các thiết bị khác nhau.
#overlay và .notification: #overlay cho phép thêm overlay trên video, và .notification định dạng thông báo.
Watermark: #watermark-top và #watermark-bottom cho phép thêm các đoạn văn bản hoặc ảnh làm watermark ở đầu và cuối của khung video.
Button: .button-container căn giữa các nút, và .button định dạng cho các nút điều khiển với màu xanh dương và hiệu ứng hover.
2. Phần body
Video Feed:
html
 
<img id="video" src="{{ url_for('video_feed') }}" alt="Video Feed">
id="video": Tạo một khung để hiển thị video trực tiếp từ camera.
src="{{ url_for('video_feed') }}": Đường dẫn đến luồng video được cung cấp bởi Flask (ví dụ: qua một endpoint /video_feed).
Nút điều khiển:
html
 
<div class="button-container">
	<button class="button" onclick="toggleCamera()">Start/Stop Camera</button>
</div>
Nút Start/Stop Camera để bật hoặc tắt camera bằng cách gọi hàm JavaScript toggleCamera().
3. Phần script
toggleCamera():
javascript
 
function toggleCamera() {
    fetch('/toggle_camera', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            alert(data.message);
    	});
}
Chức năng: Gửi yêu cầu POST đến server (endpoint /toggle_camera) để bật/tắt camera.
Phản hồi: Hiển thị thông báo dựa trên data.message từ phản hồi JSON.
sendAlert():
javascript
 
function sendAlert() {
	fetch('/send_alert', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            alert(data.message);
    	});
}
Chức năng: Gửi yêu cầu POST đến /send_alert để gửi thông báo đến người dùng hoặc hệ thống.
Phản hồi: Hiển thị thông báo sau khi gửi thành công.
updateSettings():
javascript
 
function updateSettings() {
	const settings = { example: 'value' };
    fetch('/update_settings', {
    	method: 'POST',
    	headers: {
            'Content-Type': 'application/json'
    	},
    	body: JSON.stringify(settings)
	})
    .then(response => response.json())
	.then(data => {
        alert(data.message);
	});
}
Chức năng: Cập nhật cài đặt hệ thống bằng cách gửi dữ liệu JSON đến endpoint /update_settings.
Cài đặt: Dữ liệu được gửi dưới dạng JSON. Ví dụ trong mã, settings chứa { example: 'value' }, nhưng có thể chỉnh sửa thành dữ liệu thực tế.
Phản hồi: Hiển thị thông báo xác nhận cập nhật.
4. Responsive Design
@media (max-width: 600px): Tạo giao diện tương thích với màn hình nhỏ hơn 600px (thường là trên thiết bị di động).
Các thành phần như font chữ, kích thước ảnh và nút điều khiển được điều chỉnh để phù hợp với màn hình nhỏ hơn.
Tóm tắt:
Giao diện này hiển thị video từ camera AI và có các nút để điều khiển camera, gửi cảnh báo và cập nhật cài đặt.
Có thể tương tác với Flask backend thông qua JavaScript để bật/tắt camera, gửi cảnh báo và cập nhật cài đặt.
Giao diện này có khả năng tự điều chỉnh để phù hợp với các thiết bị khác nhau, từ máy tính đến điện thoại di động.
 
 
Phần 13 : ESP và phần cứng.
1. Kết nối Wi-Fi
ESP8266 kết nối với Wi-Fi sử dụng thông tin mạng được cung cấp trong ssid và password.
2. Cấu hình phần cứng
Cảm biến chuyển động (PIR): Được kết nối với chân D0 (PIR_PIN), phát hiện chuyển động.
Cảm biến nhiệt độ và độ ẩm (DHT11): Được kết nối với chân D6 (DHTPIN), sử dụng thư viện DHT để đo nhiệt độ và độ ẩm.
Cảm biến khí (MQ135): Kết nối với chân A0 để đo nồng độ khí độc, khói.
Servo motor: Được kết nối với chân D4 để điều khiển cửa (mở hoặc đóng).
Cảm biến mưa: Kết nối với chân D7 (rainSensorPin), phát hiện mưa.
Buzzer và đèn LED: Kết nối với các chân D9, D1, D2, D3, D4, D5, D8 để điều khiển các thiết bị ngoại vi như đèn và còi báo động.
3. Gửi thông báo qua Telegram
Telegram Bot: Được sử dụng để gửi thông báo khi phát hiện khí độc hoặc mưa. Token bot và chat ID được khai báo để gửi thông báo đến một nhóm hoặc cá nhân trên Telegram.
4. Web Server (ESP8266WebServer)
ESP8266WebServer: Server web chạy trên ESP8266 để nhận các lệnh điều khiển từ thiết bị khác thông qua HTTP. Các lệnh này có thể bật hoặc tắt các thiết bị (LED, quạt, servo) hoặc nhận thông tin từ cảm biến nhiệt độ, độ ẩm, khí độc.
/led1/on: Bật LED 1
/led1/off: Tắt LED 1
/fan3/on: Bật quạt 3
/servo/180: Mở cửa (servo motor)
/temperature: Lấy thông tin nhiệt độ và độ ẩm
/gas: Lấy thông tin về nồng độ khí và khói
5. Các hàm và xử lý trong loop()
Cảm biến chuyển động: Khi phát hiện chuyển động, bật LED 5 và gửi tín hiệu.
Cảm biến khí (MQ135): Đọc giá trị nồng độ khí gas và khói, nếu vượt quá ngưỡng, sẽ gửi thông báo qua Telegram và bật còi báo động.
Cảm biến mưa: Nếu có mưa, sẽ đóng cửa bằng servo và gửi thông báo.
6. Gửi thông báo qua Telegram
Sử dụng hàm sendTelegramMessage() để gửi thông báo đến nhóm/chat Telegram khi phát hiện khí độc hoặc mưa.
Các hành động xảy ra trong mã:
Cảm biến khí MQ135: Đo nồng độ khí và khói, nếu nồng độ vượt quá ngưỡng thì kích hoạt báo động.
Cảm biến mưa: Nếu có mưa, đóng cửa (servo quay về 0 độ) và gửi thông báo.
Cảm biến chuyển động PIR: Khi phát hiện chuyển động, bật đèn LED 5.
Đọc nhiệt độ và độ ẩm: Mỗi giây, mã sẽ đo và in ra thông số nhiệt độ và độ ẩm từ cảm biến DHT11.
Các điều kiện cảnh báo:
1.     Khí độc hoặc khói (ppmGas > 20): Khi có khí độc hoặc khói, báo động và gửi thông báo qua Telegram.
2.     Phát hiện mưa: Đóng cửa và gửi thông báo mưa qua Telegram.
 
Phần 14: Code nhận id đến telegram
1.     Cấu hình nền tảng cho Windows:
o    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy()): Chỉ dùng khi chạy trên Windows để tránh lỗi liên quan đến vòng lặp sự kiện của asyncio.
2.     Thiết lập bot Telegram:
o    TOKEN: Chứa mã thông báo (token) để xác thực với bot Telegram của bạn.
o    bot = telegram.Bot(token=TOKEN): Tạo đối tượng bot sử dụng telegram.Bot để tương tác với API Telegram.
3.     Hàm bất đồng bộ get_chat_id():
o    updates = await bot.get_updates(): Lấy danh sách các tin nhắn cập nhật (updates) từ API Telegram. Mỗi update có thể chứa các tin nhắn hoặc sự kiện khác từ người dùng gửi đến bot.
o    Kiểm tra tin nhắn:
§  Nếu không có cập nhật mới, chương trình sẽ in "Không có tin nhắn mới."
§  Nếu có tin nhắn, chương trình sẽ duyệt qua từng tin nhắn để lấy chat_id và text từ update.message. Sau đó, in chat_id và nội dung text ra màn hình.
4.     Chạy hàm get_chat_id():
o    asyncio.run(get_chat_id()): Khởi chạy hàm bất đồng bộ get_chat_id() để lấy và in các tin nhắn mới nhận được.
Lưu ý:
Hãy chắc chắn rằng bot của bạn đã nhận ít nhất một tin nhắn từ người dùng để có thể lấy chat_id.
Sau khi có chat_id, bạn có thể sử dụng nó trong mã của mình để gửi tin nhắn từ bot đến đúng người nhận hoặc nhóm chat.
 
PHẦN GIẢI THÍCH CHI TIẾT CODE CHƯƠNG TRÌNH
Phần 1: Code nhận diện cử chỉ điều khiển:
1. Thư viện Sử dụng
Giải thích
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
import config
Flask: Là một framework web  dùng để xây dựng ứng dụng web. Ở đây, Flask được sử dụng để tạo và quản lý các route và giao diện web.
cv2 (OpenCV): Thư viện xử lý ảnh và video, được sử dụng để đọc, xử lý và hiển thị video.
mediapipe: Thư viện từ Google, được sử dụng để nhận diện pose (dáng người) và cử chỉ.
numpy: Thư viện tính toán số học, đặc biệt hữu ích trong việc xử lý mảng và ma trận.
pygame: Thư viện để xử lý âm thanh và chơi nhạc, được sử dụng ở đây để phát các âm thanh cảnh báo.
FER: Thư viện nhận diện cảm xúc trong hình ảnh, dùng để nhận diện cảm xúc khuôn mặt.
PIL ( Imaging Library): Thư viện xử lý ảnh, đặc biệt trong việc vẽ chữ lên hình ảnh.
os: Thư viện để làm việc với hệ thống tập tin, như kiểm tra sự tồn tại của thư mục hoặc tạo thư mục mới.
requests: Thư viện để gửi HTTP request, dùng để điều khiển các thiết bị qua giao thức HTTP.
cvzone: Thư viện bổ trợ cho OpenCV, đặc biệt cho việc nhận diện cử chỉ tay.
YOLO (You Only Look Once): Một mô hình học sâu dùng để phát hiện đối tượng (trong trường hợp này là phát hiện lửa).
math: Thư viện toán học, được sử dụng để tính toán một số phép toán như làm tròn giá trị.
time: Thư viện xử lý thời gian, đặc biệt trong việc đánh dấu thời gian và đặt tên cho các hình ảnh lưu trữ.
telebot: Thư viện cho phép tương tác với API Telegram để gửi tin nhắn hoặc hình ảnh.
threading: Thư viện hỗ trợ xử lý đa luồng, cho phép thực hiện các tác vụ song song.
config: Một module chứa các cấu hình, chẳng hạn như địa chỉ IP của ESP (một thiết bị ngoại vi trong hệ thống).
2. Cấu hình các đối tượng và khởi tạo Flask App
Giải thích
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()
bot_token = '7837480809:AAH538Eptco2p08H_j0C_M-_86mO_teXLsM'
bot = telebot.TeleBot(bot_token)
live_stream_url = 'http://192.168.137.237:5000/'
chat_id = '-1002384540377'
fire_detected_threshold = 80
start_time = None
alert_played = False
app = Flask(__name__)
mp_pose: Khởi tạo bộ xử lý để nhận diện pose.
pose: Tạo đối tượng Pose từ MediaPipe để thực hiện nhận diện pose trên ảnh hoặc video.
bot_token: Token xác thực cho bot Telegram.
bot: Đối tượng bot Telegram được khởi tạo để gửi tin nhắn.
live_stream_url: Địa chỉ URL của stream video trực tiếp (ở đây giả định là stream từ Flask server).
chat_id: ID của chat Telegram để gửi thông báo.
fire_detected_threshold: Ngưỡng xác định lửa (ví dụ: nhận diện lửa khi độ tin cậy trên 80%).
start_time và alert_played: Biến dùng để theo dõi thời gian và trạng thái cảnh báo.
app: Khởi tạo ứng dụng Flask.
3. Lớp FallDetectionApp
Lớp này quản lý các chức năng của ứng dụng như nhận diện cử chỉ tay, phát hiện ngã, điều khiển thiết bị, và gửi cảnh báo.
Giải thích
class FallDetectionApp:
	def __init__(self):
    	pygame.mixer.init()  # Khởi tạo pygame mixer để chơi âm thanh
    	self.mp_pose = mp.solutions.pose  # Định nghĩa pose của MediaPipe
    	self.pose = self.mp_pose.Pose()  # Tạo đối tượng nhận diện pose
    	self.mp_drawing = mp.solutions.drawing_utils  # Dùng để vẽ landmarks lên ảnh
    	self.emotion_detector = FER()  # Khởi tạo detector cảm xúc
    	self.detector = HandDetector(detectionCon=0.8, maxHands=1)  # Cấu hình detector cử chỉ tay
    	self.model_fire = YOLO('fire.pt')  # Mô hình YOLO để phát hiện lửa
    	self.esp_ip = config.ESP_IP  # Địa chỉ IP của ESP
    	self.cap = cv2.VideoCapture(10)  # Khởi tạo camera, đây là chỉ số thiết bị video
    	self.camera_running = True  # Biến để kiểm soát việc bật/tắt camera
    	self.frame_count = 0  # Đếm số khung hình đã xử lý
    	self.frame_interval = 1  # Tần suất xử lý frame
    	self.drawing = False  # Biến kiểm tra nếu có vẽ vùng an toàn
    	self.start_point = None
    	self.end_point = None
    	self.safety_zones = self.load_safety_zones('safety_zones.txt')  # Đọc vùng an toàn từ file
    	self.fire_detected_time = None  # Thời gian phát hiện lửa
    	self.fire_alerted = False  # Cảnh báo lửa đã được phát
    	self.finger_control_active = True  # Kiểm tra điều khiển bằng cử chỉ tay có đang hoạt động
    	self.photo_dir = "fall_detected_photos"  # Thư mục lưu ảnh khi phát hiện ngã
    	if not os.path.exists(self.photo_dir):
        	os.makedirs(self.photo_dir)  # Tạo thư mục nếu chưa có
Phương thức trong lớp FallDetectionApp:
save_image: Lưu ảnh vào thư mục khi phát hiện sự cố như ngã hoặc lửa.
send_image_to_telegram: Gửi hình ảnh đến Telegram sau khi phát hiện sự cố.
gen_frames: Chức năng chính để lấy các khung hình từ camera, xử lý chúng (phát hiện ngã, phát hiện lửa, nhận diện cử chỉ tay) và trả về khung hình cho Flask để phát trực tuyến.
load_safety_zones: Đọc các vùng an toàn từ file và trả về danh sách các vùng.
check_safety: Kiểm tra xem vị trí (tọa độ) có nằm trong vùng an toàn hay không.
put_text: Vẽ chữ lên ảnh (chẳng hạn như "An toàn" hoặc "Nguy hiểm").
save_safety_zones: Lưu các vùng an toàn vào file.
led_control: Điều khiển đèn LED (qua ESP) dựa trên cử chỉ tay.
move_servo: Điều khiển động cơ servo qua ESP.
update_safety_zones: Cập nhật các vùng an toàn mới.
toggle_camera: Bật/tắt camera.
send_alert: Gửi cảnh báo âm thanh.
update_settings: Cập nhật cài đặt hệ thống.
4. Flask Routes
index: Trang chủ, trả về template HTML.
video_feed: Trả về stream video cho Flask client (HTML page).
toggle_camera_route: Đổi trạng thái bật/tắt camera.
get_safety_zones: Lấy danh sách các vùng an toàn.
play_alert_sound: Phát âm thanh cảnh báo.
set_safety_zone: Cài đặt vùng an toàn mới thông qua các tọa độ từ form.
5. Hàm run
def run(self):
	app.run(debug=True, host='0.0.0.0')
run: Chạy ứng dụng Flask.
6. Tạo đối tượng và chạy ứng dụng
if __name__ == '__main__':
	fall_detection_app = FallDetectionApp()
	fall_detection_app.run()
Khởi tạo đối tượng FallDetectionApp và chạy ứng dụng Flask.

Các Phân Tích Chi Tiết
1.     Nhận diện tư thế người (Pose Detection)
o    Phần này sử dụng thư viện mediapipe để phát hiện các điểm (landmarks) trên cơ thể con người trong video.
o    Các điểm cột sống và khớp cơ thể như shoulder_left, shoulder_right, hip_left, hip_right, knee_left, head.
2.     Tính toán và kiểm tra an toàn (Safety Check)
o    Kiểm tra nếu đầu (head) của người nằm trong vùng an toàn bằng cách so sánh tọa độ với các biên giới của những vùng đã được định nghĩa.
3.     Nhận diện ngã (Fall Detection)
o    Để xác định một người có bị ngã hay không, cần kiểm tra vị trí của các điểm quan trọng như vai, hông và đầu gối.
4.     Nhận diện điều khiển cử chỉ bằng tay (Hand Gesture Control)
o    Sử dụng thư viện cvzone.HandTrackingModule để nhận diện các ngón tay và cử chỉ.
5.     Nhận diện và cảnh báo cháy (Fire Detection)
o    Mô hình YOLO (You Only Look Once) được sử dụng để nhận diện các vùng có khả năng cháy với độ tin cậy nhất định.
6.     Xử lý âm thanh cảnh báo (Alert Sound)
o    Khi phát hiện một sự kiện như ngã hoặc cháy, âm thanh cảnh báo sẽ được phát bằng thư viện pygame.
7.     Hệ thống điều khiển qua Telegram
o    Sau khi phát hiện sự kiện, hình ảnh sẽ được lưu lại và gửi qua Telegram thông qua API TeleBot.

Phần 2:
Hệ Thống Điều Khiển Thiết Bị Bằng Giọng Nói
Code bạn gửi là một hệ thống điều khiển thiết bị trong nhà bằng giọng nói. Sau đây là giải thích chi tiết về các phần của mã này:
1. Thư viện và cấu hình
Giải thích
import os
import time
import requests
import speech_recognition as sr
from gtts import gTTS
import pygame
import config
os: Quản lý các thao tác với hệ điều hành, ví dụ như kiểm tra sự tồn tại của file hoặc xóa file.
time: Quản lý thời gian, ví dụ như trì hoãn chương trình hoặc đợi các sự kiện.
requests: Gửi các yêu cầu HTTP để điều khiển các thiết bị IoT (như bật/tắt đèn, quạt).
speech_recognition: Thư viện nhận diện giọng nói, cho phép chuyển đổi âm thanh thành văn bản.
gTTS: Thư viện chuyển văn bản thành giọng nói, sử dụng Google Text-to-Speech.
pygame: Dùng để phát âm thanh (feedback âm thanh sau khi nhận lệnh).
config: Chứa các cấu hình, ví dụ như địa chỉ IP của ESP (cảm biến, thiết bị IoT).
2. Các hàm điều khiển thiết bị
Giải thích
def turn_on_led1():
	requests.get(f"{esp_ip}/led1/on")
 
def turn_off_led1():
	requests.get(f"{esp_ip}/led1/off")
# Tương tự với các đèn khác, quạt và servo
Mỗi hàm sử dụng requests.get() để gửi yêu cầu HTTP đến ESP8266 (hoặc bất kỳ thiết bị IoT nào khác) để điều khiển các thiết bị như đèn, quạt hoặc servo.
3. Cung cấp phản hồi bằng âm thanh
Giải thích
def provide_feedback(message):
	print(f"Tôi rõ: {message}")
	tts = gTTS(text=message, lang='vi')
    tts.save(file_to_save)
    pygame.mixer.init()
    pygame.mixer.music.load(file_to_save)
    pygame.mixer.music.play()
	while pygame.mixer.music.get_busy(): 
        pygame.time.Clock().tick(10)
    pygame.mixer.music.stop()
    os.remove(file_to_save)
Dùng gTTS để chuyển văn bản thành giọng nói. Giọng nói này được lưu vào file .mp3 và phát lại bằng pygame. Sau khi âm thanh phát xong, file âm thanh sẽ được xóa.
4
def listen_for_command():
	recognizer = sr.Recognizer()
	with sr.Microphone() as source:
    	print("Đang nghe...")
    	recognizer.adjust_for_ambient_noise(source)
    	audio = recognizer.listen(source)
 
	try:
    	command = recognizer.recognize_google(audio, language='vi-VN').lower()
    	print(f"Đã nghe: {command}")
    	return command
	except sr.UnknownValueError:
    	print("Không nghe được lệnh.")
	except sr.RequestError:
    	print("Lỗi kết nối đến dịch vụ nhận diện giọng nói.")
    	provide_feedback("Có lỗi xảy ra khi kết nối đến dịch vụ nhận diện giọng nói.")
 
	return ""
Sử dụng speech_recognition để nghe âm thanh từ microphone và chuyển thành văn bản bằng Google Speech Recognition.
5. Xử lý lệnh
def execute_command(command):
	if 'chào' in command:
    	provide_feedback("Chào bạn! Tôi đã sẵn sàng nhận lệnh.")
	elif 'cảm ơn' in command:
    	provide_feedback("Không có gì. Tôi sẽ ngừng nhận lệnh.")
	elif 'bật đèn 1' in command:
    	turn_on_led1()
    	provide_feedback("OK, đèn 1 đã được bật.")
	# Các lệnh khác tương tự...
Dựa trên văn bản nhận diện từ giọng nói, hệ thống thực thi các hành động tương ứng.
6. Lấy thông tin nhiệt độ và độ ẩm từ ESP
def get_temperature_humidity():
	try:
    	response = requests.get(f"{esp_ip}/temperature")
    	if response.status_code == 200:
        	return response.text
    	else:
        	return "Không thể lấy dữ liệu từ cảm biến."
	except requests.RequestException:
    	return "Lỗi kết nối đến ESP8266."
Gửi yêu cầu HTTP đến ESP để lấy thông tin về nhiệt độ và độ ẩm.
7. Vòng lặp chính
def main():
	while True:
    	command = listen_for_command()
    	if command:
        	execute_command(command)
Chạy vòng lặp liên tục, lắng nghe các lệnh giọng nói và thực thi các lệnh này nếu có.
8. Kiểm tra điều kiện khi bắt đầu chương trình
Copyif __name__ == "__main__":
	main()
Đảm bảo rằng main() chỉ chạy khi script được chạy trực tiếp, không phải khi module được nhập vào từ nơi khác.

Tổng Kết
Phần cứng: ESP8266 hoặc thiết bị IoT khác điều khiển các thiết bị (đèn, quạt, servo).
Giọng nói: Hệ thống sử dụng speech_recognition để nhận diện các lệnh giọng nói từ người dùng và thực thi các hành động điều khiển thiết bị.
Phản hồi: Sau khi nhận lệnh và thực thi, hệ thống cung cấp phản hồi bằng giọng nói thông qua gTTS và phát lại qua pygame.
Điều khiển từ xa: Các yêu cầu HTTP được gửi từ máy tính đến ESP để điều khiển thiết bị (bật/tắt đèn, quạt, kiểm tra nhiệt độ).

Phần 3: Điều Khiển LED và Cảm Biến qua Bot Telegram
1.     Cấu hình Bot Telegram:
o	Đoạn mã sử dụng thư viện telebot để tạo một bot Telegram. Bot này nhận lệnh từ người dùng qua tin nhắn và thực hiện các hành động điều khiển thiết bị (như bật/tắt đèn, điều khiển servo, quạt,...) dựa trên các lệnh nhận được.
o	bot_token là token của bot, dùng để nhận và gửi tin nhắn qua API Telegram.
o	chat_id là ID của nhóm hoặc cá nhân mà bot sẽ gửi tin nhắn.
2.     Điều khiển Servo và Cảm biến Nhiệt Độ và Độ ẩm:
o	move_servo(angle): Hàm này điều khiển servo qua ESP8266 bằng cách gửi yêu cầu HTTP để thay đổi góc servo (từ 0 đến 180 độ).
o	get_temperature_humidity(): Hàm này gửi yêu cầu HTTP tới ESP8266 để lấy dữ liệu cảm biến nhiệt độ và độ ẩm. Nếu thành công, nó trả về dữ liệu từ cảm biến.
3.     Phản hồi qua Bot Telegram:
o	provide_feedback(message): Hàm gửi phản hồi về kết quả của lệnh điều khiển (ví dụ: "LED 1 đã bật", "Quạt đã tắt",...).
4.     Xử lý lệnh điều khiển thiết bị qua Bot:
o	handle_device_control(command, chat_id): Nhận lệnh từ người dùng qua tin nhắn Telegram, sau đó điều khiển các thiết bị tương ứng (bật/tắt đèn, quạt, servo, hoặc gửi liên kết video stream từ camera).
o	Các lệnh như '1', '2', '3' dùng để bật/tắt LED, '4', '04' dùng để điều khiển servo (mở/đóng cửa), '5', '05' để bật/tắt quạt.
5.     Chạy Bot:
o	bot.message_handler(func=lambda message: True): Hàm này là nơi bot nhận và xử lý mọi tin nhắn gửi đến. Sau khi nhận được lệnh từ người dùng, bot sẽ gọi handle_device_control() để thực hiện.
6.     Chạy Bot:
o	bot.polling(none_stop=True): Bot sẽ tiếp tục chạy và lắng nghe tin nhắn từ người dùng.
Phần 4: Cài Đặt và Cập Nhật Vị Trí (Phát hiện ngã với khu vực an toàn)
1.     Cấu hình Video Stream và Webcam:
o	cv2.VideoCapture(10): Dùng OpenCV để mở webcam hoặc camera IP. Dòng lệnh này mở webcam và lấy dữ liệu video từ đó.
o	rtsp_url: Cấu hình cho việc truyền trực tiếp video từ camera IP, nếu sử dụng RTSP.
2.     Vẽ Khu Vực An Toàn:
o	Trong phương thức draw_rectangle, người dùng có thể vẽ một hình chữ nhật để xác định khu vực an toàn trên màn hình. Khi người dùng nhấn chuột, hệ thống sẽ bắt đầu vẽ một hình chữ nhật, và khi nhả chuột, khu vực đó sẽ được lưu lại.
3.     Lưu và Tải Khu Vực An Toàn:
o	save_safety_zone và save_safety_zones: Lưu thông tin các khu vực an toàn vào một tệp văn bản. Mỗi khu vực an toàn được lưu dưới dạng tọa độ của hai góc đối diện.
o	load_safety_zones: Hàm này đọc dữ liệu từ tệp và khôi phục lại các khu vực an toàn khi ứng dụng khởi động lại.
4.     Hiển Thị Khu Vực An Toàn:
o	Trong phương thức gen_frames, video từ webcam sẽ được hiển thị, đồng thời các khu vực an toàn đã được xác định sẽ được vẽ lên màn hình (màu sắc là màu vàng).
o	Nếu người dùng đang vẽ một khu vực an toàn, nó sẽ hiển thị trên màn hình với màu xanh lá cây.
5.     Dừng ứng dụng:
o	Khi người dùng nhấn phím 'q', ứng dụng sẽ dừng lại và đóng tất cả các cửa sổ hiển thị OpenCV.
 
Phần 5 Cảnh báo té ngã trong nhà vệ sinh
1. Cài đặt ban đầu
import cv2
import mediapipe as mp
import numpy as np
import pygame
import telebot
from datetime import datetime
import os
cv2: Thư viện OpenCV để xử lý video và hình ảnh.
mediapipe: Thư viện của Google để xử lý và nhận diện các tư thế cơ thể.
numpy: Thư viện tính toán số học cho các phép toán ma trận, ví dụ như tính toán góc.
pygame: Dùng để phát âm thanh khi phát hiện té ngã.
telebot: Dùng để gửi thông báo qua Telegram khi phát hiện té ngã.
datetime: Lấy thời gian hiện tại để đặt tên cho ảnh.
os: Quản lý các thư mục và tệp tin.
2. Khởi tạo MediaPipe và các công cụ
 
 
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
pose = mp_pose.Pose()
pygame.mixer.init()
fall_sound = pygame.mixer.Sound("fall_sound.wav")
bot_token = '7837480809:AAH538Eptco2p08H_j0C_M-_86mO_teXLsM'
bot = telebot.TeleBot(bot_token)
chat_id = '-1002384540377'
output_folder = "fall_detected_photos"
os.makedirs(output_folder, exist_ok=True)
mp_pose.Pose(): Khởi tạo đối tượng Pose của MediaPipe để theo dõi và nhận diện tư thế cơ thể.
pygame.mixer.init(): Khởi tạo hệ thống âm thanh của pygame để phát âm thanh khi té ngã.
fall_sound: Tải tệp âm thanh cảnh báo khi phát hiện té ngã.
bot_token và bot: Khởi tạo bot Telegram để gửi thông báo.
chat_id: ID của nhóm hoặc người nhận thông báo.
output_folder: Thư mục lưu trữ ảnh khi phát hiện té ngã.
3. Mở camera
 
 
cap = cv2.VideoCapture(1)
cv2.VideoCapture(1): Mở camera (thường là camera thứ hai trong hệ thống).
4. Hàm gửi cảnh báo té ngã qua Telegram
def send_fall_alert(image_path):
	with open(image_path, 'rb') as photo:
        bot.send_photo(chat_id, photo)
send_fall_alert(image_path): Hàm gửi ảnh qua Telegram khi phát hiện té ngã.
Ảnh được mở bằng open() trong chế độ nhị phân ('rb').
Sử dụng phương thức send_photo của telebot để gửi ảnh.
5. Hàm phát hiện té ngã
def detect_fall(landmarks):
    shoulder_left = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
    shoulder_right = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]
	hip_left = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
	hip_right = landmarks[mp_pose.PoseLandmark.RIGHT_HIP]
	nose = landmarks[mp_pose.PoseLandmark.NOSE]
	shoulder_y = (shoulder_left.y + shoulder_right.y) / 2
	hip_y = (hip_left.y + hip_right.y) / 2
	torso_angle = np.arctan2(hip_y - shoulder_y, hip_right.x - shoulder_left.x) * 180 / np.pi
	if abs(shoulder_y - hip_y) < 0.15 and abs(torso_angle) < 30:
    	return True
	return False
detect_fall(landmarks): Phát hiện té ngã dựa vào các điểm đặc trưng của cơ thể (được lấy từ landmarks).
shoulder_left, shoulder_right, hip_left, hip_right, nose: Các điểm trên cơ thể được xác định bởi MediaPipe Pose (vai, hông, mũi).
shoulder_y và hip_y: Tính toán vị trí trung bình của vai và hông.
torso_angle: Tính toán góc của thân người dựa trên vị trí của vai và hông.
Nếu shoulder_y và hip_y cách nhau dưới 0.15 và torso_angle nhỏ hơn 30 độ, hệ thống cho rằng người dùng đang trong tình trạng té ngã.
6. Vòng lặp chính để nhận diện và phát hiện té ngã
fall_detected_frames = 0
fall_confirmation_frames = 5
 
while cap.isOpened():
	ret, frame = cap.read()
	if not ret:
    	break
 
	rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
	results = pose.process(rgb_frame)
 
    skeleton_frame = np.zeros_like(frame)
 
	if results.pose_landmarks:
        mp_drawing.draw_landmarks(
            skeleton_frame,
            results.pose_landmarks,
            mp_pose.POSE_CONNECTIONS,
            mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=3)
    	)
    	if detect_fall(results.pose_landmarks.landmark):
            fall_detected_frames += 1
    	else:
            fall_detected_frames = 0
    	if fall_detected_frames >= fall_confirmation_frames:
            fall_sound.play()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            skeleton_image_path = os.path.join(output_folder, f"skeleton_fall_detected_{timestamp}.jpg")
            cv2.imwrite(skeleton_image_path, skeleton_frame)
            send_fall_alert(skeleton_image_path)
            fall_detected_frames = 0 
 
    cv2.imshow("OUT DETCTED", skeleton_frame)
 
	if cv2.waitKey(1) & 0xFF == ord('q'):
    	break
 
cap.release()
fall_detected_frames: Đếm số frame liên tiếp phát hiện té ngã.
fall_confirmation_frames: Số frame cần phát hiện té ngã liên tiếp để xác nhận là té ngã thật sự.
results.pose_landmarks: Lấy các điểm tư thế cơ thể từ MediaPipe.
mp_drawing.draw_landmarks(): Vẽ các điểm tư thế cơ thể lên hình ảnh.
detect_fall(): Kiểm tra nếu người dùng đang té ngã.
Nếu phát hiện té ngã trong fall_confirmation_frames frame, hệ thống sẽ phát âm thanh cảnh báo, lưu ảnh và gửi ảnh qua Telegram.
cv2.imshow(): Hiển thị video với các điểm tư thế cơ thể.
cv2.waitKey(1): Đợi người dùng nhấn 'q' để thoát khỏi vòng lặp.
Tóm tắt:
Hệ thống sử dụng camera để theo dõi người dùng trong nhà vệ sinh, nhận diện các điểm cơ thể và tính toán các chỉ số như góc của thân người.
Nếu người dùng té ngã (theo các chỉ số này), hệ thống sẽ phát âm thanh cảnh báo và gửi ảnh qua Telegram.
Sau khi xác nhận té ngã trong một số frame liên tiếp, hệ thống sẽ gửi thông báo và hình ảnh té ngã qua Telegram.


 Phần 6: Hàm Dùng để tạo luồng qua địa chỉ ip vs file là config.py
Định nghĩa địa chỉ IP của ESP:
ESP_IP = 'http://192.168.137.66': Đây là địa chỉ IP của ESP trong mạng, giúp các chương trình khác liên lạc với nó khi cần.
Phần 7: Phân ra 4 luồng để chạy các file. Nghĩa là 1 file sẽ chạy 1 luồng hàm này tương ứng với hàm main toàn chương trình
  Hàm run_file1, run_file2, run_file3, run_file4:
Mỗi hàm dùng subprocess.run() để chạy một tệp  riêng:
run_file1(): Chạy tệp telegram call image.py để gọi tính năng gọi và gửi hình ảnh qua Telegram.
run_file2(): Chạy tệp control led và nhiệt độ.py để điều khiển LED và đọc nhiệt độ từ các thiết bị.
run_file3(): Chạy tệp voiceweb.py để thực hiện chức năng điều khiển bằng giọng nói và quản lý giao diện web.
run_file4(): Chạy tệp wc.py để quản lý các chức năng liên quan đến phát hiện té ngã hoặc giám sát khu vực vệ sinh.
Khởi tạo các luồng (threads):
Mỗi tệp sẽ chạy trong một luồng riêng, cho phép các chương trình hoạt động đồng thời mà không phải chờ đợi lẫn nhau.
Các luồng được tạo với:
thread1 = threading.Thread(target=run_file1)
thread2 = threading.Thread(target=run_file2)
thread3 = threading.Thread(target=run_file3)
thread4 = threading.Thread(target=run_file4)
Bắt đầu và đợi các luồng hoàn thành:
start(): Bắt đầu từng luồng, khiến các tệp  chạy song song.
join(): Đợi cho đến khi các luồng hoàn thành trước khi tiếp tục (hoặc kết thúc) chương trình chính.
Phần 8: Phát hiện người lạ.
 1. Cấu hình Telegram
TELEGRAM_TOKEN = '7837480809:AAH538Eptco2p08H_j0C_M-_86mO_teXLsM'
CHAT_ID = '-1002384540377'
TELEGRAM_TOKEN: Đây là mã token của bot Telegram, dùng để xác thực bot khi gửi tin nhắn.
CHAT_ID: ID của nhóm hoặc người nhận tin nhắn trên Telegram. Tin nhắn sẽ được gửi đến chat này.
2. Hàm gửi ảnh qua Telegram
def send_telegram_photo(photo_path):
	url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
	with open(photo_path, 'rb') as photo_file:
    	params = {
        	'chat_id': CHAT_ID,
    	}
    	response = requests.post(url, params=params, files={'photo': photo_file})
	return response
send_telegram_photo(photo_path): Hàm này dùng để gửi ảnh qua Telegram.
photo_path: Đường dẫn đến ảnh cần gửi.
requests.post(): Gửi ảnh qua API của Telegram. Ảnh sẽ được mở bằng open() dưới chế độ nhị phân ('rb').
params chứa chat_id (địa chỉ nhận tin nhắn).
files là tham số chứa ảnh cần gửi.
3. Tải và xử lý các ảnh khuôn mặt đã biết
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
known_faces = []
known_face_names = []
 
path = 'training'
for filename in os.listdir(path):
	if filename.endswith('.jpg') or filename.endswith('.png'):
    	image_path = os.path.join(path, filename)
    	image = cv2.imread(image_path)
    	gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    	faces = face_cascade.detectMultiScale(gray, 1.1, 4)
 
    	for (x, y, w, h) in faces:
        	face_roi = gray[y:y+h, x:x+w]
        	known_faces.append(face_roi)
        	name = os.path.splitext(filename)[0]
        	known_face_names.append(name)
face_cascade: Tải mô hình phát hiện khuôn mặt Haar Cascade để nhận diện khuôn mặt trong ảnh.
known_faces: Danh sách lưu các khuôn mặt đã biết dưới dạng mảng ảnh grayscale.
known_face_names: Danh sách lưu tên tương ứng của các khuôn mặt đã biết.
path = 'training': Đọc ảnh từ thư mục training.
os.listdir(path): Duyệt qua tất cả các tệp trong thư mục training.
cv2.imread(): Đọc ảnh từ đĩa.
cv2.cvtColor(): Chuyển ảnh sang grayscale để việc nhận diện khuôn mặt dễ dàng hơn.
face_cascade.detectMultiScale(): Phát hiện khuôn mặt trong ảnh.
4. Mở camera và nhận diện khuôn mặt trong video
video_capture = cv2.VideoCapture(0)
 
while True:
	ret, frame = video_capture.read()
	gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
 
	faces = face_cascade.detectMultiScale(gray_frame, 1.1, 4)
 
	for (x, y, w, h) in faces:
    	face_roi = gray_frame[y:y+h, x:x+w]
    	name = "Unknown"
    	for i, known_face in enumerate(known_faces):
        	result = cv2.compareHist(
            	cv2.calcHist([face_roi], [0], None, [256], [0, 256]),
            	cv2.calcHist([known_face], [0], None, [256], [0, 256]),
            	cv2.HISTCMP_CORREL
        	)
        	if result > 0.2:
            	name = known_face_names[i]
            	ak
video_capture = cv2.VideoCapture(0): Mở camera để nhận diện khuôn mặt trong thời gian thực.
ret, frame = video_capture.read(): Đọc mỗi frame từ camera.
cv2.cvtColor(): Chuyển đổi frame sang grayscale.
face_cascade.detectMultiScale(): Phát hiện khuôn mặt trong mỗi frame.
cv2.compareHist(): So sánh các histogram giữa khuôn mặt phát hiện được và các khuôn mặt đã biết để nhận diện khuôn mặt. Nếu sự tương đồng lớn hơn 0.2, đó là khuôn mặt đã biết.
5. Chụp ảnh và gửi qua Telegram nếu không nhận diện được khuôn mặt
if name == "Unknown":
	timestamp = time.strftime("%Y%m%d-%H%M%S")
	screenshot_path = f"unknown_face_{timestamp}.jpg"
	cv2.imwrite(screenshot_path, frame) 
	send_telegram_photo(screenshot_path)
	os.remove(screenshot_path) 
if name == "Unknown":: Nếu không nhận diện được khuôn mặt (tên là "Unknown"), hệ thống sẽ chụp ảnh và gửi ảnh đó qua Telegram.
time.strftime(): Lấy thời gian hiện tại để tạo tên ảnh.
cv2.imwrite(): Lưu ảnh chụp vào tệp.
send_telegram_photo(): Gửi ảnh qua Telegram.
os.remove(): Xóa ảnh tạm sau khi đã gửi.
6. Vẽ hình chữ nhật và hiển thị tên khuôn mặt
cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
cv2.putText(frame, name, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
cv2.rectangle(): Vẽ một hình chữ nhật quanh khuôn mặt trong mỗi frame.
cv2.putText(): Hiển thị tên khuôn mặt (hoặc "Unknown" nếu không nhận diện được).
7. Hiển thị video và dừng khi nhấn 'q'
cv2.imshow('Video', frame)
if cv2.waitKey(1) & 0xFF == ord('q'):
	break
cv2.imshow(): Hiển thị video trong cửa sổ.
cv2.waitKey(1): Chờ người dùng nhấn phím. Nếu phím 'q' được nhấn, vòng lặp sẽ dừng lại.
8. Giải phóng tài nguyên khi kết thúc
 
 
video_capture.release()
cv2.destroyAllWindows()
video_capture.release(): Giải phóng tài nguyên camera.
cv2.destroyAllWindows(): Đóng tất cả các cửa sổ OpenCV.
Phần 9: Chụp nhận diện khuôn mặt.
1. Tạo thư mục lưu ảnh
 
 
output_dir = 'training'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)
output_dir = 'training': Đặt tên thư mục lưu ảnh là training.
os.makedirs(output_dir): Kiểm tra xem thư mục này có tồn tại hay không. Nếu không, thư mục training sẽ được tạo ra.
2. Khởi tạo camera
 
 
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Cannot open camera")
	exit()
cap = cv2.VideoCapture(0): Mở camera với chỉ số 0 (thường là camera mặc định của máy tính).
cap.isOpened(): Kiểm tra xem camera có mở thành công không. Nếu không, sẽ in ra thông báo lỗi và kết thúc chương trình bằng exit().
3. Các biến cần thiết
 
 
capture_interval = 2
frame_count = 0
capture_interval = 2: Đặt thời gian chờ giữa mỗi lần chụp ảnh là 2 giây.
frame_count = 0: Khởi tạo biến đếm số lượng ảnh đã chụp.
4. Vòng lặp chụp ảnh
 
 
while True:
	ret, frame = cap.read()
	if not ret:
        print("Khong doc duoc ...")
    	break
    cv2.imshow('frame', frame)
	frame_count += 1
	img_path = os.path.join(output_dir, f'Que Tran_{frame_count:04d}.jpg')
    cv2.imwrite(img_path, frame)
    print(f"Saved {img_path}")
    time.sleep(capture_interval)
	if cv2.waitKey(1) == ord('q'):
    	break
while True:: Bắt đầu vòng lặp vô hạn để liên tục lấy ảnh từ camera.
ret, frame = cap.read(): Đọc một frame từ camera. Nếu không thể đọc, chương trình sẽ in thông báo lỗi và dừng lại.
cv2.imshow('frame', frame): Hiển thị ảnh vừa chụp trong một cửa sổ tên là 'frame'.
frame_count += 1: Tăng số đếm frame lên 1 mỗi khi chụp ảnh.
img_path = os.path.join(output_dir, f'Que Tran_{frame_count:04d}.jpg'): Đặt đường dẫn để lưu ảnh, tên ảnh sẽ theo định dạng Que Tran_XXXX.jpg, với XXXX là số thứ tự của ảnh (được định dạng 4 chữ số).
cv2.imwrite(img_path, frame): Lưu ảnh vào đường dẫn đã định.
print(f"Saved {img_path}"): In ra thông báo đã lưu ảnh tại đường dẫn này.
time.sleep(capture_interval): Tạm dừng chương trình trong 2 giây (theo giá trị capture_interval) giữa mỗi lần chụp ảnh.
if cv2.waitKey(1) == ord('q'):: Kiểm tra xem người dùng có nhấn phím q không. Nếu có, vòng lặp sẽ dừng lại.
5. Dọn dẹp tài nguyên khi kết thúc
 
 
finally:
    cap.release()
    cv2.destroyAllWindows()
cap.release(): Giải phóng tài nguyên của camera khi chương trình kết thúc.
cv2.destroyAllWindows(): Đóng tất cả cửa sổ OpenCV khi chương trình kết thúc.
Tóm lại:
Đoạn mã này sẽ:
1.     Mở camera.
2.     Chụp ảnh mỗi 2 giây và lưu ảnh vào thư mục training với tên là Que Tran_XXXX.jpg.
3.     Hiển thị ảnh đang được chụp trên cửa sổ frame.
4.     Dừng chụp khi người dùng nhấn phím q.
5.     Giải phóng tài nguyên khi kết thúc.
Chương trình này có thể hữu ích để thu thập dữ liệu hình ảnh cho các dự án học máy hoặc nhận dạng đối tượng.
 
Phần 10: Nhắc hẹn
1. Lớp ReminderSystem
Lớp này có vai trò quản lý và thực hiện các nhắc nhở trong hệ thống.
Thuộc tính self.reminders: Lưu trữ các nhắc nhở. Mỗi nhắc nhở sẽ có thời gian (dạng "HH
"), thông điệp và một cờ repeat cho biết liệu nhắc nhở có được lặp lại vào ngày hôm sau hay không.
2. Các phương thức trong ReminderSystem
add_reminder(time_str, message, repeat=False): Thêm một nhắc nhở vào từ điển self.reminders với thời gian, thông điệp và cờ repeat (mặc định là False).
show_reminders(): Hiển thị tất cả các nhắc nhở đã thêm.
speak_message(message): Dùng gTTS để chuyển văn bản thành giọng nói và phát thông báo qua loa.
check_reminders(): Kiểm tra nhắc nhở mỗi phút. Nếu thời gian hiện tại khớp với một nhắc nhở, hệ thống sẽ thông báo và hỏi người dùng có muốn lặp lại nhắc nhở vào ngày hôm sau không.
ask_for_repeat(message): Hỏi người dùng có muốn lặp lại nhắc nhở vào ngày hôm sau.
wait_for_reminder_time(): Chờ đến giờ nhắc nhở và thoát khỏi lắng nghe lệnh mới khi nhắc nhở đến giờ.
schedule_repeat(message): Lên lịch để lặp lại nhắc nhở vào ngày hôm sau.
start_reminder_check(): Bắt đầu kiểm tra nhắc nhở trong một luồng riêng biệt.
listen_for_commands(): Lắng nghe các lệnh giọng nói từ người dùng. Nếu người dùng nói "nhắc hẹn", hệ thống sẽ yêu cầu người dùng cung cấp thời gian và thông điệp nhắc nhở.
listen_for_reminder_details(): Lắng nghe chi tiết về thời gian và thông điệp nhắc nhở từ giọng nói, sau đó thêm nhắc nhở vào hệ thống.
3. Sử dụng thư viện ngoài
speech_recognition: Dùng để nhận diện giọng nói của người dùng.
playsound: Phát âm thanh nhắc nhở bằng giọng nói.
gTTS: Chuyển văn bản thành giọng nói (Text-to-Speech).
os: Quản lý các tệp, ví dụ như xóa tệp âm thanh sau khi phát.
4. Quy trình hoạt động
Bước 1: Khi chương trình khởi chạy, phương thức start_reminder_check() sẽ được gọi trong một luồng riêng biệt để kiểm tra các nhắc nhở mỗi phút.
Bước 2: Phương thức listen_for_commands() sẽ liên tục lắng nghe lệnh giọng nói từ người dùng. Khi người dùng nói "nhắc hẹn", hệ thống sẽ yêu cầu họ cung cấp chi tiết nhắc nhở.
Bước 3: Khi người dùng cung cấp thời gian và thông điệp, phương thức add_reminder() sẽ thêm nhắc nhở vào hệ thống.
Bước 4: Nếu thời gian của một nhắc nhở khớp với thời gian thực, hệ thống sẽ phát thông báo và hỏi người dùng có muốn lặp lại nhắc nhở vào ngày hôm sau.
Bước 5: Các nhắc nhở sẽ được lặp lại nếu người dùng chọn "có" khi hỏi về việc lặp lại.
5. Chạy chương trình
Sau khi khởi tạo đối tượng ReminderSystem, phương thức start_reminder_check() sẽ bắt đầu kiểm tra nhắc nhở trong một luồng riêng, trong khi phương thức listen_for_commands() lắng nghe các lệnh giọng nói.
6. Vấn đề tiềm ẩn
Tiếng ồn xung quanh: Hệ thống có thể gặp khó khăn trong việc nhận diện giọng nói nếu có quá nhiều tiếng ồn.
Định dạng thời gian: Người dùng cần phải nói thời gian đúng định dạng (ví dụ: "23 giờ 15"). Nếu không, chương trình có thể không nhận diện được.
Phần 11: Xử lí bàn tay:
1.     Thông tin cơ bản về gói:
o	name='cvzone': Tên của gói là cvzone.
o	packages=['cvzone']: Danh sách các gói  cần bao gồm. Ở đây, chỉ có một gói là cvzone.
o	version='1.6': Phiên bản của gói là 1.6.
o	license='MIT': Gói này sử dụng giấy phép MIT, cho phép sử dụng mã nguồn mở với ít hạn chế.
2.     Mô tả và thông tin tác giả:
o	description='Computer Vision Helping Library': Mô tả ngắn gọn về gói, nêu rõ đây là một thư viện hỗ trợ về Thị giác máy tính.
o	author='Computer Vision Zone': Tên tác giả hoặc tổ chức phát triển gói.
o	author_email='contact@computervision.zone': Email liên hệ của tác giả hoặc tổ chức phát triển.
o	url='https://github.com/cvzone/cvzone.git': URL đến kho lưu trữ mã nguồn trên GitHub.
3.     Keywords và yêu cầu cài đặt:
o	keywords=['ComputerVision', 'HandTracking', 'FaceTracking', 'PoseEstimation']: Từ khóa giúp người dùng tìm thấy gói khi tìm kiếm.
o	install_requires=[ 'opencv-', 'numpy']: Liệt kê các gói phụ thuộc cần được cài đặt cùng với gói cvzone. Ở đây, gói yêu cầu opencv- và numpy.
o	_requires='>=3.6': Gói yêu cầu  phiên bản 3.6 hoặc cao hơn.
4.     Phân loại (classifiers):
o	Development Status :: 3 - Alpha: Trạng thái phát triển là Alpha, cho thấy gói đang ở giai đoạn thử nghiệm.
o	Intended Audience :: Developers: Đối tượng sử dụng chính là các nhà phát triển.
o	Topic :: Software Development :: Build Tools: Chủ đề của gói là phát triển phần mềm, công cụ xây dựng.
o	License :: OSI Approved :: MIT License: Xác nhận gói được cấp phép MIT.
o	Programming Language ::  :: 3: Gói hỗ trợ  3.
Tóm tắt:
File setup.py này cấu hình để người dùng có thể dễ dàng cài đặt gói cvzone và các phụ thuộc liên quan bằng lệnh pip install cvzone.
Phần 12: Web
 1. Phần head
Cấu trúc tài liệu HTML5: Tài liệu bắt đầu bằng <!DOCTYPE html>, định nghĩa cấu trúc tài liệu là HTML5.
Metadata và CSS:
<meta charset="UTF-8">: Thiết lập mã hóa ký tự UTF-8.
<meta name="viewport" content="width=device-width, initial-scale=1.0">: Tạo responsive cho trang web bằng cách tối ưu hiển thị trên các thiết bị.
<title>Camera AI Home</title>: Tiêu đề của trang.
CSS: Định dạng giao diện của trang.
body: Định dạng nền trắng và font chữ Arial.
#header: Header với nền trắng, màu chữ xám đậm, canh giữa và padding.
#video-container: Đặt video ở giữa trang, bo tròn góc, đổ bóng, và có thể thay đổi kích thước để phù hợp với các thiết bị khác nhau.
#overlay và .notification: #overlay cho phép thêm overlay trên video, và .notification định dạng thông báo.
Watermark: #watermark-top và #watermark-bottom cho phép thêm các đoạn văn bản hoặc ảnh làm watermark ở đầu và cuối của khung video.
Button: .button-container căn giữa các nút, và .button định dạng cho các nút điều khiển với màu xanh dương và hiệu ứng hover.
2. Phần body
Video Feed:
html
 
<img id="video" src="{{ url_for('video_feed') }}" alt="Video Feed">
id="video": Tạo một khung để hiển thị video trực tiếp từ camera.
src="{{ url_for('video_feed') }}": Đường dẫn đến luồng video được cung cấp bởi Flask (ví dụ: qua một endpoint /video_feed).
Nút điều khiển:
html
 
<div class="button-container">
	<button class="button" onclick="toggleCamera()">Start/Stop Camera</button>
</div>
Nút Start/Stop Camera để bật hoặc tắt camera bằng cách gọi hàm JavaScript toggleCamera().
3. Phần script
toggleCamera():
javascript
 
function toggleCamera() {
    fetch('/toggle_camera', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            alert(data.message);
    	});
}
Chức năng: Gửi yêu cầu POST đến server (endpoint /toggle_camera) để bật/tắt camera.
Phản hồi: Hiển thị thông báo dựa trên data.message từ phản hồi JSON.
sendAlert():
javascript
 
function sendAlert() {
	fetch('/send_alert', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            alert(data.message);
    	});
}
Chức năng: Gửi yêu cầu POST đến /send_alert để gửi thông báo đến người dùng hoặc hệ thống.
Phản hồi: Hiển thị thông báo sau khi gửi thành công.
updateSettings():
javascript
 
function updateSettings() {
	const settings = { example: 'value' };
    fetch('/update_settings', {
    	method: 'POST',
    	headers: {
            'Content-Type': 'application/json'
    	},
    	body: JSON.stringify(settings)
	})
    .then(response => response.json())
	.then(data => {
        alert(data.message);
	});
}
Chức năng: Cập nhật cài đặt hệ thống bằng cách gửi dữ liệu JSON đến endpoint /update_settings.
Cài đặt: Dữ liệu được gửi dưới dạng JSON. Ví dụ trong mã, settings chứa { example: 'value' }, nhưng có thể chỉnh sửa thành dữ liệu thực tế.
Phản hồi: Hiển thị thông báo xác nhận cập nhật.
4. Responsive Design
@media (max-width: 600px): Tạo giao diện tương thích với màn hình nhỏ hơn 600px (thường là trên thiết bị di động).
Các thành phần như font chữ, kích thước ảnh và nút điều khiển được điều chỉnh để phù hợp với màn hình nhỏ hơn.
Tóm tắt:
Giao diện này hiển thị video từ camera AI và có các nút để điều khiển camera, gửi cảnh báo và cập nhật cài đặt.
Có thể tương tác với Flask backend thông qua JavaScript để bật/tắt camera, gửi cảnh báo và cập nhật cài đặt.
Giao diện này có khả năng tự điều chỉnh để phù hợp với các thiết bị khác nhau, từ máy tính đến điện thoại di động.
 
 
Phần 13 : ESP và phần cứng.
1. Kết nối Wi-Fi
ESP8266 kết nối với Wi-Fi sử dụng thông tin mạng được cung cấp trong ssid và password.
2. Cấu hình phần cứng
Cảm biến chuyển động (PIR): Được kết nối với chân D0 (PIR_PIN), phát hiện chuyển động.
Cảm biến nhiệt độ và độ ẩm (DHT11): Được kết nối với chân D6 (DHTPIN), sử dụng thư viện DHT để đo nhiệt độ và độ ẩm.
Cảm biến khí (MQ135): Kết nối với chân A0 để đo nồng độ khí độc, khói.
Servo motor: Được kết nối với chân D4 để điều khiển cửa (mở hoặc đóng).
Cảm biến mưa: Kết nối với chân D7 (rainSensorPin), phát hiện mưa.
Buzzer và đèn LED: Kết nối với các chân D9, D1, D2, D3, D4, D5, D8 để điều khiển các thiết bị ngoại vi như đèn và còi báo động.
3. Gửi thông báo qua Telegram
Telegram Bot: Được sử dụng để gửi thông báo khi phát hiện khí độc hoặc mưa. Token bot và chat ID được khai báo để gửi thông báo đến một nhóm hoặc cá nhân trên Telegram.
4. Web Server (ESP8266WebServer)
ESP8266WebServer: Server web chạy trên ESP8266 để nhận các lệnh điều khiển từ thiết bị khác thông qua HTTP. Các lệnh này có thể bật hoặc tắt các thiết bị (LED, quạt, servo) hoặc nhận thông tin từ cảm biến nhiệt độ, độ ẩm, khí độc.
/led1/on: Bật LED 1
/led1/off: Tắt LED 1
/fan3/on: Bật quạt 3
/servo/180: Mở cửa (servo motor)
/temperature: Lấy thông tin nhiệt độ và độ ẩm
/gas: Lấy thông tin về nồng độ khí và khói
5. Các hàm và xử lý trong loop()
Cảm biến chuyển động: Khi phát hiện chuyển động, bật LED 5 và gửi tín hiệu.
Cảm biến khí (MQ135): Đọc giá trị nồng độ khí gas và khói, nếu vượt quá ngưỡng, sẽ gửi thông báo qua Telegram và bật còi báo động.
Cảm biến mưa: Nếu có mưa, sẽ đóng cửa bằng servo và gửi thông báo.
6. Gửi thông báo qua Telegram
Sử dụng hàm sendTelegramMessage() để gửi thông báo đến nhóm/chat Telegram khi phát hiện khí độc hoặc mưa.
Các hành động xảy ra trong mã:
Cảm biến khí MQ135: Đo nồng độ khí và khói, nếu nồng độ vượt quá ngưỡng thì kích hoạt báo động.
Cảm biến mưa: Nếu có mưa, đóng cửa (servo quay về 0 độ) và gửi thông báo.
Cảm biến chuyển động PIR: Khi phát hiện chuyển động, bật đèn LED 5.
Đọc nhiệt độ và độ ẩm: Mỗi giây, mã sẽ đo và in ra thông số nhiệt độ và độ ẩm từ cảm biến DHT11.
Các điều kiện cảnh báo:
1.     Khí độc hoặc khói (ppmGas > 20): Khi có khí độc hoặc khói, báo động và gửi thông báo qua Telegram.
2.     Phát hiện mưa: Đóng cửa và gửi thông báo mưa qua Telegram.
 
Phần 14: Code nhận id đến telegram
1.     Cấu hình nền tảng cho Windows:
o    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy()): Chỉ dùng khi chạy trên Windows để tránh lỗi liên quan đến vòng lặp sự kiện của asyncio.
2.     Thiết lập bot Telegram:
o    TOKEN: Chứa mã thông báo (token) để xác thực với bot Telegram của bạn.
o    bot = telegram.Bot(token=TOKEN): Tạo đối tượng bot sử dụng telegram.Bot để tương tác với API Telegram.
3.     Hàm bất đồng bộ get_chat_id():
o    updates = await bot.get_updates(): Lấy danh sách các tin nhắn cập nhật (updates) từ API Telegram. Mỗi update có thể chứa các tin nhắn hoặc sự kiện khác từ người dùng gửi đến bot.
o    Kiểm tra tin nhắn:
§  Nếu không có cập nhật mới, chương trình sẽ in "Không có tin nhắn mới."
§  Nếu có tin nhắn, chương trình sẽ duyệt qua từng tin nhắn để lấy chat_id và text từ update.message. Sau đó, in chat_id và nội dung text ra màn hình.
4.     Chạy hàm get_chat_id():
o    asyncio.run(get_chat_id()): Khởi chạy hàm bất đồng bộ get_chat_id() để lấy và in các tin nhắn mới nhận được.
Lưu ý:
Hãy chắc chắn rằng bot của bạn đã nhận ít nhất một tin nhắn từ người dùng để có thể lấy chat_id.
Sau khi có chat_id, bạn có thể sử dụng nó trong mã của mình để gửi tin nhắn từ bot đến đúng người nhận hoặc nhóm chat.
 
PHẦN GIẢI THÍCH CHI TIẾT CODE CHƯƠNG TRÌNH
Phần 1: Code nhận diện cử chỉ điều khiển:
1. Thư viện Sử dụng
Giải thích
from flask import Flask, Response, render_template, request, jsonify
import cvPHẦN GIẢI THÍCH CHI TIẾT CODE CHƯƠNG TRÌNH
Phần 1: Code nhận diện cử chỉ điều khiển:
1. Thư viện Sử dụng
Giải thích
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
import config
Flask: Là một framework web  dùng để xây dựng ứng dụng web. Ở đây, Flask được sử dụng để tạo và quản lý các route và giao diện web.
cv2 (OpenCV): Thư viện xử lý ảnh và video, được sử dụng để đọc, xử lý và hiển thị video.
mediapipe: Thư viện từ Google, được sử dụng để nhận diện pose (dáng người) và cử chỉ.
numpy: Thư viện tính toán số học, đặc biệt hữu ích trong việc xử lý mảng và ma trận.
pygame: Thư viện để xử lý âm thanh và chơi nhạc, được sử dụng ở đây để phát các âm thanh cảnh báo.
FER: Thư viện nhận diện cảm xúc trong hình ảnh, dùng để nhận diện cảm xúc khuôn mặt.
PIL ( Imaging Library): Thư viện xử lý ảnh, đặc biệt trong việc vẽ chữ lên hình ảnh.
os: Thư viện để làm việc với hệ thống tập tin, như kiểm tra sự tồn tại của thư mục hoặc tạo thư mục mới.
requests: Thư viện để gửi HTTP request, dùng để điều khiển các thiết bị qua giao thức HTTP.
cvzone: Thư viện bổ trợ cho OpenCV, đặc biệt cho việc nhận diện cử chỉ tay.
YOLO (You Only Look Once): Một mô hình học sâu dùng để phát hiện đối tượng (trong trường hợp này là phát hiện lửa).
math: Thư viện toán học, được sử dụng để tính toán một số phép toán như làm tròn giá trị.
time: Thư viện xử lý thời gian, đặc biệt trong việc đánh dấu thời gian và đặt tên cho các hình ảnh lưu trữ.
telebot: Thư viện cho phép tương tác với API Telegram để gửi tin nhắn hoặc hình ảnh.
threading: Thư viện hỗ trợ xử lý đa luồng, cho phép thực hiện các tác vụ song song.
config: Một module chứa các cấu hình, chẳng hạn như địa chỉ IP của ESP (một thiết bị ngoại vi trong hệ thống).
2. Cấu hình các đối tượng và khởi tạo Flask App
Giải thích
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()
bot_token = '7837480809:AAH538Eptco2p08H_j0C_M-_86mO_teXLsM'
bot = telebot.TeleBot(bot_token)
live_stream_url = 'http://192.168.137.237:5000/'
chat_id = '-1002384540377'
fire_detected_threshold = 80
start_time = None
alert_played = False
app = Flask(__name__)
mp_pose: Khởi tạo bộ xử lý để nhận diện pose.
pose: Tạo đối tượng Pose từ MediaPipe để thực hiện nhận diện pose trên ảnh hoặc video.
bot_token: Token xác thực cho bot Telegram.
bot: Đối tượng bot Telegram được khởi tạo để gửi tin nhắn.
live_stream_url: Địa chỉ URL của stream video trực tiếp (ở đây giả định là stream từ Flask server).
chat_id: ID của chat Telegram để gửi thông báo.
fire_detected_threshold: Ngưỡng xác định lửa (ví dụ: nhận diện lửa khi độ tin cậy trên 80%).
start_time và alert_played: Biến dùng để theo dõi thời gian và trạng thái cảnh báo.
app: Khởi tạo ứng dụng Flask.
3. Lớp FallDetectionApp
Lớp này quản lý các chức năng của ứng dụng như nhận diện cử chỉ tay, phát hiện ngã, điều khiển thiết bị, và gửi cảnh báo.
Giải thích
class FallDetectionApp:
	def __init__(self):
    	pygame.mixer.init()  # Khởi tạo pygame mixer để chơi âm thanh
    	self.mp_pose = mp.solutions.pose  # Định nghĩa pose của MediaPipe
    	self.pose = self.mp_pose.Pose()  # Tạo đối tượng nhận diện pose
    	self.mp_drawing = mp.solutions.drawing_utils  # Dùng để vẽ landmarks lên ảnh
    	self.emotion_detector = FER()  # Khởi tạo detector cảm xúc
    	self.detector = HandDetector(detectionCon=0.8, maxHands=1)  # Cấu hình detector cử chỉ tay
    	self.model_fire = YOLO('fire.pt')  # Mô hình YOLO để phát hiện lửa
    	self.esp_ip = config.ESP_IP  # Địa chỉ IP của ESP
    	self.cap = cv2.VideoCapture(10)  # Khởi tạo camera, đây là chỉ số thiết bị video
    	self.camera_running = True  # Biến để kiểm soát việc bật/tắt camera
    	self.frame_count = 0  # Đếm số khung hình đã xử lý
    	self.frame_interval = 1  # Tần suất xử lý frame
    	self.drawing = False  # Biến kiểm tra nếu có vẽ vùng an toàn
    	self.start_point = None
    	self.end_point = None
    	self.safety_zones = self.load_safety_zones('safety_zones.txt')  # Đọc vùng an toàn từ file
    	self.fire_detected_time = None  # Thời gian phát hiện lửa
    	self.fire_alerted = False  # Cảnh báo lửa đã được phát
    	self.finger_control_active = True  # Kiểm tra điều khiển bằng cử chỉ tay có đang hoạt động
    	self.photo_dir = "fall_detected_photos"  # Thư mục lưu ảnh khi phát hiện ngã
    	if not os.path.exists(self.photo_dir):
        	os.makedirs(self.photo_dir)  # Tạo thư mục nếu chưa có
Phương thức trong lớp FallDetectionApp:
save_image: Lưu ảnh vào thư mục khi phát hiện sự cố như ngã hoặc lửa.
send_image_to_telegram: Gửi hình ảnh đến Telegram sau khi phát hiện sự cố.
gen_frames: Chức năng chính để lấy các khung hình từ camera, xử lý chúng (phát hiện ngã, phát hiện lửa, nhận diện cử chỉ tay) và trả về khung hình cho Flask để phát trực tuyến.
load_safety_zones: Đọc các vùng an toàn từ file và trả về danh sách các vùng.
check_safety: Kiểm tra xem vị trí (tọa độ) có nằm trong vùng an toàn hay không.
put_text: Vẽ chữ lên ảnh (chẳng hạn như "An toàn" hoặc "Nguy hiểm").
save_safety_zones: Lưu các vùng an toàn vào file.
led_control: Điều khiển đèn LED (qua ESP) dựa trên cử chỉ tay.
move_servo: Điều khiển động cơ servo qua ESP.
update_safety_zones: Cập nhật các vùng an toàn mới.
toggle_camera: Bật/tắt camera.
send_alert: Gửi cảnh báo âm thanh.
update_settings: Cập nhật cài đặt hệ thống.
4. Flask Routes
index: Trang chủ, trả về template HTML.
video_feed: Trả về stream video cho Flask client (HTML page).
toggle_camera_route: Đổi trạng thái bật/tắt camera.
get_safety_zones: Lấy danh sách các vùng an toàn.
play_alert_sound: Phát âm thanh cảnh báo.
set_safety_zone: Cài đặt vùng an toàn mới thông qua các tọa độ từ form.
5. Hàm run
def run(self):
	app.run(debug=True, host='0.0.0.0')
run: Chạy ứng dụng Flask.
6. Tạo đối tượng và chạy ứng dụng
if __name__ == '__main__':
	fall_detection_app = FallDetectionApp()
	fall_detection_app.run()
Khởi tạo đối tượng FallDetectionApp và chạy ứng dụng Flask.

Các Phân Tích Chi Tiết
1.     Nhận diện tư thế người (Pose Detection)
o    Phần này sử dụng thư viện mediapipe để phát hiện các điểm (landmarks) trên cơ thể con người trong video.
o    Các điểm cột sống và khớp cơ thể như shoulder_left, shoulder_right, hip_left, hip_right, knee_left, head.
2.     Tính toán và kiểm tra an toàn (Safety Check)
o    Kiểm tra nếu đầu (head) của người nằm trong vùng an toàn bằng cách so sánh tọa độ với các biên giới của những vùng đã được định nghĩa.
3.     Nhận diện ngã (Fall Detection)
o    Để xác định một người có bị ngã hay không, cần kiểm tra vị trí của các điểm quan trọng như vai, hông và đầu gối.
4.     Nhận diện điều khiển cử chỉ bằng tay (Hand Gesture Control)
o    Sử dụng thư viện cvzone.HandTrackingModule để nhận diện các ngón tay và cử chỉ.
5.     Nhận diện và cảnh báo cháy (Fire Detection)
o    Mô hình YOLO (You Only Look Once) được sử dụng để nhận diện các vùng có khả năng cháy với độ tin cậy nhất định.
6.     Xử lý âm thanh cảnh báo (Alert Sound)
o    Khi phát hiện một sự kiện như ngã hoặc cháy, âm thanh cảnh báo sẽ được phát bằng thư viện pygame.
7.     Hệ thống điều khiển qua Telegram
o    Sau khi phát hiện sự kiện, hình ảnh sẽ được lưu lại và gửi qua Telegram thông qua API TeleBot.

Phần 2:
Hệ Thống Điều Khiển Thiết Bị Bằng Giọng Nói
Code bạn gửi là một hệ thống điều khiển thiết bị trong nhà bằng giọng nói. Sau đây là giải thích chi tiết về các phần của mã này:
1. Thư viện và cấu hình
Giải thích
import os
import time
import requests
import speech_recognition as sr
from gtts import gTTS
import pygame
import config
os: Quản lý các thao tác với hệ điều hành, ví dụ như kiểm tra sự tồn tại của file hoặc xóa file.
time: Quản lý thời gian, ví dụ như trì hoãn chương trình hoặc đợi các sự kiện.
requests: Gửi các yêu cầu HTTP để điều khiển các thiết bị IoT (như bật/tắt đèn, quạt).
speech_recognition: Thư viện nhận diện giọng nói, cho phép chuyển đổi âm thanh thành văn bản.
gTTS: Thư viện chuyển văn bản thành giọng nói, sử dụng Google Text-to-Speech.
pygame: Dùng để phát âm thanh (feedback âm thanh sau khi nhận lệnh).
config: Chứa các cấu hình, ví dụ như địa chỉ IP của ESP (cảm biến, thiết bị IoT).
2. Các hàm điều khiển thiết bị
Giải thích
def turn_on_led1():
	requests.get(f"{esp_ip}/led1/on")
 
def turn_off_led1():
	requests.get(f"{esp_ip}/led1/off")
# Tương tự với các đèn khác, quạt và servo
Mỗi hàm sử dụng requests.get() để gửi yêu cầu HTTP đến ESP8266 (hoặc bất kỳ thiết bị IoT nào khác) để điều khiển các thiết bị như đèn, quạt hoặc servo.
3. Cung cấp phản hồi bằng âm thanh
Giải thích
def provide_feedback(message):
	print(f"Tôi rõ: {message}")
	tts = gTTS(text=message, lang='vi')
    tts.save(file_to_save)
    pygame.mixer.init()
    pygame.mixer.music.load(file_to_save)
    pygame.mixer.music.play()
	while pygame.mixer.music.get_busy(): 
        pygame.time.Clock().tick(10)
    pygame.mixer.music.stop()
    os.remove(file_to_save)
Dùng gTTS để chuyển văn bản thành giọng nói. Giọng nói này được lưu vào file .mp3 và phát lại bằng pygame. Sau khi âm thanh phát xong, file âm thanh sẽ được xóa.
4
def listen_for_command():
	recognizer = sr.Recognizer()
	with sr.Microphone() as source:
    	print("Đang nghe...")
    	recognizer.adjust_for_ambient_noise(source)
    	audio = recognizer.listen(source)
 
	try:
    	command = recognizer.recognize_google(audio, language='vi-VN').lower()
    	print(f"Đã nghe: {command}")
    	return command
	except sr.UnknownValueError:
    	print("Không nghe được lệnh.")
	except sr.RequestError:
    	print("Lỗi kết nối đến dịch vụ nhận diện giọng nói.")
    	provide_feedback("Có lỗi xảy ra khi kết nối đến dịch vụ nhận diện giọng nói.")
 
	return ""
Sử dụng speech_recognition để nghe âm thanh từ microphone và chuyển thành văn bản bằng Google Speech Recognition.
5. Xử lý lệnh
def execute_command(command):
	if 'chào' in command:
    	provide_feedback("Chào bạn! Tôi đã sẵn sàng nhận lệnh.")
	elif 'cảm ơn' in command:
    	provide_feedback("Không có gì. Tôi sẽ ngừng nhận lệnh.")
	elif 'bật đèn 1' in command:
    	turn_on_led1()
    	provide_feedback("OK, đèn 1 đã được bật.")
	# Các lệnh khác tương tự...
Dựa trên văn bản nhận diện từ giọng nói, hệ thống thực thi các hành động tương ứng.
6. Lấy thông tin nhiệt độ và độ ẩm từ ESP
def get_temperature_humidity():
	try:
    	response = requests.get(f"{esp_ip}/temperature")
    	if response.status_code == 200:
        	return response.text
    	else:
        	return "Không thể lấy dữ liệu từ cảm biến."
	except requests.RequestException:
    	return "Lỗi kết nối đến ESP8266."
Gửi yêu cầu HTTP đến ESP để lấy thông tin về nhiệt độ và độ ẩm.
7. Vòng lặp chính
def main():
	while True:
    	command = listen_for_command()
    	if command:
        	execute_command(command)
Chạy vòng lặp liên tục, lắng nghe các lệnh giọng nói và thực thi các lệnh này nếu có.
8. Kiểm tra điều kiện khi bắt đầu chương trình
Copyif __name__ == "__main__":
	main()
Đảm bảo rằng main() chỉ chạy khi script được chạy trực tiếp, không phải khi module được nhập vào từ nơi khác.

Tổng Kết
Phần cứng: ESP8266 hoặc thiết bị IoT khác điều khiển các thiết bị (đèn, quạt, servo).
Giọng nói: Hệ thống sử dụng speech_recognition để nhận diện các lệnh giọng nói từ người dùng và thực thi các hành động điều khiển thiết bị.
Phản hồi: Sau khi nhận lệnh và thực thi, hệ thống cung cấp phản hồi bằng giọng nói thông qua gTTS và phát lại qua pygame.
Điều khiển từ xa: Các yêu cầu HTTP được gửi từ máy tính đến ESP để điều khiển thiết bị (bật/tắt đèn, quạt, kiểm tra nhiệt độ).

Phần 3: Điều Khiển LED và Cảm Biến qua Bot Telegram
1.     Cấu hình Bot Telegram:
o	Đoạn mã sử dụng thư viện telebot để tạo một bot Telegram. Bot này nhận lệnh từ người dùng qua tin nhắn và thực hiện các hành động điều khiển thiết bị (như bật/tắt đèn, điều khiển servo, quạt,...) dựa trên các lệnh nhận được.
o	bot_token là token của bot, dùng để nhận và gửi tin nhắn qua API Telegram.
o	chat_id là ID của nhóm hoặc cá nhân mà bot sẽ gửi tin nhắn.
2.     Điều khiển Servo và Cảm biến Nhiệt Độ và Độ ẩm:
o	move_servo(angle): Hàm này điều khiển servo qua ESP8266 bằng cách gửi yêu cầu HTTP để thay đổi góc servo (từ 0 đến 180 độ).
o	get_temperature_humidity(): Hàm này gửi yêu cầu HTTP tới ESP8266 để lấy dữ liệu cảm biến nhiệt độ và độ ẩm. Nếu thành công, nó trả về dữ liệu từ cảm biến.
3.     Phản hồi qua Bot Telegram:
o	provide_feedback(message): Hàm gửi phản hồi về kết quả của lệnh điều khiển (ví dụ: "LED 1 đã bật", "Quạt đã tắt",...).
4.     Xử lý lệnh điều khiển thiết bị qua Bot:
o	handle_device_control(command, chat_id): Nhận lệnh từ người dùng qua tin nhắn Telegram, sau đó điều khiển các thiết bị tương ứng (bật/tắt đèn, quạt, servo, hoặc gửi liên kết video stream từ camera).
o	Các lệnh như '1', '2', '3' dùng để bật/tắt LED, '4', '04' dùng để điều khiển servo (mở/đóng cửa), '5', '05' để bật/tắt quạt.
5.     Chạy Bot:
o	bot.message_handler(func=lambda message: True): Hàm này là nơi bot nhận và xử lý mọi tin nhắn gửi đến. Sau khi nhận được lệnh từ người dùng, bot sẽ gọi handle_device_control() để thực hiện.
6.     Chạy Bot:
o	bot.polling(none_stop=True): Bot sẽ tiếp tục chạy và lắng nghe tin nhắn từ người dùng.
Phần 4: Cài Đặt và Cập Nhật Vị Trí (Phát hiện ngã với khu vực an toàn)
1.     Cấu hình Video Stream và Webcam:
o	cv2.VideoCapture(10): Dùng OpenCV để mở webcam hoặc camera IP. Dòng lệnh này mở webcam và lấy dữ liệu video từ đó.
o	rtsp_url: Cấu hình cho việc truyền trực tiếp video từ camera IP, nếu sử dụng RTSP.
2.     Vẽ Khu Vực An Toàn:
o	Trong phương thức draw_rectangle, người dùng có thể vẽ một hình chữ nhật để xác định khu vực an toàn trên màn hình. Khi người dùng nhấn chuột, hệ thống sẽ bắt đầu vẽ một hình chữ nhật, và khi nhả chuột, khu vực đó sẽ được lưu lại.
3.     Lưu và Tải Khu Vực An Toàn:
o	save_safety_zone và save_safety_zones: Lưu thông tin các khu vực an toàn vào một tệp văn bản. Mỗi khu vực an toàn được lưu dưới dạng tọa độ của hai góc đối diện.
o	load_safety_zones: Hàm này đọc dữ liệu từ tệp và khôi phục lại các khu vực an toàn khi ứng dụng khởi động lại.
4.     Hiển Thị Khu Vực An Toàn:
o	Trong phương thức gen_frames, video từ webcam sẽ được hiển thị, đồng thời các khu vực an toàn đã được xác định sẽ được vẽ lên màn hình (màu sắc là màu vàng).
o	Nếu người dùng đang vẽ một khu vực an toàn, nó sẽ hiển thị trên màn hình với màu xanh lá cây.
5.     Dừng ứng dụng:
o	Khi người dùng nhấn phím 'q', ứng dụng sẽ dừng lại và đóng tất cả các cửa sổ hiển thị OpenCV.
 
Phần 5 Cảnh báo té ngã trong nhà vệ sinh
1. Cài đặt ban đầu
import cv2
import mediapipe as mp
import numpy as np
import pygame
import telebot
from datetime import datetime
import os
cv2: Thư viện OpenCV để xử lý video và hình ảnh.
mediapipe: Thư viện của Google để xử lý và nhận diện các tư thế cơ thể.
numpy: Thư viện tính toán số học cho các phép toán ma trận, ví dụ như tính toán góc.
pygame: Dùng để phát âm thanh khi phát hiện té ngã.
telebot: Dùng để gửi thông báo qua Telegram khi phát hiện té ngã.
datetime: Lấy thời gian hiện tại để đặt tên cho ảnh.
os: Quản lý các thư mục và tệp tin.
2. Khởi tạo MediaPipe và các công cụ
 
 
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
pose = mp_pose.Pose()
pygame.mixer.init()
fall_sound = pygame.mixer.Sound("fall_sound.wav")
bot_token = '7837480809:AAH538Eptco2p08H_j0C_M-_86mO_teXLsM'
bot = telebot.TeleBot(bot_token)
chat_id = '-1002384540377'
output_folder = "fall_detected_photos"
os.makedirs(output_folder, exist_ok=True)
mp_pose.Pose(): Khởi tạo đối tượng Pose của MediaPipe để theo dõi và nhận diện tư thế cơ thể.
pygame.mixer.init(): Khởi tạo hệ thống âm thanh của pygame để phát âm thanh khi té ngã.
fall_sound: Tải tệp âm thanh cảnh báo khi phát hiện té ngã.
bot_token và bot: Khởi tạo bot Telegram để gửi thông báo.
chat_id: ID của nhóm hoặc người nhận thông báo.
output_folder: Thư mục lưu trữ ảnh khi phát hiện té ngã.
3. Mở camera
 
 
cap = cv2.VideoCapture(1)
cv2.VideoCapture(1): Mở camera (thường là camera thứ hai trong hệ thống).
4. Hàm gửi cảnh báo té ngã qua Telegram
def send_fall_alert(image_path):
	with open(image_path, 'rb') as photo:
        bot.send_photo(chat_id, photo)
send_fall_alert(image_path): Hàm gửi ảnh qua Telegram khi phát hiện té ngã.
Ảnh được mở bằng open() trong chế độ nhị phân ('rb').
Sử dụng phương thức send_photo của telebot để gửi ảnh.
5. Hàm phát hiện té ngã
def detect_fall(landmarks):
    shoulder_left = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
    shoulder_right = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]
	hip_left = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
	hip_right = landmarks[mp_pose.PoseLandmark.RIGHT_HIP]
	nose = landmarks[mp_pose.PoseLandmark.NOSE]
	shoulder_y = (shoulder_left.y + shoulder_right.y) / 2
	hip_y = (hip_left.y + hip_right.y) / 2
	torso_angle = np.arctan2(hip_y - shoulder_y, hip_right.x - shoulder_left.x) * 180 / np.pi
	if abs(shoulder_y - hip_y) < 0.15 and abs(torso_angle) < 30:
    	return True
	return False
detect_fall(landmarks): Phát hiện té ngã dựa vào các điểm đặc trưng của cơ thể (được lấy từ landmarks).
shoulder_left, shoulder_right, hip_left, hip_right, nose: Các điểm trên cơ thể được xác định bởi MediaPipe Pose (vai, hông, mũi).
shoulder_y và hip_y: Tính toán vị trí trung bình của vai và hông.
torso_angle: Tính toán góc của thân người dựa trên vị trí của vai và hông.
Nếu shoulder_y và hip_y cách nhau dưới 0.15 và torso_angle nhỏ hơn 30 độ, hệ thống cho rằng người dùng đang trong tình trạng té ngã.
6. Vòng lặp chính để nhận diện và phát hiện té ngã
fall_detected_frames = 0
fall_confirmation_frames = 5
 
while cap.isOpened():
	ret, frame = cap.read()
	if not ret:
    	break
 
	rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
	results = pose.process(rgb_frame)
 
    skeleton_frame = np.zeros_like(frame)
 
	if results.pose_landmarks:
        mp_drawing.draw_landmarks(
            skeleton_frame,
            results.pose_landmarks,
            mp_pose.POSE_CONNECTIONS,
            mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=3)
    	)
    	if detect_fall(results.pose_landmarks.landmark):
            fall_detected_frames += 1
    	else:
            fall_detected_frames = 0
    	if fall_detected_frames >= fall_confirmation_frames:
            fall_sound.play()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            skeleton_image_path = os.path.join(output_folder, f"skeleton_fall_detected_{timestamp}.jpg")
            cv2.imwrite(skeleton_image_path, skeleton_frame)
            send_fall_alert(skeleton_image_path)
            fall_detected_frames = 0 
 
    cv2.imshow("OUT DETCTED", skeleton_frame)
 
	if cv2.waitKey(1) & 0xFF == ord('q'):
    	break
 
cap.release()
fall_detected_frames: Đếm số frame liên tiếp phát hiện té ngã.
fall_confirmation_frames: Số frame cần phát hiện té ngã liên tiếp để xác nhận là té ngã thật sự.
results.pose_landmarks: Lấy các điểm tư thế cơ thể từ MediaPipe.
mp_drawing.draw_landmarks(): Vẽ các điểm tư thế cơ thể lên hình ảnh.
detect_fall(): Kiểm tra nếu người dùng đang té ngã.
Nếu phát hiện té ngã trong fall_confirmation_frames frame, hệ thống sẽ phát âm thanh cảnh báo, lưu ảnh và gửi ảnh qua Telegram.
cv2.imshow(): Hiển thị video với các điểm tư thế cơ thể.
cv2.waitKey(1): Đợi người dùng nhấn 'q' để thoát khỏi vòng lặp.
Tóm tắt:
Hệ thống sử dụng camera để theo dõi người dùng trong nhà vệ sinh, nhận diện các điểm cơ thể và tính toán các chỉ số như góc của thân người.
Nếu người dùng té ngã (theo các chỉ số này), hệ thống sẽ phát âm thanh cảnh báo và gửi ảnh qua Telegram.
Sau khi xác nhận té ngã trong một số frame liên tiếp, hệ thống sẽ gửi thông báo và hình ảnh té ngã qua Telegram.


 Phần 6: Hàm Dùng để tạo luồng qua địa chỉ ip vs file là config.py
Định nghĩa địa chỉ IP của ESP:
ESP_IP = 'http://192.168.137.66': Đây là địa chỉ IP của ESP trong mạng, giúp các chương trình khác liên lạc với nó khi cần.
Phần 7: Phân ra 4 luồng để chạy các file. Nghĩa là 1 file sẽ chạy 1 luồng hàm này tương ứng với hàm main toàn chương trình
  Hàm run_file1, run_file2, run_file3, run_file4:
Mỗi hàm dùng subprocess.run() để chạy một tệp  riêng:
run_file1(): Chạy tệp telegram call image.py để gọi tính năng gọi và gửi hình ảnh qua Telegram.
run_file2(): Chạy tệp control led và nhiệt độ.py để điều khiển LED và đọc nhiệt độ từ các thiết bị.
run_file3(): Chạy tệp voiceweb.py để thực hiện chức năng điều khiển bằng giọng nói và quản lý giao diện web.
run_file4(): Chạy tệp wc.py để quản lý các chức năng liên quan đến phát hiện té ngã hoặc giám sát khu vực vệ sinh.
Khởi tạo các luồng (threads):
Mỗi tệp sẽ chạy trong một luồng riêng, cho phép các chương trình hoạt động đồng thời mà không phải chờ đợi lẫn nhau.
Các luồng được tạo với:
thread1 = threading.Thread(target=run_file1)
thread2 = threading.Thread(target=run_file2)
thread3 = threading.Thread(target=run_file3)
thread4 = threading.Thread(target=run_file4)
Bắt đầu và đợi các luồng hoàn thành:
start(): Bắt đầu từng luồng, khiến các tệp  chạy song song.
join(): Đợi cho đến khi các luồng hoàn thành trước khi tiếp tục (hoặc kết thúc) chương trình chính.
Phần 8: Phát hiện người lạ.
 1. Cấu hình Telegram
TELEGRAM_TOKEN = '7837480809:AAH538Eptco2p08H_j0C_M-_86mO_teXLsM'
CHAT_ID = '-1002384540377'
TELEGRAM_TOKEN: Đây là mã token của bot Telegram, dùng để xác thực bot khi gửi tin nhắn.
CHAT_ID: ID của nhóm hoặc người nhận tin nhắn trên Telegram. Tin nhắn sẽ được gửi đến chat này.
2. Hàm gửi ảnh qua Telegram
def send_telegram_photo(photo_path):
	url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
	with open(photo_path, 'rb') as photo_file:
    	params = {
        	'chat_id': CHAT_ID,
    	}
    	response = requests.post(url, params=params, files={'photo': photo_file})
	return response
send_telegram_photo(photo_path): Hàm này dùng để gửi ảnh qua Telegram.
photo_path: Đường dẫn đến ảnh cần gửi.
requests.post(): Gửi ảnh qua API của Telegram. Ảnh sẽ được mở bằng open() dưới chế độ nhị phân ('rb').
params chứa chat_id (địa chỉ nhận tin nhắn).
files là tham số chứa ảnh cần gửi.
3. Tải và xử lý các ảnh khuôn mặt đã biết
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
known_faces = []
known_face_names = []
 
path = 'training'
for filename in os.listdir(path):
	if filename.endswith('.jpg') or filename.endswith('.png'):
    	image_path = os.path.join(path, filename)
    	image = cv2.imread(image_path)
    	gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    	faces = face_cascade.detectMultiScale(gray, 1.1, 4)
 
    	for (x, y, w, h) in faces:
        	face_roi = gray[y:y+h, x:x+w]
        	known_faces.append(face_roi)
        	name = os.path.splitext(filename)[0]
        	known_face_names.append(name)
face_cascade: Tải mô hình phát hiện khuôn mặt Haar Cascade để nhận diện khuôn mặt trong ảnh.
known_faces: Danh sách lưu các khuôn mặt đã biết dưới dạng mảng ảnh grayscale.
known_face_names: Danh sách lưu tên tương ứng của các khuôn mặt đã biết.
path = 'training': Đọc ảnh từ thư mục training.
os.listdir(path): Duyệt qua tất cả các tệp trong thư mục training.
cv2.imread(): Đọc ảnh từ đĩa.
cv2.cvtColor(): Chuyển ảnh sang grayscale để việc nhận diện khuôn mặt dễ dàng hơn.
face_cascade.detectMultiScale(): Phát hiện khuôn mặt trong ảnh.
4. Mở camera và nhận diện khuôn mặt trong video
video_capture = cv2.VideoCapture(0)
 
while True:
	ret, frame = video_capture.read()
	gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
 
	faces = face_cascade.detectMultiScale(gray_frame, 1.1, 4)
 
	for (x, y, w, h) in faces:
    	face_roi = gray_frame[y:y+h, x:x+w]
    	name = "Unknown"
    	for i, known_face in enumerate(known_faces):
        	result = cv2.compareHist(
            	cv2.calcHist([face_roi], [0], None, [256], [0, 256]),
            	cv2.calcHist([known_face], [0], None, [256], [0, 256]),
            	cv2.HISTCMP_CORREL
        	)
        	if result > 0.2:
            	name = known_face_names[i]
            	ak
video_capture = cv2.VideoCapture(0): Mở camera để nhận diện khuôn mặt trong thời gian thực.
ret, frame = video_capture.read(): Đọc mỗi frame từ camera.
cv2.cvtColor(): Chuyển đổi frame sang grayscale.
face_cascade.detectMultiScale(): Phát hiện khuôn mặt trong mỗi frame.
cv2.compareHist(): So sánh các histogram giữa khuôn mặt phát hiện được và các khuôn mặt đã biết để nhận diện khuôn mặt. Nếu sự tương đồng lớn hơn 0.2, đó là khuôn mặt đã biết.
5. Chụp ảnh và gửi qua Telegram nếu không nhận diện được khuôn mặt
if name == "Unknown":
	timestamp = time.strftime("%Y%m%d-%H%M%S")
	screenshot_path = f"unknown_face_{timestamp}.jpg"
	cv2.imwrite(screenshot_path, frame) 
	send_telegram_photo(screenshot_path)
	os.remove(screenshot_path) 
if name == "Unknown":: Nếu không nhận diện được khuôn mặt (tên là "Unknown"), hệ thống sẽ chụp ảnh và gửi ảnh đó qua Telegram.
time.strftime(): Lấy thời gian hiện tại để tạo tên ảnh.
cv2.imwrite(): Lưu ảnh chụp vào tệp.
send_telegram_photo(): Gửi ảnh qua Telegram.
os.remove(): Xóa ảnh tạm sau khi đã gửi.
6. Vẽ hình chữ nhật và hiển thị tên khuôn mặt
cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
cv2.putText(frame, name, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
cv2.rectangle(): Vẽ một hình chữ nhật quanh khuôn mặt trong mỗi frame.
cv2.putText(): Hiển thị tên khuôn mặt (hoặc "Unknown" nếu không nhận diện được).
7. Hiển thị video và dừng khi nhấn 'q'
cv2.imshow('Video', frame)
if cv2.waitKey(1) & 0xFF == ord('q'):
	break
cv2.imshow(): Hiển thị video trong cửa sổ.
cv2.waitKey(1): Chờ người dùng nhấn phím. Nếu phím 'q' được nhấn, vòng lặp sẽ dừng lại.
8. Giải phóng tài nguyên khi kết thúc
 
 
video_capture.release()
cv2.destroyAllWindows()
video_capture.release(): Giải phóng tài nguyên camera.
cv2.destroyAllWindows(): Đóng tất cả các cửa sổ OpenCV.
Phần 9: Chụp nhận diện khuôn mặt.
1. Tạo thư mục lưu ảnh
 
 
output_dir = 'training'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)
output_dir = 'training': Đặt tên thư mục lưu ảnh là training.
os.makedirs(output_dir): Kiểm tra xem thư mục này có tồn tại hay không. Nếu không, thư mục training sẽ được tạo ra.
2. Khởi tạo camera
 
 
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Cannot open camera")
	exit()
cap = cv2.VideoCapture(0): Mở camera với chỉ số 0 (thường là camera mặc định của máy tính).
cap.isOpened(): Kiểm tra xem camera có mở thành công không. Nếu không, sẽ in ra thông báo lỗi và kết thúc chương trình bằng exit().
3. Các biến cần thiết
 
 
capture_interval = 2
frame_count = 0
capture_interval = 2: Đặt thời gian chờ giữa mỗi lần chụp ảnh là 2 giây.
frame_count = 0: Khởi tạo biến đếm số lượng ảnh đã chụp.
4. Vòng lặp chụp ảnh
 
 
while True:
	ret, frame = cap.read()
	if not ret:
        print("Khong doc duoc ...")
    	break
    cv2.imshow('frame', frame)
	frame_count += 1
	img_path = os.path.join(output_dir, f'Que Tran_{frame_count:04d}.jpg')
    cv2.imwrite(img_path, frame)
    print(f"Saved {img_path}")
    time.sleep(capture_interval)
	if cv2.waitKey(1) == ord('q'):
    	break
while True:: Bắt đầu vòng lặp vô hạn để liên tục lấy ảnh từ camera.
ret, frame = cap.read(): Đọc một frame từ camera. Nếu không thể đọc, chương trình sẽ in thông báo lỗi và dừng lại.
cv2.imshow('frame', frame): Hiển thị ảnh vừa chụp trong một cửa sổ tên là 'frame'.
frame_count += 1: Tăng số đếm frame lên 1 mỗi khi chụp ảnh.
img_path = os.path.join(output_dir, f'Que Tran_{frame_count:04d}.jpg'): Đặt đường dẫn để lưu ảnh, tên ảnh sẽ theo định dạng Que Tran_XXXX.jpg, với XXXX là số thứ tự của ảnh (được định dạng 4 chữ số).
cv2.imwrite(img_path, frame): Lưu ảnh vào đường dẫn đã định.
print(f"Saved {img_path}"): In ra thông báo đã lưu ảnh tại đường dẫn này.
time.sleep(capture_interval): Tạm dừng chương trình trong 2 giây (theo giá trị capture_interval) giữa mỗi lần chụp ảnh.
if cv2.waitKey(1) == ord('q'):: Kiểm tra xem người dùng có nhấn phím q không. Nếu có, vòng lặp sẽ dừng lại.
5. Dọn dẹp tài nguyên khi kết thúc
 
 
finally:
    cap.release()
    cv2.destroyAllWindows()
cap.release(): Giải phóng tài nguyên của camera khi chương trình kết thúc.
cv2.destroyAllWindows(): Đóng tất cả cửa sổ OpenCV khi chương trình kết thúc.
Tóm lại:
Đoạn mã này sẽ:
1.     Mở camera.
2.     Chụp ảnh mỗi 2 giây và lưu ảnh vào thư mục training với tên là Que Tran_XXXX.jpg.
3.     Hiển thị ảnh đang được chụp trên cửa sổ frame.
4.     Dừng chụp khi người dùng nhấn phím q.
5.     Giải phóng tài nguyên khi kết thúc.
Chương trình này có thể hữu ích để thu thập dữ liệu hình ảnh cho các dự án học máy hoặc nhận dạng đối tượng.
 
Phần 10: Nhắc hẹn
1. Lớp ReminderSystem
Lớp này có vai trò quản lý và thực hiện các nhắc nhở trong hệ thống.
Thuộc tính self.reminders: Lưu trữ các nhắc nhở. Mỗi nhắc nhở sẽ có thời gian (dạng "HH
"), thông điệp và một cờ repeat cho biết liệu nhắc nhở có được lặp lại vào ngày hôm sau hay không.
2. Các phương thức trong ReminderSystem
add_reminder(time_str, message, repeat=False): Thêm một nhắc nhở vào từ điển self.reminders với thời gian, thông điệp và cờ repeat (mặc định là False).
show_reminders(): Hiển thị tất cả các nhắc nhở đã thêm.
speak_message(message): Dùng gTTS để chuyển văn bản thành giọng nói và phát thông báo qua loa.
check_reminders(): Kiểm tra nhắc nhở mỗi phút. Nếu thời gian hiện tại khớp với một nhắc nhở, hệ thống sẽ thông báo và hỏi người dùng có muốn lặp lại nhắc nhở vào ngày hôm sau không.
ask_for_repeat(message): Hỏi người dùng có muốn lặp lại nhắc nhở vào ngày hôm sau.
wait_for_reminder_time(): Chờ đến giờ nhắc nhở và thoát khỏi lắng nghe lệnh mới khi nhắc nhở đến giờ.
schedule_repeat(message): Lên lịch để lặp lại nhắc nhở vào ngày hôm sau.
start_reminder_check(): Bắt đầu kiểm tra nhắc nhở trong một luồng riêng biệt.
listen_for_commands(): Lắng nghe các lệnh giọng nói từ người dùng. Nếu người dùng nói "nhắc hẹn", hệ thống sẽ yêu cầu người dùng cung cấp thời gian và thông điệp nhắc nhở.
listen_for_reminder_details(): Lắng nghe chi tiết về thời gian và thông điệp nhắc nhở từ giọng nói, sau đó thêm nhắc nhở vào hệ thống.
3. Sử dụng thư viện ngoài
speech_recognition: Dùng để nhận diện giọng nói của người dùng.
playsound: Phát âm thanh nhắc nhở bằng giọng nói.
gTTS: Chuyển văn bản thành giọng nói (Text-to-Speech).
os: Quản lý các tệp, ví dụ như xóa tệp âm thanh sau khi phát.
4. Quy trình hoạt động
Bước 1: Khi chương trình khởi chạy, phương thức start_reminder_check() sẽ được gọi trong một luồng riêng biệt để kiểm tra các nhắc nhở mỗi phút.
Bước 2: Phương thức listen_for_commands() sẽ liên tục lắng nghe lệnh giọng nói từ người dùng. Khi người dùng nói "nhắc hẹn", hệ thống sẽ yêu cầu họ cung cấp chi tiết nhắc nhở.
Bước 3: Khi người dùng cung cấp thời gian và thông điệp, phương thức add_reminder() sẽ thêm nhắc nhở vào hệ thống.
Bước 4: Nếu thời gian của một nhắc nhở khớp với thời gian thực, hệ thống sẽ phát thông báo và hỏi người dùng có muốn lặp lại nhắc nhở vào ngày hôm sau.
Bước 5: Các nhắc nhở sẽ được lặp lại nếu người dùng chọn "có" khi hỏi về việc lặp lại.
5. Chạy chương trình
Sau khi khởi tạo đối tượng ReminderSystem, phương thức start_reminder_check() sẽ bắt đầu kiểm tra nhắc nhở trong một luồng riêng, trong khi phương thức listen_for_commands() lắng nghe các lệnh giọng nói.
6. Vấn đề tiềm ẩn
Tiếng ồn xung quanh: Hệ thống có thể gặp khó khăn trong việc nhận diện giọng nói nếu có quá nhiều tiếng ồn.
Định dạng thời gian: Người dùng cần phải nói thời gian đúng định dạng (ví dụ: "23 giờ 15"). Nếu không, chương trình có thể không nhận diện được.
Phần 11: Xử lí bàn tay:
1.     Thông tin cơ bản về gói:
o	name='cvzone': Tên của gói là cvzone.
o	packages=['cvzone']: Danh sách các gói  cần bao gồm. Ở đây, chỉ có một gói là cvzone.
o	version='1.6': Phiên bản của gói là 1.6.
o	license='MIT': Gói này sử dụng giấy phép MIT, cho phép sử dụng mã nguồn mở với ít hạn chế.
2.     Mô tả và thông tin tác giả:
o	description='Computer Vision Helping Library': Mô tả ngắn gọn về gói, nêu rõ đây là một thư viện hỗ trợ về Thị giác máy tính.
o	author='Computer Vision Zone': Tên tác giả hoặc tổ chức phát triển gói.
o	author_email='contact@computervision.zone': Email liên hệ của tác giả hoặc tổ chức phát triển.
o	url='https://github.com/cvzone/cvzone.git': URL đến kho lưu trữ mã nguồn trên GitHub.
3.     Keywords và yêu cầu cài đặt:
o	keywords=['ComputerVision', 'HandTracking', 'FaceTracking', 'PoseEstimation']: Từ khóa giúp người dùng tìm thấy gói khi tìm kiếm.
o	install_requires=[ 'opencv-', 'numpy']: Liệt kê các gói phụ thuộc cần được cài đặt cùng với gói cvzone. Ở đây, gói yêu cầu opencv- và numpy.
o	_requires='>=3.6': Gói yêu cầu  phiên bản 3.6 hoặc cao hơn.
4.     Phân loại (classifiers):
o	Development Status :: 3 - Alpha: Trạng thái phát triển là Alpha, cho thấy gói đang ở giai đoạn thử nghiệm.
o	Intended Audience :: Developers: Đối tượng sử dụng chính là các nhà phát triển.
o	Topic :: Software Development :: Build Tools: Chủ đề của gói là phát triển phần mềm, công cụ xây dựng.
o	License :: OSI Approved :: MIT License: Xác nhận gói được cấp phép MIT.
o	Programming Language ::  :: 3: Gói hỗ trợ  3.
Tóm tắt:
File setup.py này cấu hình để người dùng có thể dễ dàng cài đặt gói cvzone và các phụ thuộc liên quan bằng lệnh pip install cvzone.
Phần 12: Web
 1. Phần head
Cấu trúc tài liệu HTML5: Tài liệu bắt đầu bằng <!DOCTYPE html>, định nghĩa cấu trúc tài liệu là HTML5.
Metadata và CSS:
<meta charset="UTF-8">: Thiết lập mã hóa ký tự UTF-8.
<meta name="viewport" content="width=device-width, initial-scale=1.0">: Tạo responsive cho trang web bằng cách tối ưu hiển thị trên các thiết bị.
<title>Camera AI Home</title>: Tiêu đề của trang.
CSS: Định dạng giao diện của trang.
body: Định dạng nền trắng và font chữ Arial.
#header: Header với nền trắng, màu chữ xám đậm, canh giữa và padding.
#video-container: Đặt video ở giữa trang, bo tròn góc, đổ bóng, và có thể thay đổi kích thước để phù hợp với các thiết bị khác nhau.
#overlay và .notification: #overlay cho phép thêm overlay trên video, và .notification định dạng thông báo.
Watermark: #watermark-top và #watermark-bottom cho phép thêm các đoạn văn bản hoặc ảnh làm watermark ở đầu và cuối của khung video.
Button: .button-container căn giữa các nút, và .button định dạng cho các nút điều khiển với màu xanh dương và hiệu ứng hover.
2. Phần body
Video Feed:
html
 
<img id="video" src="{{ url_for('video_feed') }}" alt="Video Feed">
id="video": Tạo một khung để hiển thị video trực tiếp từ camera.
src="{{ url_for('video_feed') }}": Đường dẫn đến luồng video được cung cấp bởi Flask (ví dụ: qua một endpoint /video_feed).
Nút điều khiển:
html
 
<div class="button-container">
	<button class="button" onclick="toggleCamera()">Start/Stop Camera</button>
</div>
Nút Start/Stop Camera để bật hoặc tắt camera bằng cách gọi hàm JavaScript toggleCamera().
3. Phần script
toggleCamera():
javascript
 
function toggleCamera() {
    fetch('/toggle_camera', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            alert(data.message);
    	});
}
Chức năng: Gửi yêu cầu POST đến server (endpoint /toggle_camera) để bật/tắt camera.
Phản hồi: Hiển thị thông báo dựa trên data.message từ phản hồi JSON.
sendAlert():
javascript
 
function sendAlert() {
	fetch('/send_alert', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            alert(data.message);
    	});
}
Chức năng: Gửi yêu cầu POST đến /send_alert để gửi thông báo đến người dùng hoặc hệ thống.
Phản hồi: Hiển thị thông báo sau khi gửi thành công.
updateSettings():
javascript
 
function updateSettings() {
	const settings = { example: 'value' };
    fetch('/update_settings', {
    	method: 'POST',
    	headers: {
            'Content-Type': 'application/json'
    	},
    	body: JSON.stringify(settings)
	})
    .then(response => response.json())
	.then(data => {
        alert(data.message);
	});
}
Chức năng: Cập nhật cài đặt hệ thống bằng cách gửi dữ liệu JSON đến endpoint /update_settings.
Cài đặt: Dữ liệu được gửi dưới dạng JSON. Ví dụ trong mã, settings chứa { example: 'value' }, nhưng có thể chỉnh sửa thành dữ liệu thực tế.
Phản hồi: Hiển thị thông báo xác nhận cập nhật.
4. Responsive Design
@media (max-width: 600px): Tạo giao diện tương thích với màn hình nhỏ hơn 600px (thường là trên thiết bị di động).
Các thành phần như font chữ, kích thước ảnh và nút điều khiển được điều chỉnh để phù hợp với màn hình nhỏ hơn.
Tóm tắt:
Giao diện này hiển thị video từ camera AI và có các nút để điều khiển camera, gửi cảnh báo và cập nhật cài đặt.
Có thể tương tác với Flask backend thông qua JavaScript để bật/tắt camera, gửi cảnh báo và cập nhật cài đặt.
Giao diện này có khả năng tự điều chỉnh để phù hợp với các thiết bị khác nhau, từ máy tính đến điện thoại di động.
 
 
Phần 13 : ESP và phần cứng.
1. Kết nối Wi-Fi
ESP8266 kết nối với Wi-Fi sử dụng thông tin mạng được cung cấp trong ssid và password.
2. Cấu hình phần cứng
Cảm biến chuyển động (PIR): Được kết nối với chân D0 (PIR_PIN), phát hiện chuyển động.
Cảm biến nhiệt độ và độ ẩm (DHT11): Được kết nối với chân D6 (DHTPIN), sử dụng thư viện DHT để đo nhiệt độ và độ ẩm.
Cảm biến khí (MQ135): Kết nối với chân A0 để đo nồng độ khí độc, khói.
Servo motor: Được kết nối với chân D4 để điều khiển cửa (mở hoặc đóng).
Cảm biến mưa: Kết nối với chân D7 (rainSensorPin), phát hiện mưa.
Buzzer và đèn LED: Kết nối với các chân D9, D1, D2, D3, D4, D5, D8 để điều khiển các thiết bị ngoại vi như đèn và còi báo động.
3. Gửi thông báo qua Telegram
Telegram Bot: Được sử dụng để gửi thông báo khi phát hiện khí độc hoặc mưa. Token bot và chat ID được khai báo để gửi thông báo đến một nhóm hoặc cá nhân trên Telegram.
4. Web Server (ESP8266WebServer)
ESP8266WebServer: Server web chạy trên ESP8266 để nhận các lệnh điều khiển từ thiết bị khác thông qua HTTP. Các lệnh này có thể bật hoặc tắt các thiết bị (LED, quạt, servo) hoặc nhận thông tin từ cảm biến nhiệt độ, độ ẩm, khí độc.
/led1/on: Bật LED 1
/led1/off: Tắt LED 1
/fan3/on: Bật quạt 3
/servo/180: Mở cửa (servo motor)
/temperature: Lấy thông tin nhiệt độ và độ ẩm
/gas: Lấy thông tin về nồng độ khí và khói
5. Các hàm và xử lý trong loop()
Cảm biến chuyển động: Khi phát hiện chuyển động, bật LED 5 và gửi tín hiệu.
Cảm biến khí (MQ135): Đọc giá trị nồng độ khí gas và khói, nếu vượt quá ngưỡng, sẽ gửi thông báo qua Telegram và bật còi báo động.
Cảm biến mưa: Nếu có mưa, sẽ đóng cửa bằng servo và gửi thông báo.
6. Gửi thông báo qua Telegram
Sử dụng hàm sendTelegramMessage() để gửi thông báo đến nhóm/chat Telegram khi phát hiện khí độc hoặc mưa.
Các hành động xảy ra trong mã:
Cảm biến khí MQ135: Đo nồng độ khí và khói, nếu nồng độ vượt quá ngưỡng thì kích hoạt báo động.
Cảm biến mưa: Nếu có mưa, đóng cửa (servo quay về 0 độ) và gửi thông báo.
Cảm biến chuyển động PIR: Khi phát hiện chuyển động, bật đèn LED 5.
Đọc nhiệt độ và độ ẩm: Mỗi giây, mã sẽ đo và in ra thông số nhiệt độ và độ ẩm từ cảm biến DHT11.
Các điều kiện cảnh báo:
1.     Khí độc hoặc khói (ppmGas > 20): Khi có khí độc hoặc khói, báo động và gửi thông báo qua Telegram.
2.     Phát hiện mưa: Đóng cửa và gửi thông báo mưa qua Telegram.
 
Phần 14: Code nhận id đến telegram
1.     Cấu hình nền tảng cho Windows:
o    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy()): Chỉ dùng khi chạy trên Windows để tránh lỗi liên quan đến vòng lặp sự kiện của asyncio.
2.     Thiết lập bot Telegram:
o    TOKEN: Chứa mã thông báo (token) để xác thực với bot Telegram của bạn.
o    bot = telegram.Bot(token=TOKEN): Tạo đối tượng bot sử dụng telegram.Bot để tương tác với API Telegram.
3.     Hàm bất đồng bộ get_chat_id():
o    updates = await bot.get_updates(): Lấy danh sách các tin nhắn cập nhật (updates) từ API Telegram. Mỗi update có thể chứa các tin nhắn hoặc sự kiện khác từ người dùng gửi đến bot.
o    Kiểm tra tin nhắn:
§  Nếu không có cập nhật mới, chương trình sẽ in "Không có tin nhắn mới."
§  Nếu có tin nhắn, chương trình sẽ duyệt qua từng tin nhắn để lấy chat_id và text từ update.message. Sau đó, in chat_id và nội dung text ra màn hình.
4.     Chạy hàm get_chat_id():
o    asyncio.run(get_chat_id()): Khởi chạy hàm bất đồng bộ get_chat_id() để lấy và in các tin nhắn mới nhận được.
Lưu ý:
Hãy chắc chắn rằng bot của bạn đã nhận ít nhất một tin nhắn từ người dùng để có thể lấy chat_id.
Sau khi có chat_id, bạn có thể sử dụng nó trong mã của mình để gửi tin nhắn từ bot đến đúng người nhận hoặc nhóm chat.
 
