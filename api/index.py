# /api/index.py
from http.server import BaseHTTPRequestHandler
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import random
import math

# --- Configuration ---
EMAIL_ADDRESS = "TFA1974 (at) AOL (dotcom)"
IMAGE_WIDTH = 300
IMAGE_HEIGHT = 50
FONT_SIZE = 20
# --- End Configuration ---

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 1. Create a new image with a random light background color
        bg_color = (random.randint(220, 255), random.randint(220, 255), random.randint(220, 255))
        img = Image.new('RGB', (IMAGE_WIDTH, IMAGE_HEIGHT), color=bg_color)
        draw = ImageDraw.Draw(img)

        # 2. Select a random font
        # Tries a list of common fonts. OCR is weaker against varied fonts.
        font_names = ["DejaVuSans.ttf", "Arial.ttf", "Verdana.ttf", "Tahoma.ttf"]
        font = None
        for font_name in font_names:
            try:
                font = ImageFont.truetype(font_name, FONT_SIZE)
                break
            except IOError:
                continue
        if font is None:
            font = ImageFont.load_default()

        # 3. Add random noise (lines and dots) to the background
        for _ in range(random.randint(5, 10)):
            x1, y1 = random.randint(0, IMAGE_WIDTH), random.randint(0, IMAGE_HEIGHT)
            x2, y2 = random.randint(0, IMAGE_WIDTH), random.randint(0, IMAGE_HEIGHT)
            draw.line((x1, y1, x2, y2), fill=(random.randint(150, 220), random.randint(150, 220), random.randint(150, 220)), width=1)

        # 4. Draw text with warping, rotation, and jitter
        x_start = 15
        y_center = IMAGE_HEIGHT / 2
        
        # Sine wave parameters for warping effect
        amplitude = random.uniform(2.5, 4.5)
        frequency = random.uniform(0.08, 0.12)

        for i, char in enumerate(EMAIL_ADDRESS):
            # Calculate character position with sine wave warp
            y_offset = amplitude * math.sin(frequency * (x_start))
            char_y_pos = y_center + y_offset

            # Create a temporary image for the character to rotate it
            char_img = Image.new('RGBA', (FONT_SIZE*2, FONT_SIZE*2), (0, 0, 0, 0))
            char_draw = ImageDraw.Draw(char_img)
            
            text_color = (random.randint(10, 80), random.randint(10, 80), random.randint(10, 80))
            char_draw.text((10, 10), char, font=font, fill=text_color)
            
            # Rotate the character
            rotation_angle = random.uniform(-18, 18)
            rotated_char = char_img.rotate(rotation_angle, expand=1, resample=Image.BICUBIC)

            # Paste the rotated character onto the main image
            img.paste(rotated_char, (int(x_start), int(char_y_pos - FONT_SIZE/2)), rotated_char)
            
            # Advance x position for next character
            char_width, _ = draw.textlength(char, font=font)
            x_start += char_width + random.uniform(-2, 2) # Jitter spacing

        # 5. Draw random bezier curves over the text
        for _ in range(random.randint(3, 5)):
            x1, y1 = random.randint(0, IMAGE_WIDTH), random.randint(0, IMAGE_HEIGHT)
            x2, y2 = random.randint(0, IMAGE_WIDTH), random.randint(0, IMAGE_HEIGHT)
            ctrl_x1, ctrl_y1 = random.randint(0, IMAGE_WIDTH), random.randint(0, IMAGE_HEIGHT)
            ctrl_x2, ctrl_y2 = random.randint(0, IMAGE_WIDTH), random.randint(0, IMAGE_HEIGHT)
            curve_points = [(x1,y1), (ctrl_x1, ctrl_y1), (ctrl_x2, ctrl_y2), (x2, y2)]
            draw.line(curve_points, fill=(random.randint(50,150), random.randint(50,150), random.randint(50,150)), width=2)

        # 6. Save the image to a memory buffer
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        # 7. Serve the image
        self.send_response(200)
        self.send_header('Content-type', 'image/png')
        self.end_headers()
        self.wfile.write(buffer.getvalue())
        return
