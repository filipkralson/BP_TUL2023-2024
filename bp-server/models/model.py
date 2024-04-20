import numpy as np
from PIL import Image
import os
import pandas as pd
from sklearn.model_selection import train_test_split
from keras.utils import to_categorical
from keras.models import Sequential
from keras.layers import Conv2D, MaxPool2D, Dense, Flatten, Dropout

# Data preparation
data = []
labels = []
classes = 62
cur_path = os.getcwd()

for i in range(classes):
    path = os.path.join(cur_path, "GTSRB/train", str(i))
    images = os.listdir(path)
    for a in images:
        try:
            image = Image.open(os.path.join(path, a))
            image = image.resize((32, 32))
            image = np.array(image)
            data.append(image)
            labels.append(i)
            print(i, a)
        except Exception as e:
            print(f"Error loading image: {e}")

data = np.array(data)
labels = np.array(labels)
print(data.shape, labels.shape)

# Splitting data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(
    data, labels, test_size=0.2, random_state=42)
print(X_train.shape, X_test.shape, y_train.shape, y_test.shape)

# Convert labels to one-hot encoding
y_train = to_categorical(y_train, 62)
y_test = to_categorical(y_test, 62)

# Model definition
model = Sequential()
model.add(Conv2D(filters=32, kernel_size=(5, 5),
          activation='relu', input_shape=X_train.shape[1:]))
model.add(Conv2D(filters=32, kernel_size=(5, 5), activation='relu'))
model.add(MaxPool2D(pool_size=(2, 2)))
model.add(Dropout(rate=0.25))
model.add(Conv2D(filters=64, kernel_size=(3, 3), activation='relu'))
model.add(Conv2D(filters=64, kernel_size=(3, 3), activation='relu'))
model.add(MaxPool2D(pool_size=(2, 2)))
model.add(Dropout(rate=0.25))
model.add(Flatten())
model.add(Dense(256, activation='relu'))
model.add(Dropout(rate=0.5))
model.add(Dense(62, activation='softmax'))

# Compile the model
model.compile(loss='categorical_crossentropy',
              optimizer='adam', metrics=['accuracy'])

# Train the model
epochs = 15
history = model.fit(X_train, y_train, batch_size=32, epochs=epochs,
                    validation_data=(X_test, y_test))

# Save the trained model
model.save("traffic_classifier.h5")

# Load test data
test_data = pd.read_csv('Test.csv')
labels = test_data["ClassId"].values
image_paths = test_data["Path"].values

# Process test images
test_images = []
for img_path in image_paths: 
    image = Image.open(img_path)
    image = image.resize((32, 32))
    test_images.append(np.array(image)) 

# Convert test data to numpy array
X_test_final = np.array(test_images)

# Make predictions
predictions = model.predict(X_test_final)
predicted_classes = np.argmax(predictions, axis=1)

# Save the updated model
model.save("traffic_classifier_updated.h5")
