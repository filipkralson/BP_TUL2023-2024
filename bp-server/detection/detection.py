import torch
from PIL import Image
import cv2
import numpy as np
import os
import time
import piexif
from efficientdet.backbone import EfficientDetBackbone
from efficientdet.utils import BBoxTransform, ClipBoxes
from myutils.utils import preprocess, invert_affine, postprocess

# EfficientDet parameters
compound_coef = 2
num_classes_detector = 1
force_input_size = None

# Input and output paths
input_path = "/home/rcollector/tsr/input_pics"
output_path = "/home/rcollector/tsr/output_pics2"

# Path to the trained EfficientDet model
model_detector = '/home/rcollector/tsr/detection/efficientdet/efficientdet-d2_72_36000.pth'

# Anchor parameters
anchor_ratios = [(1.0, 1.0), (1.0, 1.0), (1.0, 0.9)]
anchor_scales = [2 ** 0, 2 ** (1.0 / 3.0), 2 ** (2.0 / 3.0)]

# Detection thresholds
threshold = 0.5
iou_threshold = 0.5

# Input sizes for different compound coefficients
input_sizes = [512, 640, 768, 896, 1024, 1280, 1280, 1536, 1536]
input_size = input_sizes[compound_coef] if force_input_size is None else force_input_size

# Load EfficientDet model
model = EfficientDetBackbone(compound_coef=compound_coef,
                             num_classes=num_classes_detector,
                             ratios=anchor_ratios, scales=anchor_scales)
model.load_state_dict(torch.load(
    model_detector, map_location=torch.device('cpu')))
model.requires_grad_(False)
model.eval()

# Counter and time for processing
interator = 1
start_time = time.time()

def extract_gps_from_image(image_path):
    try:
        # Extract GPS coordinates from image EXIF metadata
        im = Image.open(image_path)
        exif_dict = piexif.load(im.info["exif"])
        description_bytes = exif_dict["0th"].get(piexif.ImageIFD.ImageDescription, b'')
        description = description_bytes.decode('utf-8')
        parts = description.split(',')
        
        latitude_str = parts[0].split(':')[1].strip()
        longitude_str = parts[1].split(':')[1].strip()
        
        latitude = float(latitude_str)
        longitude = float(longitude_str)
        
        return latitude, longitude
    except Exception as e:
        print(f"Error extracting GPS coordinates: {e}")
        return 0, 0

def detection_logic():
    global interator
    for img_file in os.listdir(input_path):
        try:
            img_path = os.path.join(input_path, img_file)
            ori_imgs, framed_imgs, framed_metas = preprocess(img_path, max_size=input_size)       
            lat, lon = extract_gps_from_image(img_path)
            
            description = f"Latitude: {lat}, Longitude: {lon}"
            exif_dict = piexif.load(img_path)
            exif_dict['0th'][piexif.ImageIFD.ImageDescription] = description.encode('utf-8')
            
            timeSave = exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal]
            x = torch.stack([torch.from_numpy(fi) for fi in framed_imgs], 0)

            x = x.to(torch.float32).permute(0, 3, 1, 2)

            with torch.no_grad():
                features, regression, classification, anchors = model(x)
                regressBoxes = BBoxTransform()
                clipBoxes = ClipBoxes()
                out = postprocess(x,
                                anchors, regression, classification,
                                regressBoxes, clipBoxes,
                                threshold, iou_threshold)

            out = invert_affine(framed_metas, out)
            files_in_input = len(os.listdir(input_path))
            
            for i, detection in enumerate(out):
                for j in range(len(detection['rois'])):
                    if len(detection['rois']) == 0:
                        continue
                    x1, y1, x2, y2 = detection['rois'][j].astype(np.int32)
                    cropped_img = ori_imgs[i][y1:y2, x1:x2]
                    cv2.imwrite(os.path.join(output_path, f"{i}_{j}_{img_file}"), cropped_img)
                    
                    exif_dictFinal = {"0th": exif_dict['0th'], "Exif": exif_dict["Exif"]}
                    exif_bytes = piexif.dump(exif_dictFinal)
                    
                    piexif.insert(exif_bytes, os.path.join(output_path, f"{i}_{j}_{img_file}"))
                    print(f"{interator}/{files_in_input} Image {i}_{j}_{img_file} saved")
                    interator += 1
        except Exception as e:
            print(f"Error processing image {img_file}: {e}. Skipping...")
            continue
        
        
if __name__ == "__main__":
    detection_logic()
