import threading
import subprocess
import sys

def run_file1():
    subprocess.run([sys.executable, "voiceweb.py"], check=True) 

def run_file2():
    subprocess.run([sys.executable, "/mnt/mydisk/NGOI NHA THONG MINH CHO NGUOI KHUYET VAN DONG/fall  and fire detected.py"], check=True)      

def run_file3():
    subprocess.run([sys.executable, "/mnt/mydisk/NGOI NHA THONG MINH CHO NGUOI KHUYET VAN DONG/wc1.py"], check=True)  
def run_file4():
    subprocess.run([sys.executable, "/mnt/mydisk/NGOI NHA THONG MINH CHO NGUOI KHUYET VAN DONG/hand_control.py"], check=True)  
def run_file5():
    subprocess.run([sys.executable, "/mnt/mydisk/NGOI NHA THONG MINH CHO NGUOI KHUYET VAN DONG/sleeping.py"], check=True)  
def run_file6():
    subprocess.run([sys.executable, "/mnt/mydisk/NGOI NHA THONG MINH CHO NGUOI KHUYET VAN DONG/sleeping.py"], check=True)  
thread1 = threading.Thread(target=run_file1)
thread2 = threading.Thread(target=run_file2)
thread3 = threading.Thread(target=run_file3)
thread4 = threading.Thread(target=run_file4)
thread5 = threading.Thread(target=run_file5)
thread6 = threading.Thread(target=run_file5)
thread1.start()
thread2.start()
thread3.start()
thread4.start()
thread5.start()
thread6.start()
thread1.join()
thread2.join()
thread3.join()
thread4.join()
thread5.join()
thread6.join()