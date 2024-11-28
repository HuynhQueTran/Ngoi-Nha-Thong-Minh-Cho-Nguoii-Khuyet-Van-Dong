import requests
import telebot
import config
import subprocess 
bot_token = '7837480809:AAH538Eptco2p08H_j0C_M-_86mO_teXLsM'  
bot = telebot.TeleBot(bot_token)

live_stream_url = 'http://192.168.140.2:5000'
esp_ip = config.ESP_IP
chat_id = '-1002384540377' 
khuon_mat_process = None
def move_servo(angle):
    try:
        angle = max(0, min(angle, 180))     
        response = requests.get(f"{esp_ip}/servo?angle={angle}")
        if response.status_code == 200:
            print(f"Servo  {angle}")
        else:
            print(f"Failed: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error sending request to ESP8266: {e}")

def get_temperature_humidity():
    try:
        response = requests.get(f"{esp_ip}/temperature") 
        if response.status_code == 200:
            message = response.text 
            return message  
        else:
            return "Không thể lấy dữ liệu từ cảm biến."
    except requests.RequestException:
        return "Lỗi kết nối đến ESP8266."

def provide_feedback(message):
    bot.send_message(chat_id, message)

def handle_device_control(command, chat_id):
    command = command.lower()
    global khuon_mat_process
    if command == 'o':
        if khuon_mat_process is None:
            khuon_mat_process = subprocess.Popen(['python', 'khuon_mat.py'])
            provide_feedback("Mở tính năng phát hiện người lạ")
        else:
            provide_feedback("khuon_mat.py.")
    elif command == 'q':
        if khuon_mat_process is not None:
            khuon_mat_process.terminate()
            khuon_mat_process = None
            provide_feedback("Đóng tính năng phát hiện người lạ")
        else:
            provide_feedback("khuon_mat.py is not running.")
            command = command.lower()
    elif command == "v":
        provide_feedback(f"Xem camera tại: {live_stream_url}")
    elif command == '1':
        requests.get(f"{esp_ip}/led1/on")
        provide_feedback("LED 1 is ON")
    elif command == '2':
        requests.get(f"{esp_ip}/led2/on")
        provide_feedback("LED 2 is ON")
    elif command == '02':
        requests.get(f"{esp_ip}/led2/off")
        provide_feedback("LED 2 is OFF")
    elif command in ['01', '0']:
        requests.get(f"{esp_ip}/led1/off")
        requests.get(f"{esp_ip}/led2/off")
        provide_feedback("LEDs are OFF")
    elif command in ['3', '03']:
        requests.get(f"{esp_ip}/led1/on")
        requests.get(f"{esp_ip}/led2/on")
        provide_feedback("LED 1 AND 2 are ON")
    elif command == '4':
        move_servo(180)  
        provide_feedback("OPEN DOOR")
    elif command == '04':
        move_servo(0) 
        provide_feedback("CLOSE")
    elif command == '5':
        requests.get(f"{esp_ip}/fan3/on")  
        provide_feedback("MỞ QUẠT")
    elif command == '05':
        requests.get(f"{esp_ip}/fan3/off")
        provide_feedback("TẮT QUẠT")
    elif 'h' in command or 'độ ẩm' in command:
        result = get_temperature_humidity()
        provide_feedback(f"Nhiệt độ và độ ẩm hiện tại là: {result}")
    else:
        provide_feedback("Lệnh không xác định.")

@bot.message_handler(func=lambda message: True)
def receive_message(message):
    chat_id = message.chat.id
    command = message.text.strip()
    handle_device_control(command, chat_id)

if __name__ == "__main__":
    print("Bot is running...")
    bot.polling(none_stop=True)
