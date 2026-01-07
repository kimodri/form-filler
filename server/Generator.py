from PIL import Image, ImageDraw, ImageFont
from pdf2image import convert_from_path
import os


class Generator:
    def __init__(self, font_path="arial.ttf", font_size=30, poppler_path=None):
        self.font_size = font_size
        self.font_path = font_path
        self.poppler_path = poppler_path

    def _load_image(self, template_path):
        """
        Load image from file path, handling both images and PDFs.
        
        :param template_path: Path to the template (image or PDF)
        :return: PIL Image object
        """
        ext = template_path.lower().split(".")[-1]
        
        if ext == "pdf":
            # Convert PDF to images
            pages = convert_from_path(
                template_path,
                dpi=300,
                poppler_path=self.poppler_path
            )
            
            if not pages:
                raise ValueError(f"No pages found in PDF: {template_path}")
            
            if len(pages) > 1:
                print(f"Warning: PDF has {len(pages)} pages. Using only the first page.")
            
            return pages[0]  # Return first page as PIL Image
        
        elif ext in ("jpg", "jpeg", "png", "bmp", "tiff"):
            return Image.open(template_path)
        
        else:
            raise ValueError(f"Unsupported file format: {ext}. Supported: jpg, jpeg, png, pdf")

    def generate(self, template_path, mappings, user_profile, output_path):
        """
        Generate the text to be written on the blank spaces

        :param template_path: Path to the blank form (image or PDF)
        :param mappings: List of dicts from the Parser ({section, label, fill_target...})
        :param user_profile: Dict containing user data ({'Patient Information_Full Name': 'John Doe'})
        :param output_path: Where to save the result
        """

        try:
            image = self._load_image(template_path)
        except FileNotFoundError:
            print(f"Error: Could not find template at {template_path}")
            return
        except Exception as e:
            print(f"Error loading template: {e}")
            return
        
        draw = ImageDraw.Draw(image)

        for item in mappings:
            # Normalize key to match your database keys
            clean_key = item["label"].replace(":", "").strip()

            # Retrieve Data
            user_value = user_profile.get(clean_key)
            
            if user_value:
                self._draw_text(draw, item['fill_target'], user_value)
            else:
                print(f"Warning: No data found for field '{clean_key}'")

        # Save the result
        image.save(output_path)
        print(f"Generated form saved to: {output_path}")

    def _draw_text(self, draw_surface, box, text):
        """
        Helper to calculate position and font size, then draw.
        """
        x, y, w, h = box['x'], box['y'], box['w'], box['h']
        
        try:
            font = ImageFont.truetype(self.font_path, self.font_size)
        except IOError:
            # Fallback if font file is missing
            font = ImageFont.load_default()

        # Simple vertical centering calculation
        text_x = x + 25
        text_y = y + (h - self.font_size) // 2
        
        draw_surface.text((text_x, text_y), text, fill="black", font=font)