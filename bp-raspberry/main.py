import urllib.request
import urllib.error
import os
import RPi.GPIO as GPIO
from add_gps import add_geolocation, get_current_speed
from picamera2 import Picamera2
from server_upload import upload_files_sftp
import time

# Pin for LED indicator
led_pin = 18
GPIO.setmode(GPIO.BCM)
GPIO.setup(led_pin, GPIO.OUT)

# Local and remote folders for file transfer
local_folder = '/home/raspi/Desktop/raspi-part/pictures/'
remote_folder = '/home/rcollector/tsr/input_pics'

# SFTP server details
server = 'doprava.nti.tul.cz'
username = 'rcollector'
private_key_path = '/home/raspi/.ssh/id_rsa'

# Function to check internet connectivity
def is_internet_connected():
    try:
        urllib.request.urlopen('http://www.google.com', timeout=1)
        return True
    except urllib.request.URLError:
        return False

try:
    # Initialize PiCamera
    picam2 = Picamera2()
    picam2.start()
    time.sleep(1)
    picam2.set_controls({"AfMode": 2, "AfTrigger": 0})
    GPIO.output(led_pin, GPIO.HIGH)
    time.sleep(5)

    while True:
        # Add geolocation to captured images
        add_geolocation(picam2)
        # Get current speed
        speed = get_current_speed()[2]

        # Check if speed is 0 and internet is connected
        if speed == 0.0 and is_internet_connected():
            print("Internet is connected. Uploading files and restarting the code...")
            
            # Upload files to remote server
            upload_files_sftp(local_folder, remote_folder, server, username, private_key_path)
            
            # Delete uploaded files from local folder
            files_in_folder = os.listdir(local_folder)
            for file in files_in_folder:
                file_path = os.path.join(local_folder, file)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    print(f"Failed to delete {file_path}. Error: {e}")

            # Blink LED indicator
            for _ in range(5): 
                GPIO.output(led_pin, GPIO.HIGH)
                time.sleep(0.5)
                GPIO.output(led_pin, GPIO.LOW)
                time.sleep(0.5)

            GPIO.output(led_pin, GPIO.HIGH)
            continue
        else:
            continue
                
except Exception as e:
    # Handle exceptions
    print("\nProgram end")
    print(e)
    GPIO.output(led_pin, GPIO.LOW)
    GPIO.cleanup()
    exit()
