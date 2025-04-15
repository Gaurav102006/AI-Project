# -*- coding: utf-8 -*-
"""Python Project

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1Wc-BifYFgG3mvaWu2-6gVPtZN1We2w3E
"""

# Install required packages
!pip install numpy pandas matplotlib scikit-learn opencv-python kaggle

# Import libraries
import os
import cv2
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.decomposition import PCA
from google.colab import files

# Setup Kaggle API (upload your kaggle.json first)
if not os.path.exists('/root/.kaggle/kaggle.json'):
    uploaded = files.upload()
    !mkdir -p ~/.kaggle
    !cp kaggle.json ~/.kaggle/
    !chmod 600 ~/.kaggle/kaggle.json

# Download and extract a smaller version of PlantVillage dataset
!kaggle datasets download -d emmarex/plantdisease
!unzip -q plantdisease.zip

import os
import cv2
import numpy as np
from google.colab.patches import cv2_imshow

# 1. FIND THE DATASET (with nested directory handling)
def find_plantvillage_data():
    # Check all possible locations
    search_paths = [
        '/content/plantvillage',
        '/content/PlantVillage',
        '/content/plantdisease',
        '/content/plantdisease.zip',
        '/content/plantvillage-dataset.zip'
    ]

    for path in search_paths:
        if os.path.exists(path):
            if path.endswith('.zip'):
                print(f"Found zip file at {path}, extracting...")
                !unzip -q {path} -d /content/extracted
                return '/content/extracted'

            # Check for nested PlantVillage folder
            nested = os.path.join(path, 'PlantVillage')
            if os.path.exists(nested):
                return nested
            return path

    # If nothing found, download fresh
    print("Downloading dataset...")
    !kaggle datasets download -d abdallahalidev/plantvillage-dataset
    !unzip -q plantvillage-dataset.zip
    return '/content/PlantVillage'

dataset_path = find_plantvillage_data()
print(f"Using dataset at: {dataset_path}")

# 2. FIND ALL IMAGES RECURSIVELY
def find_image_paths(root_path, max_per_class=50):
    image_paths = []
    class_names = []

    for root, dirs, files in os.walk(root_path):
        for file in files[:max_per_class]:
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                image_paths.append(os.path.join(root, file))
                class_names.append(os.path.basename(root))

    return image_paths, class_names

image_paths, class_names = find_image_paths(dataset_path)
print(f"Found {len(image_paths)} images across {len(set(class_names))} classes")

# 3. CREATE SIMPLIFIED CLASS MAPPING (for demo)
unique_classes = list(set(class_names))[:15]  # Only use 3 classes for demo
class_to_idx = {cls:i for i, cls in enumerate(unique_classes)}

# 4. LOAD IMAGES (with error handling)
def load_images(paths, classes, target_size=(64,64)):
    images = []
    labels = []

    for path, cls in zip(paths, classes):
        if cls not in class_to_idx:
            continue

        try:
            img = cv2.imread(path)
            if img is not None:
                img = cv2.resize(img, target_size)
                images.append(img.flatten())
                labels.append(class_to_idx[cls])
        except Exception as e:
            print(f"Error loading {path}: {e}")
            continue

    return np.array(images), np.array(labels)

X, y = load_images(image_paths, class_names)

if len(X) == 0:
    # Show directory structure for debugging
    print("Directory structure:")
    !find {dataset_path} -type d | head -20

    # Try alternative loading method
    print("\nTrying alternative approach...")
    sample_path = os.path.join(dataset_path, os.listdir(dataset_path)[0])
    sample_img = cv2.imread(os.path.join(sample_path, os.listdir(sample_path)[0]))
    cv2_imshow(sample_img)
    raise ValueError("Couldn't load any images. Please check the dataset structure.")
else:
    print(f"Successfully loaded {X.shape[0]} images")
    print(f"Class distribution: {np.bincount(y)}")

# Dataset is Doubled
def rotate_image(image,angle):
  rows,cols=image.shape[:2]
  m=cv2.getRotationMatrix2D((cols/2,rows/2),angle,1)
  return cv2.warpAffine(image,m,(cols,rows))

def flip_image(image,horizontal=True):
  if horizontal:
    return cv2.flip(image,1)
  else:
    return cv2.flip(image,0)

X_augmented = []
y_augmented = []

for i in range(len(X)):
    image = X[i].reshape(64, 64, 3)  # Reshape to original image dimensions
    label = y[i]

    # Apply rotations
    for angle in [15, 30, -15, -30]:
        rotated_image = rotate_image(image, angle)
        X_augmented.append(rotated_image.flatten())
        y_augmented.append(label)

    # Apply horizontal flip
    flipped_image = flip_image(image)
    X_augmented.append(flipped_image.flatten())
    y_augmented.append(label)

    # ... add more augmentations as needed

X_augmented = np.array(X_augmented)
y_augmented = np.array(y_augmented)

X_doubled = np.concatenate([X, X_augmented])
y_doubled = np.concatenate([y, y_augmented])

# Reduce dimensions to make training faster
pca = PCA(n_components=100)  # Keep top 100 components
X_reduced = pca.fit_transform(X_doubled)

print(f"Reduced from {X.shape[1]} to {X_reduced.shape[1]} dimensions")

# Split data into train/test sets
X_train, X_test, y_train, y_test = train_test_split(X_reduced, y_doubled, test_size=0.2, random_state=200)

model=RandomForestClassifier(n_estimators=500, random_state=200)
model.fit(X_train, y_train)

y_pred=model.predict(X_test)

# First, let's verify our classes
print("Actual classes found:", unique_classes)  # This should show all 15 classes

# If classes is empty or incorrect, recreate it from the data
if len(unique_classes) != len(np.unique(y_test)):
    classes = [f"class_{i}" for i in range(len(np.unique(y_test)))]
    print("Using generated class names:", classes)

# Now run evaluation with proper class alignment
print("\nModel Evaluation:")
print("Accuracy:", accuracy_score(y_test, y_pred))
print("\nClassification Report:")
print(classification_report(y_test, y_pred, target_names=unique_classes))

# Add a confusion matrix for better visualization
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
import matplotlib.pyplot as plt

cm = confusion_matrix(y_test, y_pred)
disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=unique_classes)
disp.plot(cmap=plt.cm.Blues,xticks_rotation=90)
plt.title("Confusion Matrix")
plt.show()

def predict_disease(image_path):
    # Load and preprocess image
    img = cv2.imread(image_path)
    img = cv2.resize(img, (64, 64))
    img_flat = img.flatten().reshape(1, -1)
    img_reduced = pca.transform(img_flat)

    # Predict
    pred = model.predict(img_reduced)[0]
    proba = model.predict_proba(img_reduced)[0]

    # Display results
    plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    plt.axis('off')
    plt.show()

    print("\nPrediction Results:")
    for i, cls in enumerate(unique_classes):
        print(f"{cls}: {proba[i]*100:.1f}%")
    print(f"\nMost likely: {unique_classes[pred]} ({proba[pred]*100:.1f}% confidence)")

    predicted_plant = unique_classes[pred]

# Test with an example (upload your own image)
uploaded = files.upload()
test_image = list(uploaded.keys())[0]
predict_disease(test_image)
