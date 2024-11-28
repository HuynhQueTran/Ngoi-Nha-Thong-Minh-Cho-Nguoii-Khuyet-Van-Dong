import os
import time
import requests
import speech_recognition as sr
from gtts import gTTS
import pygame
import config

esp_ip = config.ESP_IP  
def turn_on_led1():
    requests.get(f"{esp_ip}/led1/on")

def turn_off_led1():
    requests.get(f"{esp_ip}/led1/off")

def turn_on_led2():
    requests.get(f"{esp_ip}/led2/on")

def turn_off_led2():
    requests.get(f"{esp_ip}/led2/off")

def turn_on_led3():
    requests.get(f"{esp_ip}/led3/on")

def turn_off_led3():
    requests.get(f"{esp_ip}/led3/off")

def turn_on_fan():
    requests.get(f"{esp_ip}/fan3/on") 

def turn_off_fan():
    requests.get(f"{esp_ip}/fan3/off")

def move_servo():
    requests.get(f"{esp_ip}/servo?angle=180")

def move_servo1():
    requests.get(f"{esp_ip}/servo?angle=0")
feedback_file_1 = "feedback_1.mp3"
feedback_file_2 = "feedback_2.mp3"

def provide_feedback(message):
    print(f"Tôi rõ: {message}")
    
    if os.path.exists(feedback_file_1):
        try:
            os.remove(feedback_file_1)
        except PermissionError:
            print(f"Lỗi khi xóa {feedback_file_1}. Tiến trình đang sử dụng file.")
    if os.path.exists(feedback_file_2):
        try:
            os.remove(feedback_file_2)
        except PermissionError:
            print(f"Lỗi khi xóa {feedback_file_2}. Tiến trình đang sử dụng file.")

    file_to_save = feedback_file_1 if not os.path.exists(feedback_file_1) else feedback_file_2
    tts = gTTS(text=message, lang='vi')
    tts.save(file_to_save)

    pygame.mixer.init()
    pygame.mixer.music.load(file_to_save) 
    pygame.mixer.music.play()  

    while pygame.mixer.music.get_busy():  
        pygame.time.Clock().tick(10)

    pygame.mixer.music.stop() 
    
    time.sleep(1)  
    try:
        os.remove(file_to_save)  
    except PermissionError:
        print("Không thể xóa file âm thanh, vì nó vẫn đang được sử dụng.")
    except Exception as e:
        print(f"Đã xảy ra lỗi khi xóa file: {e}")
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

def execute_command(command):
    if 'chào' in command:
        provide_feedback("Chào bạn! Tôi đã sẵn sàng nhận lệnh.")
    elif 'cảm ơn' in command:
        provide_feedback("Không có gì. Tôi sẽ ngừng nhận lệnh.")
def get_temperature_humidity():
    try:
        response = requests.get(f"{esp_ip}/temperature")
        if response.status_code == 200:
            return response.text
        else:
            return "Không thể lấy dữ liệu từ cảm biến."
    except requests.RequestException:
        return "Lỗi kết nối đến ESP8266."

def execute_command(command):
    global active_mode

    if 'chào' in command:
        active_mode = True
        provide_feedback("Chào bạn! Tôi đã sẵn sàng nhận lệnh.")
    elif 'cảm ơn' in command:
        active_mode = False
        provide_feedback("Không có gì. Tôi sẽ ngừng nhận lệnh.")
    elif active_mode:
        if 'bật đèn 1' in command:
            turn_on_led1()
            provide_feedback("OK, đèn 1 đã được bật.")
        elif 'tắt đèn 1' in command:
            turn_off_led1()
            provide_feedback("OK, đèn 1 đã được tắt.")
        elif 'bật đèn 2' in command:
            turn_on_led2()
            provide_feedback("OK, đèn 2 đã được bật.")
        elif 'tắt đèn 2' in command:
            turn_off_led2()
            provide_feedback("OK, đèn 2 đã được tắt.")
        elif 'bật đèn 3' in command:
            turn_on_led3()
            provide_feedback("OK, đèn 3 đã được bật.")
        elif 'tắt đèn 3' in command:
            turn_off_led3()
            provide_feedback("OK, đèn 3 đã được tắt.")
        elif 'bật hai đèn' in command:
            turn_on_led1()
            turn_on_led2()
            provide_feedback("OK, hai đèn đã được bật.")
        elif 'tắt hai đèn' in command:
            turn_off_led1()
            turn_off_led2()
            provide_feedback("OK, hai đèn đã được tắt.")
        elif 'bật quạt' in command:
            turn_on_fan()
            provide_feedback("OK, quạt đã được bật.")
        elif 'tắt quạt' in command:
            turn_off_fan()
            provide_feedback("OK, quạt đã được tắt.")
        elif 'nhiệt độ' in command or 'độ ẩm' in command:
            result = get_temperature_humidity()
            provide_feedback(f"Nhiệt độ và độ ẩm hiện tại là: {result}")
        elif 'mở cửa' in command:
            move_servo(180)  
            provide_feedback("OK, Cửa đã được mở")
        elif 'đóng cửa' in command:
            move_servo(0) 
            provide_feedback("OK, Cửa đã được đóng.")
        else:
            provide_feedback("Lệnh không xác định.")
def main():
    while True:
        command = listen_for_command()
        if command:
            execute_command(command)

if __name__ == "__main__":
    main()
