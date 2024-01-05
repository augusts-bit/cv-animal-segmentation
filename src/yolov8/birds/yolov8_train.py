
"""YOLOv8_SAHI.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1Xuecuiu4n3ObxuL8cLmHhmfAKKIX2nui
"""

# Based on https://github.com/computervisioneng/image-segmentation-yolov8/

# ------------------------------------------------------------------------------------- #
# Import
# ------------------------------------------------------------------------------------- #

import os, re, random
import cv2
from ultralytics import YOLO
# from utils.datasets import *
import yaml
import torch
from PIL import Image
import matplotlib.pyplot as plt
import numpy as np
from pathlib import *
import argparse # Parse arguments given to job

# ==============================================================

# Load inputs given to job

# ==============================================================

# This is how you load input from job
# https://learn.microsoft.com/en-us/azure/machine-learning/tutorial-train-model?view=azureml-api-2 

# input and output arguments
parser = argparse.ArgumentParser()

# Training data
parser.add_argument("--traindata")
parser.add_argument("--epochs", type=int, default=10)
parser.add_argument("--batch", type=int, default=3)
parser.add_argument("--lr0", type=float, default=0.00025)
args = parser.parse_args()

print(os.listdir(args.traindata))

# ==============================================================

# Check what species are in dataset

# ==============================================================

ann_dir = os.path.join(args.traindata, "annotations")
ann_files = sorted([f for f in os.listdir(ann_dir) if f.endswith('.txt')])

categories = []
for ann_file in ann_files:

       # Get annotations: bounding box, segmentation (mask) and label
        with open(os.path.join(ann_dir, ann_file), "r") as file:
            annotations = file.readlines()

            # Get category
            for annotation in annotations:
                # Process each line in the file
                if annotation.startswith('Original label'):

                    # Extract category
                    match = re.search(r'Original label for object \d+ : "(.*?)"', annotation)
                    if match:
                        label = match.group(1)
                        categories.append(label)

soorten = sorted(list(set(categories)))
print("Dataset contains:", soorten)

# ------------------------------------------------------------------------------------- #
# Split train-validation and create yaml
# ------------------------------------------------------------------------------------- #

# Rename images and labels to folder to lowercase (necessary?)
# os.rename(os.path.join(args.traindata, "Images"), os.path.join(args.traindata, "images"))
# os.rename(os.path.join(args.traindata, "Labels"), os.path.join(args.traindata, "labels"))

# See https://github.com/ultralytics/yolov5/issues/1579

IMG_FORMATS = 'bmp', 'dng', 'jpeg', 'jpg', 'mpo', 'png', 'tif', 'tiff', 'webp', 'pfm'  # include image suffixes

def img2label_paths(img_paths):
    # Define label paths as a function of image paths
    sa, sb = f'{os.sep}Images{os.sep}', f'{os.sep}Labels{os.sep}'  # /images/, /labels/ substrings
    return [sb.join(x.rsplit(sa, 1)).rsplit('.', 1)[0] + '.txt' for x in img_paths]

def autosplit(path, weights, annotated_only=False):
    """ Autosplit a dataset into train/val/test splits and save path/autosplit_*.txt files
    Usage: from utils.dataloaders import *; autosplit()
    Arguments
        path:            Path to images directory 
                        --> assumes that the corresponding labels is in the same parent directory /labels/ 
        weights:         Train, val, test weights (list, tuple)
        annotated_only:  Only use images with an annotated txt file
    """
    path = Path(path)  # images dir
    files = sorted(x for x in path.rglob('*.*') if x.suffix[1:].lower() in IMG_FORMATS)  # image files only
    n = len(files)  # number of files
    random.seed(0)  # for reproducibility
    indices = random.choices([0, 1, 2], weights=weights, k=n)  # assign each image to a split

    txt = ['autosplit_train.txt', 'autosplit_val.txt', ]  # 2 txt files
    for x in txt:
        if (path.parent / x).exists():
            (path.parent / x).unlink()  # remove existing

    print(f'Autosplitting images from {path}' + ', using *.txt labeled images only' * annotated_only)
    for i, img in zip(indices, files):
        if not annotated_only or Path(img2label_paths([str(img)])[0]).exists():  # check label
            with open(path.parent / txt[i], 'a') as f:
                f.write(f'./{img.relative_to(path.parent).as_posix()}' + '\n')  # add image to txt file

autosplit(os.path.join(args.traindata, "Images"), weights=(0.9, 0.1, 0.0))

data = {
    'path': args.traindata, # root path, start at home directory
    'train': os.path.join(args.traindata, "autosplit_train.txt"),
    'val': os.path.join(args.traindata, "autosplit_val.txt"),
    'nc': 1, # number of classes
    'names': ['bird']
}

with open(os.path.join(args.traindata, "config.yaml"), 'w') as file:
    yaml.dump(data, file, default_flow_style=False)

# ------------------------------------------------------------------------------------- #
# Train YOLOv8
# ------------------------------------------------------------------------------------- #

# load a pretrained model (recommended for training)
model = YOLO('yolov8n-seg.pt')

# arguments for training (see https://docs.ultralytics.com/modes/train/#arguments)
args = {"data": os.path.join(args.traindata, "config.yaml"),
        "epochs": args.epochs, "batch": args.batch, "lr0": args.lr0,
        "project": "./outputs", "exist_ok": True} # model will be saved in './outputs' folder in Azure

# train
model.train(**args)

# model weights: '/outputs/weights/best.pt'
# model yaml: '/outputs/args.yaml'
