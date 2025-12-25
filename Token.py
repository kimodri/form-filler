from pdf2image import convert_from_path
import os
import pytesseract
from pytesseract import Output
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

POPPLER_PATH = os.getenv("POPPLER_PATH")
pytesseract.pytesseract.tesseract_cmd = os.getenv("PYTESSERACT_PATH")

class Token:
    def __init__(self, type, value, bbox):
        self.type = type   # e.g., "FIELD_LABEL"
        self.value = value # e.g., "Name:"
        self.bbox = bbox   # (x, y, w, h)

def main():
    pages = convert_from_path(
        "./forms/Employment_Application.pdf", 
        300,
        poppler_path=POPPLER_PATH
    )

    data = pytesseract.image_to_data(pages[0], output_type=Output.DICT)
    
    # Print the first few words detected to prove it works
    # print("Detected text data keys:", data.keys())
    # print("First 5 words found:", data['width'][:20])
    df = pd.DataFrame(data)
    print(df.head(20))

if __name__ == "__main__":
    main()