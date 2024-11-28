# camera_stream.py
import cv2
import mediapipe as mp
import numpy as np
import pygame
from fer import FER
from PIL import Image, ImageDraw, ImageFont
import os
import time
import telebot

class CameraStream:
    def __init__(self, rtsp_url):
        self.rtsp_url = rtsp_url
        self.cap = None

    def start_stream(self):
        """Bắt đầu luồng RTSP."""
        self.cap = cv2.VideoCapture(self.rtsp_url)
        if not self.cap.isOpened():
            raise Exception(f"Không thể kết nối với camera RTSP: {self.rtsp_url}")

    def get_frame(self):
        """Lấy một khung hình từ camera."""
        if self.cap is None:
            raise Exception("Luồng chưa được khởi động. Gọi start_stream() trước.")
        ret, frame = self.cap.read()
        if not ret:
            raise Exception("Không thể đọc dữ liệu từ camera.")
        return frame

    def release(self):
        """Giải phóng tài nguyên."""
        if self.cap is not None:
            self.cap.release()

# Test if this file is run directly
if __name__ == "__main__":
    rtsp_url = "rtsp://admin:EGIBWC@192.168.137.130:554/h264_stream"
    camera = CameraStream(rtsp_url)

    try:
        camera.start_stream()
        while True:
            frame = camera.get_frame()
            cv2.imshow("Camera Ezviz - RTSP Stream", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        camera.release()
        cv2.destroyAllWindows()
