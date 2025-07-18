from http.server import BaseHTTPRequestHandler
from io import BytesIO
from urllib.parse import urlparse, parse_qs
from PIL import Image, ImageDraw, ImageFont
import random
import math
import os

DEFAULT_TEXT = "No Text Provided"
MAX_TEXT_LENGTH = 50

IMAGE_WIDTH = 400
IMAGE_HEIGHT = 100

INITIAL_FONT_SIZE = 48
HORIZONTAL_PADDING = 2
VERTICAL_PADDING = 2
DESIRED_AMPLITUDE_MAX = 8.0
DESIRED_SPACING_MIN = -5.0
DESIRED_SPACING_MAX = 5.0
DESIRED_ROTATION_MIN = -35
DESIRED_ROTATION_MAX = 35
BULGE_FACTOR = 0.5

class handler(BaseHTTPRequestHandler):

    def font_exists(self, font_name):
        script_dir = os.path.dirname(__file__)
        return os.path.exists(os.path.join(script_dir, font_name))

    def calculate_max_width(self, draw, text, font_list):
        max_font_width = 0
        for char in text:
            char_width = max(draw.textlength(char, font=font) for font in font_list)
            max_font_width += char_width + DESIRED_SPACING_MAX
        return max_font_width

    def apply_bulge_distortion(self, image, factor):
        width, height = image.size
        distorted_image = Image.new('RGBA', image.size)
        center_x, center_y = width / 2.0, height / 2.0
        max_radius = min(center_x, center_y)

        for y in range(height):
            for x in range(width):
                dx = x - center_x
                dy = y - center_y
                distance = math.sqrt(dx * dx + dy * dy)

                if distance <= max_radius:
                    r = distance / max_radius
                    new_r = r - (r * factor * (distance - max_radius) / max_radius)
                    theta = math.atan2(dy, dx)
                    src_x = int(center_x + new_r * max_radius * math.cos(theta))
                    src_y = int(center_y + new_r * max_radius * math.sin(theta))
                    if 0 <= src_x < width and 0 <= src_y < height:
                        pixel = image.getpixel((src_x, src_y))
                        distorted_image.putpixel((x, y), pixel)
                else:
                    pixel = image.getpixel((x, y))
                    distorted_image.putpixel((x, y), pixel)
        return distorted_image

    def do_GET(self):
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)
        text_to_render = query_params.get('text', [DEFAULT_TEXT])[0]
        
        if len(text_to_render) > MAX_TEXT_LENGTH:
            text_to_render = text_to_render[:MAX_TEXT_LENGTH]

        bg_color = (random.randint(220, 255), random.randint(220, 255), random.randint(220, 255))
        final_img = Image.new('RGB', (IMAGE_WIDTH, IMAGE_HEIGHT), color=bg_color)
        text_layer = Image.new('RGBA', (IMAGE_WIDTH, IMAGE_HEIGHT), (0,0,0,0))
        draw = ImageDraw.Draw(text_layer)
        
        script_dir = os.path.dirname(__file__)
        font_names = [
            os.path.join("fonts", "DejaVuSans-Bold.ttf"),
            os.path.join("fonts", "DejaVuSerif-Bold.ttf")
        ]
        
        available_font_paths = [os.path.join(script_dir, name) for name in font_names if self.font_exists(os.path.join(script_dir, name))]
        if not available_font_paths:
            raise IOError("Fonts not found in deployment package.")

        current_font_size = INITIAL_FONT_SIZE
        while current_font_size > 10:
            font_list_check = [ImageFont.truetype(path, current_font_size) for path in available_font_paths]
            max_width = self.calculate_max_width(ImageDraw.Draw(Image.new('RGB',(1,1))), text_to_render, font_list_check)
            if max_width < (IMAGE_WIDTH - HORIZONTAL_PADDING * 2):
                break
            current_font_size -= 1
        
        final_font_size = current_font_size
        final_font_list = [ImageFont.truetype(path, final_font_size) for path in available_font_paths]

        char_configs = []
        actual_width = 0
        for char in text_to_render:
            font = random.choice(final_font_list)
            spacing = random.uniform(DESIRED_SPACING_MIN, DESIRED_SPACING_MAX)
            width = draw.textlength(char, font=font)
            actual_width += width + spacing
            char_configs.append({'char': char, 'font': font, 'width': width, 'spacing': spacing})
        
        x_start = (IMAGE_WIDTH - actual_width) / 2
        y_center = IMAGE_HEIGHT / 2
        current_x = x_start

        for config in char_configs:
            y_offset = random.uniform(-DESIRED_AMPLITUDE_MAX, DESIRED_AMPLITUDE_MAX)
            char_y_pos = y_center + y_offset
            
            char_img = Image.new('RGBA', (final_font_size * 2, final_font_size * 2))
            char_draw = ImageDraw.Draw(char_img)
            text_color = (random.randint(10, 80), random.randint(10, 80), random.randint(10, 80))
            char_draw.text((final_font_size/2, final_font_size/2), config['char'], font=config['font'], fill=text_color)
            
            rotation = random.uniform(DESIRED_ROTATION_MIN, DESIRED_ROTATION_MAX)
            rotated_char = char_img.rotate(rotation, expand=True, resample=Image.BICUBIC)
            
            text_layer.paste(rotated_char, (int(current_x), int(char_y_pos - rotated_char.height / 2)), rotated_char)
            current_x += config['width'] + config['spacing']

        distorted_text_layer = self.apply_bulge_distortion(text_layer, BULGE_FACTOR)
        final_img.paste(distorted_text_layer, (0,0), distorted_text_layer)
        final_draw = ImageDraw.Draw(final_img)
        
        for _ in range(random.randint(5, 7)):
            final_draw.line([(random.randint(0, IMAGE_WIDTH), random.randint(0, IMAGE_HEIGHT)) for _ in range(4)], 
                      fill=(random.randint(70, 170), random.randint(70, 170), random.randint(70, 170)), width=2)
        
        buffer = BytesIO()
        final_img.save(buffer, format="PNG")
        
        self.send_response(200)
        self.send_header('Content-type', 'image/png')
        self.end_headers()
        self.wfile.write(buffer.getvalue())
        return
