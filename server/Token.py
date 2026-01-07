from pdf2image import convert_from_path
import os
import pytesseract
from pytesseract import Output
from dotenv import load_dotenv
import numpy as np
import cv2
from textwrap import dedent

from Parser import Parser
from Generator import Generator

load_dotenv()

POPPLER_PATH = os.getenv("POPPLER_PATH")
pytesseract.pytesseract.tesseract_cmd = os.getenv("PYTESSERACT_PATH")

class Token:
    def __init__(self, id, type, value, bbox, page=0):
        self.id = id
        self.type = type
        self.value = value
        self.bbox = bbox  # (x, y, w, h)
        self.page = page


    def __str__(self):
        return f"id: {self.id}, type: {self.type}, value: {self.value}, x: {self.bbox[0]}, y: {self.bbox[1]}, w: {self.bbox[2]}, h: {self.bbox[3]}, page: {self.page}"

class Tokenizer:

    def __init__(self, file_path, poppler_path=POPPLER_PATH, pytesseract_path=pytesseract.pytesseract.tesseract_cmd):
        self.file_path = file_path
        self.poppler_path  = poppler_path
        self.pytesseract_path = pytesseract_path
        self.img = None

    def __str__(self):
        return dedent(f"""Tokenizer: 
    - Poppler path at {self.poppler_path}, 
    - Pytesseract path at {self.pytesseract_path}
    - Attempting to tokenize file {self.file_path}""")

    def _check_extension(self, file_path):
        valid_ext = ("jpg", "png", "jpeg", "pdf")
        if not self.file_path.endswith(valid_ext):
            raise()
        else:
            ext = file_path.split(".")[-1]
            return ext

    def _pil_to_cv(self, pil_img):
        return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    
    def _get_dimensions(self):
        """Returns (height, width) of the last processed image"""
        if self.img is not None:
            height, width = self.img.shape[:2]
            return height, width
        return None, None

    def tokenize_file(self, output_path=None):
        ext = self._check_extension(self.file_path)

        all_tokens = []
        dimensions = []
        page_offset_y = 0

        if ext == "pdf":
            pages = convert_from_path(
                self.file_path,
                300,
                poppler_path=self.poppler_path
            )

            # if len(pages) > 1:
            #     raise()
            
            for page_index, page in enumerate(pages):
                self.img = self._pil_to_cv(page)
                if self.img is not None:
                    page_height, page_width = self._get_dimensions()
                    dimensions.append((page_height, page_width))

                if output_path is not None:
                    n = len(pages)
                    # Get the base filename without the path or extension
                    base_name = os.path.basename(self.file_path).split(".")[0]
                    
                    # Create a unique filename for the specific page
                    # Example: ../form_images/personal_data_sheet_page_0.png
                    if n > 1:
                        file_name = f"{base_name}_page_{page_index}.png"
                    else:
                        file_name = f"{base_name}.png"    
                    destination = os.path.join(output_path, file_name)
                    
                    # Save using the 'destination' path, not the folder 'output_path'
                    page.save(destination, 'PNG')

                data = pytesseract.image_to_data(
                    self.img,
                    output_type=Output.DICT
                )

                textual_tokens = self._process_ocr_data(
                    data,
                    width=page_width,
                    page=page
                )

                visual_tokens = self._get_visual_token(self.img, page)
 
                page_tokens = self._merge_and_sort(
                    textual_tokens,
                    visual_tokens
                )

                # Apply Y offset so pages don't overlap
                for t in page_tokens:
                    x, y, w, h = t.bbox
                    t.bbox = (x, y + page_offset_y, w, h)

                all_tokens.extend(page_tokens)
                page_offset_y += page_height

            return all_tokens, dimensions

        else:  # meaning if the file uploaded is not pdf then use OpenCV
            self.img = cv2.imread(self.file_path)
            
            if self.img is not None:
                page_height, page_width = self._get_dimensions()
                dimensions.append((page_height, page_width))

            data = pytesseract.image_to_data(
                self.img,
                output_type=Output.DICT
            )

            textual_tokens = self._process_ocr_data(
                data,
                width=page_width,
            )

            visual_tokens = self._get_visual_token(self.img)

            final_tokens = self._merge_and_sort(
                textual_tokens,
                visual_tokens
            )

            return final_tokens, dimensions

    def _process_ocr_data(self, data, width, page=0, gap_threshold=27):
        """
        Groups Tesseract words into lines based on Block+Paragraph+Line
        then splits them horizontally if a large gap is detectec.
        
        :param self: The instance of the class
        :param data: Data from doing an OCR to an image
        """

        raw_lines = {}
        n_boxes = len(data['text'])
        
        for i in range(n_boxes):
            # Skip empty text or low confidence garbage
            if int(data['conf'][i]) == -1 or not data['text'][i].strip():
                continue
            
            # Creating an ID (key) for each word
            line_id = f"{data['block_num'][i]}_{data['par_num'][i]}_{data['line_num'][i]}"
            
            word_info = {
                "text": (data['text'][i].replace("_", "")).strip(),
                "left": data['left'][i],
                "top": data['top'][i],
                "width": data['width'][i],
                "right": data['left'][i] + data['width'][i],
                "height": data['height'][i]
            }
            
            if line_id not in raw_lines:
                raw_lines[line_id] = []
            raw_lines[line_id].append(word_info)


        # Process each line: Merge words, but split on huge gaps
        final_tokens = []

        for line_id, words in raw_lines.items():
            # Ensure words are sorted left-to-right (Tesseract usually does this, but be safe)
            words.sort(key=lambda w: w['left'])
            
            # Initialize the first phrase with the first word
            current_phrase_text = words[0]['text']
            current_phrase_bbox = [words[0]['left'], words[0]['top'], words[0]['width'], words[0]['height']]
            last_word_right = words[0]['right']

            for i in range(1, len(words)):
                word = words[i]
                
                # Calculate the gap between the end of the last word and start of this one
                gap = word['left'] - last_word_right
                
                # DECISION: Is this a new field on the same line?
                if gap > gap_threshold:
                    # YES: The gap is huge (e.g., between "Name:" and "Phone:")
                    # 1. Save the previous phrase as a complete token
                    
                    token_type = ""
                    token_id=0

                    if (current_phrase_text.strip().endswith(":")):
                        token_type = "FIELD_LABEL"
                        token_id = 3
                    else:
                        token_type = "NOTE"
                        token_id = 5
                    
                    final_tokens.append( #{
                        Token(
                            id = token_id,
                            type = token_type,
                            value = current_phrase_text,
                            bbox=(current_phrase_bbox[0], 
                                  current_phrase_bbox[1], 
                                  current_phrase_bbox[2], 
                                  current_phrase_bbox[3],),
                            page=page
                        ))
                        # "id": token_id,
                        # "type": token_type,
                        # "value": current_phrase_text,
                        # "x": current_phrase_bbox[0],
                        # "y": current_phrase_bbox[1],
                        # "w": current_phrase_bbox[2],
                        # "h": current_phrase_bbox[3]
                    #})
                    
                    # 2. Start a completely new phrase for the current word
                    current_phrase_text = word['text']
                    # Reset bbox to this new word's geometry
                    current_phrase_bbox = [word['left'], word['top'], word['width'], word['height']]
                    
                else:
                    # NO: The gap is small. It's part of the same sentence.
                    current_phrase_text += " " + word['text']
                    
                    # Expand the width of the current phrase to include this word
                    # New Width = (Word Right Edge) - (Phrase Left Edge)
                    current_phrase_bbox[2] = word['right'] - current_phrase_bbox[0]
                    
                    # Update height to be the max height seen (optional, but good for bounding boxes)
                    current_phrase_bbox[3] = max(current_phrase_bbox[3], word['height'])
                
                # Update tracker for the next iteration
                last_word_right = word['right']


            # Append the final phrase of the line after the loop finishes
            token_type = ""
            token_id = 0

            if (current_phrase_text.strip().endswith(":")):
                token_type = "FIELD_LABEL"
                token_id = 3
            else:
                token_type = "NOTE"
                token_id = 5
                
            final_tokens.append( #{
                        Token(
                            id = token_id,
                            type = token_type,
                            value = current_phrase_text,
                            bbox=(current_phrase_bbox[0], 
                                  current_phrase_bbox[1], 
                                  current_phrase_bbox[2], 
                                  current_phrase_bbox[3],),
                            page=page
                        ))
                        # "id": token_id,
                        # "type": token_type,
                        # "value": current_phrase_text,
                        # "x": current_phrase_bbox[0],
                        # "y": current_phrase_bbox[1],
                        # "w": current_phrase_bbox[2],
                        # "h": current_phrase_bbox[3]
                    #})


        # Clean the final tokens
        notes = [t for t in final_tokens if t.type == "NOTE"]
        if not notes:
            return final_tokens

        heights = np.array([t.bbox[3] for t in notes])
        median_h = np.median(heights)

        PAGE_WIDTH = width
        TOP_REGION = 350  # Stricter threshold for top of page

        def is_form_title(t, notes, median_h):
            """Form title is the topmost element that's prominent"""
            # Find the note with minimum Y coordinate (topmost)
            topmost_y = min(note.bbox[1] for note in notes)
            
            # Check if this token is the topmost one (or very close to it)
            is_topmost = abs(t.bbox[1] - topmost_y) < 50  # Allow 50px tolerance
            
            return (
                is_topmost and                                # Must be at the top
                t.bbox[1] < TOP_REGION and                    # In top region
                t.bbox[3] >= median_h * 0.90 and              # Taller than typical notes
                t.bbox[2] >= 0.20 * PAGE_WIDTH and            # Reasonably wide
                len(t.value.split()) >= 2                     # Multi-word
            )

        def is_section_title(t, median_h):
            """Section titles are wider than labels but not as prominent as form title"""
            return (
                t.bbox[3] >= median_h * 0.75 and              # Similar height to notes
                t.bbox[2] >= 0.20 * PAGE_WIDTH and            # Wider than typical labels
                len(t.value.split()) <= 6 and                 # Reasonable word count
                not t.value.strip().endswith(":")             # Exclude field labels
            )

        # Classify tokens
        for t in final_tokens:
            if t.type != "NOTE":
                continue

            if is_form_title(t, notes, median_h):
                t.type = "FORM_TITLE"
                t.id = 1
            elif is_section_title(t, median_h):
                t.type = "SECTION_TITLE"
                t.id = 2

        return final_tokens

    # OpenCV Implementation
    def _get_visual_token(self, img, page=0):

        # img = cv2.imread(self.file_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # binary image (invert so lines are white)
        _, bw = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)

        # Detect horizontal lines
        h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
        h_lines = cv2.morphologyEx(bw, cv2.MORPH_OPEN, h_kernel)

        # Detect vertical lines
        v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
        v_lines = cv2.morphologyEx(bw, cv2.MORPH_OPEN, v_kernel)

        # Combine lines
        lines = cv2.add(h_lines, v_lines)

        # Find contours
        contours, _ = cv2.findContours(lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        visual_tokens = []
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            if w > 100 and h > 5:
                # Store as a dictionary or object to match your Token style
                # visual_tokens.append({
                #     'type': 'FIELD_SPACE', # or CHECKBOX depending on shape
                #     'value': '____',
                #     'x': x, 'y': y, 'w': w, 'h': h
                # })

                visual_tokens.append(
                    Token(
                        id = 4,
                        type = "FIELD_SPACE",
                        value = "____",
                        bbox = (x, y, w, h),
                        page=page
                    )
                )

        # CRITICAL STEP: SORT BY Y (Top-to-Bottom), THEN X (Left-to-Right)
        # We use y // 10 to allow for slight "wobble" in alignment (Row Clustering)
        visual_tokens.sort(key=lambda b: (b.bbox[1] // 10, b.bbox[0]))
        return visual_tokens

    def _merge_and_sort(self, textual_tokens, visual_tokens, row_tolerance=40):
        
        # 1. Unified List
        all_tokens = textual_tokens + visual_tokens

        # 2. Initial Sort by Y (Top to Bottom)
        # This gets them roughly in order so we can cluster them
        all_tokens.sort(key=lambda t: t.bbox[1])  # t.bbox[1] == y

        rows = []
        current_row = []
        
        # We track the "average Y" of the current row to handle drift
        current_row_y = 0 

        if all_tokens:
            current_row = [all_tokens[0]]
            current_row_y = all_tokens[0].bbox[1]

        for i in range(1, len(all_tokens)):
            token = all_tokens[i]
            
            # 3. Check Vertical Distance
            # If this token is within 'row_tolerance' pixels of the current row's Y...
            if abs(token.bbox[1] - current_row_y) <= row_tolerance:
                current_row.append(token)
                
                # Optional: Update average Y (moving average) to follow the line's drift
                # current_row_y = (current_row_y + token['y']) / 2
            else:
                # It's a new line! 
                # a. Sort the OLD row by X (Left to Right)
                current_row.sort(key=lambda t: t.bbox[0])
                rows.append(current_row)
                
                # b. Start the NEW row
                current_row = [token]
                current_row_y = token.bbox[1]

        # Don't forget the last row
        if current_row:
            current_row.sort(key=lambda t: t.bbox[0])
            rows.append(current_row)

        # 4. Flatten into a single stream
        # This turns [[Row1_Item1, Row1_Item2], [Row2_Item1]] into [Item1, Item2, Item1...]
        final_stream = [token for row in rows for token in row]
        
        return final_stream

    def _visualize_file(self, tokens, img=None):

        if img == None:
            img = self.img
        # DO NOT reload the image inside the loop
        for t in tokens:
            x, y, w, h = t.bbox

            # COLOR CODING SCHEME (BGR)
            if t.type == 'FIELD_SPACE':
                color = (0, 0, 255)      # Red
                thickness = 2
            elif t.type == 'CHECKBOX':
                color = (0, 0, 255)
                thickness = 2
            elif t.type == 'FIELD_LABEL':
                color = (0, 255, 0)      # Green
                thickness = 2
            elif t.type == 'SECTION_TITLE':
                color = (255, 0, 0)      # Blue
                thickness = 3
            else:
                color = (255, 255, 0)
                thickness = 1

            # Draw rectangle
            cv2.rectangle(img, (x, y), (x + w, y + h), color, thickness)

            # Draw label
            label_text = f"{t.type}"
            cv2.putText(
                img,
                label_text,
                (x, y - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.4,
                color,
                1
            )
    # Save ONCE, after all drawings
        cv2.imwrite("../detections/final_detected1.jpg", img)

def main():
    # path = "../forms/personal_data_sheet.pdf"
    # path = "../forms/bg_verification_form.pdf"
    # path = "../forms/employment_application_form.pdf"
    # path = "../forms/contact_form.pdf"
    # path = "../forms/onboarding_form.pdf"

    # path = "../form_images/personal_data_sheet.png"
    # path = "../form_images/bg_verification_form.png"
    # path = "../form_images/employment_application_form.png"
    # path = "../form_images/contact_form.png"
    # path = "../form_images/onboarding_form.png"

    path = "../onboarding_form.pdf"

    # path = "../medical_form.jpg"
    
    tokenizer = Tokenizer(path)
    print(tokenizer) 
    tokens, dimensions = tokenizer.tokenize_file()

    # img = cv2.imread(path)
    tokenizer._visualize_file(tokens)

    print(dimensions)
    for token in tokens:
        print(token)

    parser = Parser()

    accepted, errors = parser(tokens)
    print(errors)

    if accepted:
        print("Form Accepted, now generating ...")

        user = {
            "Full Name": "Juan Dela Cruz",
            "Date of Birth": "1990-05-15",
            "Gender": "Lalaki",
            "Nationality": "Pilipino",
            
            "Email Address": "juan.delacruz@example.com",
            "Phone Number": "+63 912 345 6789",
            "Alternate Phone": "+63 998 765 4321",
            "Address": "123 Mabini Street, Barangay Malinis, Quezon City, Metro Manila, Pilipinas",
            
            "Highest Education Level": "Kolehiyo",
            "School": "Unibersidad ng Pilipinas",
            "Course/Program": "Inhinyeriyang Elektrikal",
            "Year Graduated": "2012",
            
            "Current Employer": "San Miguel Corporation",
            "Job Title": "Senior Software Engineer",
            "Years of Experience": "10",
            "Monthly Salary": "₱80,000",
            
            "SSS Number": "34-5678901-2",
            "TIN Number": "123-456-789",
            "PhilHealth Number": "12-345678901-2",
            "Pag-IBIG Number": "1234-5678-9012"
        }
        gen = Generator()

        gen.generate(path, parser.mappings, user, "../filled_out_form1.jpg")

    else:
        print("Not Accepted")
    
    print(parser.mappings)

if __name__ == "__main__":
    main()