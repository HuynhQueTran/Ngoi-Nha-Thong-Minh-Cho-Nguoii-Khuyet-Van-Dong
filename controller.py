
import pyfirmata

comport = 'COM6'
board = pyfirmata.Arduino(comport)

led_pins = {
    'led_1': board.get_pin('d:8:o'),
    'led_2': board.get_pin('d:9:o'),
    'led_3': board.get_pin('d:10:o'),
    'led_4': board.get_pin('d:11:o'),
    'led_5': board.get_pin('d:12:o'),
    'led_fire': board.get_pin('d:13:o')
}

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

def led_control(fingerUp):
    if fingerUp == [0,0,0,0,0]:
        led_pins['led_1'].write(0)
        led_pins['led_2'].write(0)
        led_pins['led_3'].write(0)
        led_pins['led_4'].write(0)
        led_pins['led_5'].write(0)
    elif fingerUp == [0,1,0,0,0]:
        led_pins['led_1'].write(1)
        led_pins['led_2'].write(0)
        led_pins['led_3'].write(0)
        led_pins['led_4'].write(0)
        led_pins['led_5'].write(0)
    elif fingerUp == [0,1,1,0,0]:
        led_pins['led_1'].write(1)
        led_pins['led_2'].write(1)
        led_pins['led_3'].write(0)
        led_pins['led_4'].write(0)
        led_pins['led_5'].write(0)
    elif fingerUp == [0,1,1,1,0]:
        led_pins['led_1'].write(1)
        led_pins['led_2'].write(1)
        led_pins['led_3'].write(1)
        led_pins['led_4'].write(0)
        led_pins['led_5'].write(0)
    elif fingerUp == [0,1,1,1,1]:
        led_pins['led_1'].write(1)
        led_pins['led_2'].write(1)
        led_pins['led_3'].write(1)
        led_pins['led_4'].write(1)
        led_pins['led_5'].write(0)
    elif fingerUp == [1,1,1,1,1]:
        led_pins['led_1'].write(1)
        led_pins['led_2'].write(1)
        led_pins['led_3'].write(1)
        led_pins['led_4'].write(1)
        led_pins['led_5'].write(1)

def control_led(name, state):
    if name in led_pins:
        led_pins[name].write(state)
    
def control_servo(angle):
    servo_4.write(angle)
