import os
import piexif
import numpy as np
import time
from PIL import Image
from keras.models import load_model
from pymongo import MongoClient

classes = {
            0: 'Omezení rychlosti (20 km/h)',
            1: 'Omezení rychlosti (30 km/h)',
            2: 'Omezení rychlosti (50 km/h)',
            3: 'Omezení rychlosti (60 km/h)',
            4: 'Omezení rychlosti (70 km/h)',
            5: 'Omezení rychlosti (80 km/h)',
            6: 'Konec omezení rychlosti (80 km/h)',
            7: 'Omezení rychlosti (100 km/h)',
            8: 'Omezení rychlosti (120 km/h)',
            9: 'Zákaz předjíždění',
            10: 'Zákaz předjíždění nákladních vozidel přesahujících 3,5 tuny',
            11: 'Povinnost dání přednosti zprava',
            12: 'Hlavní silnice',
            13: 'Dej přednost v jízdě',
            14: 'Stop',
            15: 'Zákaz vjezdu vozidel',
            16: 'Zákaz vjezdu vozidel s hmotností přesahující 3,5 tuny',
            17: 'Zákaz vjezdu, jednosměrná ulice',
            18: 'Obecná výstraha',
            19: 'Ostrá pravá zatáčka',
            20: 'Ostrá levá zatáčka',
            21: 'Dvojitá ostrá zatáčka',
            22: 'Nekvalitní vozovka',
            23: 'Kluzká vozovka',
            24: 'Vozovka se zužuje vpravo',
            25: 'Práce na silnici',
            26: 'Dopravní semafory',
            27: 'Chodci',
            28: 'Přechod pro děti',
            29: 'Přechod pro cyklisty',
            30: 'Varování před ledem/sněhem',
            31: 'Varování před divokou zvěří',
            32: 'Konec omezení rychlosti a předjíždění',
            33: 'Přikázaný směr vpravo',
            34: 'Přikázaný směr vlevo',
            35: 'Přikázaný směr rovně',
            36: 'Přikázaný směr rovně nebo vpravo',
            37: 'Přikázaný směr rovně nebo vlevo',
            38: 'Držte se vpravo',
            39: 'Držte se vlevo',
            40: 'Povinný směr jízdy v kruhovém objezdu',
            41: 'Konec zákazu předjíždění',
            42: 'Konec zákazu předjíždění vozidel přesahujících hmotnost 3,5 tuny',
            43: 'Zákaz stání',
            44: 'Práce na silnici',
            45: 'Pozor semafor',
            46: 'Konec hlavní silnice',
            47: 'Přednost před protijedoucími vozidly',
            48: 'Zákaz vjezdu v jednom směru',
            49: 'Zákaz vjezdu všech motorových vozidel',
            50: 'Zákaz odbočení vlevo',
            51: 'Zákaz odbočení vpravo',
            52: 'Konec všech zákazů',
            53: 'Zákaz zastavení',
            54: 'Kruhový objezd',
            55: 'Jednosměrný provoz',
            56: 'Přechod pro chodce',
            57: 'Parkoviště',
            58: 'Obytná zóna',
            59: 'Konec obytné zóny',
            60: 'Zpomalovací práh',
            61: 'Slepá pozemní komunikace'
        }

def extract_gps_from_image(image_path):
    """
    Extracts GPS coordinates (latitude and longitude) and timestamp from the EXIF metadata of an image file.
    """
    try:
        im = Image.open(image_path)
        exif_dict = piexif.load(im.info["exif"])
        description_bytes = exif_dict["0th"].get(piexif.ImageIFD.ImageDescription, b'')
        description = description_bytes.decode('utf-8')
        parts = description.split(',')
        
        latitude_str = parts[0].split(':')[1].strip()
        longitude_str = parts[1].split(':')[1].strip()
        
        latitude = float(latitude_str)
        longitude = float(longitude_str)
        timestamp = exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal].decode('utf-8')
        
        return latitude, longitude, timestamp
    except Exception as e:
        print(f"Error extracting GPS coordinates: {e}")
        return 0, 0

def classify(file_path):
    """
    Classifies an input image into one of the defined traffic sign classes using a pre-trained model.
    """
    image = Image.open(file_path)
    image = image.resize((32, 32))
    image = np.expand_dims(image, axis=0)
    image = np.array(image)
    index = model.predict([image])[0]
    pred2 = np.argmax(index, axis=0)
    sign = classes[pred2]
    return sign, pred2

# Load the pre-trained traffic sign classification model
model = load_model("models/traffic_classifier_new.h5")

# Connect to MongoDB database
client = MongoClient('mongodb://127.0.0.1:27017/')
db = client['traffic_data']
collection = db['image_data']

folder_path = "output_pics"

def check_ordered_files_and_save_to_database(folder_path, collection):
    """
    Iterates through image files in a specified folder, checks for missing sequence numbers in the file names,
    extracts GPS coordinates, classifies the traffic sign, and saves relevant information to the database.
    """
    files = os.listdir(folder_path)
    sorted_files = sorted(files)

    for i in range(len(sorted_files) - 1):
        current_file = sorted_files[i]
        next_file = sorted_files[i + 1]
        
        current_number = int(current_file.split('_')[-1].split('.')[0])
        next_number = int(next_file.split('_')[-1].split('.')[0])
        
        if next_number - current_number > 1:
            missing_file_number = current_number
            original_file = f"{current_file.split('_')[0]}_{current_file.split('_')[1]}_{current_file.split('_')[2]}_{missing_file_number}.jpg"
            original_path = os.path.join(folder_path, original_file)
            lat, lon, timestamp = extract_gps_from_image(original_path)
            sign, pred2 = classify(original_path)

            timestamp_struct = time.strptime(timestamp, "%Y:%m:%d %H:%M:%S")
            formatted_time = time.strftime("%d.%m.%Y %H:%M:%S", timestamp_struct)

            if pred2 < 12:
                continue
            else:
                data = {
                    "filename": current_file,
                    "predicted_class": sign,
                    "latitude": lat,
                    "longitude": lon,
                    "time": formatted_time,
                    "probability": float(100 - pred2)
                }
                collection.insert_one(data)
    
    client.close()

# Execute the function to process images and save data to the database
check_ordered_files_and_save_to_database(folder_path, collection)