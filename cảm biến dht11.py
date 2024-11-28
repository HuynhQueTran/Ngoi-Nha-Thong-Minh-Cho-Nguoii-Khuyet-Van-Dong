import requests
import speech_recognition as sr
import pygame
import time
from gtts import gTTS  

ESP_IP = "192.168.137.146"

def speak(text):
    pygame.mixer.init()
    tts = gTTS(text=text, lang='vi')
    tts.save("response.mp3")
    pygame.mixer.music.load("response.mp3")
    pygame.mixer.music.play()

    while pygame.mixer.music.get_busy():
        time.sleep(1)

def get_temperature_humidity():
    try:
        response = requests.get(f"http://{ESP_IP}/temperature")
        if response.status_code == 200:
            return response.text
        else:
            return "Không thể lấy dữ liệu từ cảm biến"
    except requests.RequestException:
        return "Lỗi kết nối đến ESP8266"

def listen_and_respond():
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()

    speak("Xin chào! Vui lòng nói 'chào bạn' để bắt đầu.")

    while True:
        try:
            with microphone as source:
                print("Đang lắng nghe...")
                recognizer.adjust_for_ambient_noise(source)
                audio = recognizer.listen(source)

            command = recognizer.recognize_google(audio, language="vi-VN")
            print("Bạn nói:", command)

            if "chào bạn" in command.lower():
                speak("Xin chào! Bạn cần giúp gì?")

            elif "nhiệt độ" in command.lower() or "độ ẩm" in command.lower():
                result = get_temperature_humidity()
                speak(f"Nhiệt độ và độ ẩm hiện tại là: {result}")

            elif "cảm ơn" in command.lower():
                speak("Cảm ơn bạn! Tôi vẫn ở đây nếu bạn cần gì thêm.")

            else:
                speak("Xin lỗi, tôi không hiểu. Vui lòng thử lại.")

        except sr.UnknownValueError:
            print("Không nhận diện được giọng nói, vui lòng thử lại.")
        except sr.RequestError:
            print("Không thể kết nối tới dịch vụ nhận diện giọng nói.")

        time.sleep(1)

if __name__ == "__main__":
    listen_and_respond()
