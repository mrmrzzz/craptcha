from http.server import BaseHTTPRequestHandler
from io import BytesIO
from urllib.parse import urlparse, parse_qs
from PIL import Image, ImageDraw, ImageFont
import os
import random

DEFAULT_TEXT = "MVP"
MAX_TEXT_LENGTH = 50

IMAGE_WIDTH = 400
IMAGE_HEIGHT = 100

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # --- URL Parsing ---
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)
        text_to_render = query_params.get('text', [DEFAULT_TEXT])[0]
        
        if len(text_to_render) > MAX_TEXT_LENGTH:
            text_to_render = text_to_render[:MAX_TEXT_LENGTH]

        # --- Basic Image Setup ---
        bg_color = (240, 240, 240)
        final_img = Image.new('RGB', (IMAGE_WIDTH, IMAGE_HEIGHT), color=bg_color)
        draw = ImageDraw.Draw(final_img)
        
        # --- Font Loading ---
        script_dir = os.path.dirname(__file__)
        font_path = os.path.join(script_dir, "fonts/DejaVuSans-Bold.ttf")
        
        try:
            # Load one font, once.
            font = ImageFont.truetype(font_path, 36)
        except IOError:
            # If font loading fails, use a basic default and report error
            font = ImageFont.load_default()
            text_to_render = "Error: Font not found."

        # --- Simple Text Drawing ---
        text_bbox = draw.textbbox((0, 0), text_to_render, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        x_pos = (IMAGE_WIDTH - text_width) / 2
        y_pos = (IMAGE_HEIGHT - text_height) / 2
        
        draw.text((x_pos, y_pos), text_to_render, font=font, fill=(50, 50, 50))
        
        # --- Response ---
        buffer = BytesIO()
        final_img.save(buffer, format="PNG")
        
        self.send_response(200)
        self.send_header('Content-type', 'image/png')
        self.end_headers()
        self.wfile.write(buffer.getvalue())
        return
