import piexif
from gps import L76X
import time
import os

# Initialize GPS module
x = L76X.L76X()
x.L76X_Set_Baudrate(9600)
x.L76X_Send_Command(x.SET_POS_FIX_400MS)
x.L76X_Send_Command(x.SET_NMEA_OUTPUT)
x.L76X_Exit_BackupMode()

def get_current_gps_values():
    # Get current GPS values (latitude, longitude, status)
    x.L76X_Gat_GNRMC()
    return x.Lat, x.Lon, x.Status

def get_current_speed():
    # Get current speed
    return x.get_speed()

def add_geolocation(camera):
    # Get current GPS values
    latitude, longitude, status = get_current_gps_values()
    
    # Define the folder to save pictures
    pictures_folder = '/home/raspi/Desktop/raspi-part/pictures/'
    if not os.path.exists(pictures_folder):
        os.makedirs(pictures_folder)
    
    # Generate filename with current datetime
    current_datetime = time.strftime("%Y%m%d_%H%M%S")
    image_filename = f'{pictures_folder}/{current_datetime}.jpg'
    camera.capture_file(image_filename)

    try:
        # Load existing EXIF data from the image
        exif_data = piexif.load(image_filename)
        
        # Check GPS positioning status
        if status == 1:
            print('Already positioned')
        else:
            print('No positioning')
        
        # Print latitude and longitude
        print('Latitude:', latitude)
        print('Longitude:', longitude)
        
        # Format latitude and longitude strings
        latitude_str = f"{latitude:.12f}"
        longitude_str = f"{longitude:.12f}"
        
        # Create caption with latitude and longitude
        caption = f"Latitude: {latitude_str}, Longitude: {longitude_str}"
        
        # Update EXIF data with the caption
        exif_data['0th'][piexif.ImageIFD.ImageDescription] = caption.encode('utf-8')

        # Dump updated EXIF data
        exif_bytes = piexif.dump(exif_data)
        # Insert updated EXIF data into the image
        piexif.insert(exif_bytes, image_filename)
        
        print(f"EXIF data updated successfully for the image {image_filename}.")
    except Exception as e:
        print(f"Error: {str(e)}")
