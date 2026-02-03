# app/utils/file_utils.py
import os
from PIL import Image
import numpy as np

def load_image(file_path: str) -> np.ndarray:
    img = Image.open(file_path)
    return np.array(img)