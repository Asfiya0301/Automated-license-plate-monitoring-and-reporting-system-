import cv2
import pytesseract
from PIL import Image
import numpy as np

# Path to Tesseract executable (adjust this path for your system)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Preprocess the image for better OCR accuracy
def preprocess_image(image_path):
    # Load the image using OpenCV
    image = cv2.imread(image_path)

    # Convert the image to grayscale
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply thresholding to make the image binary (black & white)
    _, binary_image = cv2.threshold(gray_image, 128, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Optionally, apply noise removal using a median filter or morphological operations
    filtered_image = cv2.medianBlur(binary_image, 3)

    return filtered_image

# Extract handwritten text using Tesseract OCR
def extract_handwritten_text(image_path):
    # Preprocess the image
    preprocessed_image = preprocess_image(image_path)

    # Use Tesseract OCR to extract text from the image
    text = pytesseract.image_to_string(preprocessed_image, config='--psm 6')

    return text
# Example usage
image_path = '5.jpeg'
handwritten_text = extract_handwritten_text(image_path)
print("Extracted  Text:")
print(handwritten_text)