from http.server import BaseHTTPRequestHandler
from io import BytesIO
from urllib.parse import urlparse, parse_qs
from PIL import Image, ImageDraw, ImageFont
import random
import math
import os

# --- Configuration ---
DEFAULT_TEXT = "CRAPTCHA"
MAX_TEXT_LENGTH = 50
IMAGE_WIDTH = 550
IMAGE_HEIGHT = 100
FONT_SIZE_RANGE = (26, 52)
ROTATION_RANGE = (-20, 20)
SPACING_RANGE = (-6, 2)
AMPLITUDE_RANGE = (4, 8)
FREQUENCY_RANGE = (0.02, 0.04)
NOISE_LINE_COUNT = (20, 30)
SALT_PEPPER_AMOUNT = 0.05

class handler(BaseHTTPRequestHandler):

    def apply_wave_transform(self, image):
        width, height = image.size
        amplitude = random.uniform(AMPLITUDE_RANGE[0], AMPLITUDE_RANGE[1])
        frequency = random.uniform(FREQUENCY_RANGE[0], FREQUENCY_RANGE[1])
        
        # Create a new image to avoid modifying the original during transformation
        transformed_image = Image.new('RGBA', image.size)
        
        for y in range(height):
            for x in range(width):
                offset_x = int(x + math.sin(float(y) * frequency) * amplitude)
                if 0 <= offset_x < width:
                    pixel = image.getpixel((offset_x, y))
                    transformed_image.putpixel((x, y), pixel)
        return transformed_image

    def do_GET(self):
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)
        text_to_render = query_params.get('text', [DEFAULT_TEXT])[0]
        if len(text_to_render) > MAX_TEXT_LENGTH:
            text_to_render = text_to_render[:MAX_TEXT_LENGTH]

        bg_color = (random.randint(220, 255), random.randint(220, 255), random.randint(220, 255))
        final_img = Image.new('RGB', (IMAGE_WIDTH, IMAGE_HEIGHT), color=bg_color)
        draw = ImageDraw.Draw(final_img, 'RGBA') # Draw with transparency support
        
        color_palette = [(26, 45, 82), (92, 43, 43), (44, 74, 55), (99, 57, 110)]

        # Fast Noisy Background
        for _ in range(10):
            x0, y0 = random.randint(-50, IMAGE_WIDTH-50), random.randint(-50, IMAGE_HEIGHT-50)
            x1, y1 = x0 + random.randint(100, 200), y0 + random.randint(100, 200)
            color = random.choice(color_palette) + (random.randint(20, 50),)
            draw.rectangle([x0, y0, x1, y1], fill=color)

        script_dir = os.path.dirname(__file__)
        font_names = ["fonts/DejaVuSans-Bold.ttf", "fonts/DejaVuSerif-Bold.ttf"]
        available_font_paths = [os.path.join(script_dir, name) for name in font_names if os.path.exists(os.path.join(script_dir, name))]
        if not available_font_paths:
            raise IOError("No bundled fonts found.")

        # Optimized rendering loop
        temp_draw = ImageDraw.Draw(Image.new('RGB',(1,1)))
        
        char_configs = []
        actual_width = 0
        for char in text_to_render:
            font_path = random.choice(available_font_paths)
            font_size = random.randint(FONT_SIZE_RANGE[0], FONT_SIZE_RANGE[1])
            font = ImageFont.truetype(font_path, font_size)
            spacing = random.uniform(SPACING_RANGE[0], SPACING_RANGE[1])
            width = temp_draw.textlength(char, font=font)
            actual_width += width + spacing
            char_configs.append({'char': char, 'font': font, 'width': width, 'spacing': spacing})
        
        x_start = (IMAGE_WIDTH - actual_width) / 2
        y_center = IMAGE_HEIGHT / 2
        current_x = x_start

        for config in char_configs:
            font = config['font']
            font_size = font.size
            char_img = Image.new('RGBA', (font_size * 2, font_size * 2))
            char_draw = ImageDraw.Draw(char_img)
            
            char_draw.text((font_size/2, font_size/2), config['char'], font=font, fill=random.choice(color_palette))
            rotation = random.uniform(ROTATION_RANGE[0], ROTATION_RANGE[1])
            rotated_char = char_img.rotate(rotation, expand=True, resample=Image.BICUBIC)

            y_offset = random.uniform(-AMPLITUDE_RANGE[1], AMPLITUDE_RANGE[1])
            final_img.paste(rotated_char, (int(current_x), int(y_center + y_offset - rotated_char.height / 2)), rotated_char)
            current_x += config['width'] + config['spacing']
        
        final_img = self.apply_wave_transform(final_img.convert('RGBA'))

        final_draw = ImageDraw.Draw(final_img)
        for _ in range(random.randint(NOISE_LINE_COUNT[0], NOISE_LINE_COUNT[1])):
            final_draw.line([(random.randint(0, IMAGE_WIDTH), random.randint(0, IMAGE_HEIGHT)) for _ in range(2)], fill=random.choice(color_palette), width=2)
        
        pixels = final_img.load()
        for _ in range(int(IMAGE_WIDTH * IMAGE_HEIGHT * SALT_PEPPER_AMOUNT)):
            x, y = random.randint(0, IMAGE_WIDTH-1), random.randint(0, IMAGE_HEIGHT-1)
            pixels[x, y] = random.choice([(0,0,0,255), (255,255,255,255)])

        buffer = BytesIO()
        final_img.convert('RGB').save(buffer, format="PNG")
        
        self.send_response(200)
        self.send_header('Content-type', 'image/png')
        self.end_headers()
        self.wfile.write(buffer.getvalue())
        return
