import os
import time
import shutil
import random
import folium
import threading
import schedule
import pandas as pd
from datetime import datetime
from collections import Counter
from pymongo import MongoClient
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.layouts import column
from flask import Flask, render_template
#from detection import detection
#import classification_files_count
from bokeh.models import ColumnDataSource, ZoomInTool, ZoomOutTool, HoverTool

# Initialize Flask app
app = Flask(__name__, static_folder="/static")

# Connect to MongoDB
mongo_client = MongoClient('mongodb://localhost:27017')
db = mongo_client['traffic_data']
collection_image = db['image_data']
collection_file = db['file_data']
collection_detected = db['detected_data']

# Functions to load data from MongoDB
def load_image_data():
    cursor = collection_image.find()
    data = list(cursor)
    return data

def load_file_data():
    cursor = collection_file.find()
    data = list(cursor)
    return data

def load_detected_data():
    cursor = collection_detected.find()
    data = list(cursor)
    return data

# Update data from MongoDB periodically
def update_data():
    global image_data, file_data, detected_data
    while True:
        detected_data = load_detected_data()
        image_data = load_image_data()
        file_data = load_file_data()
        time.sleep(60)

# Function to get record count from MongoDB
def get_record_count():
    count = collection_image.count_documents({})
    return count

# Function to get file count in directory
def get_file_count():
    file_count = len(os.listdir("input_pics/"))
    return file_count

# Function to get detected count in directory
def get_detected_count():
    file_count = len(os.listdir("output_pics/"))
    return file_count

# Function to insert file count into MongoDB
def insert_file_count(count):
    record = {'count': count, 'timestamp': time.time()}
    collection_file.insert_one(record)
    
# Function to insert detected count into MongoDB
def insert_detected_count(count):
    record = {'count': count, 'timestamp': time.time()}
    collection_detected.insert_one(record)

# Function to update and insert file count into MongoDB
def update_and_insert_file_count():
    current_count = get_file_count()
    last_count = get_file_count_from_db()
    if last_count is not None:
        current_count += last_count
    insert_file_count(current_count)

# Function to update and insert detected count into MongoDB
def update_and_insert_detected_count():
    current_count = get_detected_count()
    last_count = get_detected_count_from_db()
    if last_count is not None:
        current_count += last_count
    insert_detected_count(current_count)

# Function to delete contents of directories
def delete_contents_of_directories():
    try:
        shutil.rmtree("input_pics/")
        shutil.rmtree("output_pics/")
        print("Contents of both directories have been successfully deleted.")
    except Exception as e:
        print(f"Error deleting contents of directories: {e}")

# Function to schedule update tasks
def schedule_update():
    while True:
        schedule.run_pending()
        time.sleep(60)

# Function to get file count from MongoDB
def get_file_count_from_db():
    last_record = collection_file.find_one(sort=[('_id', -1)])
    if last_record:
        return last_record['count']
    else:
        return None

# Function to get detected count from MongoDB
def get_detected_count_from_db():
    last_record = collection_detected.find_one(sort=[('_id', -1)])
    if last_record:
        return last_record['count']
    else:
        return None

# Function to generate random hex colors
def generate_colors_hex():
    colors = []
    for i in range(61):
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        color_hex = '#%02x%02x%02x' % (r, g, b)
        colors.append(color_hex)
    return colors 

# Funciton pro processing the data from database
def process_data(data, custom_palette):
    class_counts = Counter(data['predicted_class'])
    total_count = sum(class_counts.values())
    percentages = [count / total_count * 100 for count in class_counts.values()]
    
    colors = custom_palette[:len(class_counts)]
    
    table_data = []
    for i, cls in enumerate(class_counts.keys()):
        table_data.append((cls, class_counts[cls], percentages[i], colors[i]))
    
    table_data.sort(key=lambda x: x[2], reverse=True)
    
    return table_data

# Function for ploting the output
def create_bokeh_plot(data, custom_palette):
    class_counts = Counter(data['predicted_class'])
    
    sorted_class_counts = dict(sorted(class_counts.items(), key=lambda item: item[1], reverse=True))
    colors = [custom_palette[i % len(custom_palette)] for i in range(len(sorted_class_counts))]
    
    source = ColumnDataSource(data=dict(classes=list(sorted_class_counts.keys()), counts=list(sorted_class_counts.values()), colors=colors))
    
    p = figure(x_range=list(sorted_class_counts.keys()), tools="reset", width=1500)
    p.vbar(x='classes', top='counts', width=0.9, source=source, line_color="white", fill_color='colors')
    p.xgrid.grid_line_color = None
    p.y_range.start = 0
    p.xaxis.major_label_text_font_size = '0pt'
    p.xaxis.axis_label = "Třída"
    p.yaxis.axis_label = "Počet"
    p.add_tools(ZoomInTool(), ZoomOutTool())
    
    hover = HoverTool(tooltips=[("Třída", "@classes"), ("Počet", "@counts")], mode='vline')
    p.add_tools(hover)
    
    pp = column(p, sizing_mode="stretch_width")
    return pp

# Start threads for updating data and scheduled tasks
update_thread = threading.Thread(target=update_data)
update_thread.start()
schedule_thread = threading.Thread(target=schedule_update)
schedule_thread.start()

# Flask route for index page
@app.route('/')
def index():
    # Generate color palette
    color_palette = generate_colors_hex()
    
    # Get counts from MongoDB and directory
    sign_count = get_record_count()
    file_count = get_file_count_from_db()
    detected_count = get_detected_count_from_db()
    
    # Create Bokeh plot
    plot = create_bokeh_plot(pd.DataFrame(image_data), color_palette)
    
    # Generate Folium map
    map_page = map()
    
    # Process data for table
    table_data = process_data(pd.DataFrame(image_data), color_palette)
    
    # Generate Bokeh components
    script1, div1 = components(plot)
    
    return render_template("index.html", script1=script1, div1=div1, map_page=map_page, sign_count=sign_count, file_count=file_count, detected_count=detected_count, table_data=table_data)

# Main function to run Flask app
if __name__ == '__main__': 
    app.run()
