from http.server import BaseHTTPRequestHandler
from io import BytesIO
from urllib.parse import urlparse, parse_qs
from PIL import Image, ImageDraw, ImageFont
import random
import math
import os

# --- Configuration ---
DEFAULT_TEXT = "CAPTCHA"
MAX_TEXT_LENGTH = 50
IMAGE_WIDTH = 400
IMAGE_HEIGHT = 100
FONT_SIZE_RANGE = (40, 52)
HORIZONTAL_PADDING = 20
VERTICAL_PADDING = 10
ROTATION_RANGE = (-20, 20)
SPACING_RANGE = (-8, 2)
AMPLITUDE_RANGE = (4, 8)
FREQUENCY_RANGE = (0.02, 0.04)
NOISE_LINE_COUNT = (10, 15)
SALT_PEPPER_AMOUNT = 0.03

class handler(BaseHTTPRequestHandler):

    def apply_wave_transform(self, image):
        width, height = image.size
        # Simple, fast sine wave shear
        amplitude = random.uniform(AMPLITUDE_RANGE[0], AMPLITUDE_RANGE[1])
        frequency = random.uniform(FREQUENCY_RANGE[0], FREQUENCY_RANGE[1])
        
        def transform_func(x, y):
            return x + math.sin(y * frequency) * amplitude, y

        # Use AFFINE transform which is very fast
        return image.transform(image.size, Image.AFFINE, (1, 0, 0, 0, 1, 0), Image.BICUBIC, fillcolor=(0,0,0,0), method=transform_func)

    def do_GET(self):
        # --- 1. Parse URL ---
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)
        text_to_render = query_params.get('text', [DEFAULT_TEXT])[0]
        if len(text_to_render) > MAX_TEXT_LENGTH:
            text_to_render = text_to_render[:MAX_TEXT_LENGTH]

        # --- 2. Setup Images and Palettes ---
        bg_color = (random.randint(220, 255), random.randint(220, 255), random.randint(220, 255))
        final_img = Image.new('RGB', (IMAGE_WIDTH, IMAGE_HEIGHT), color=bg_color)
        draw = ImageDraw.Draw(final_img)
        text_layer = Image.new('RGBA', (IMAGE_WIDTH, IMAGE_HEIGHT), (0,0,0,0))
        text_draw = ImageDraw.Draw(text_layer)
        
        color_palette = [(26, 45, 82), (92, 43, 43), (44, 74, 55), (99, 57, 110)]

        # --- 3. Fast Noisy Background ---
        for _ in range(10):
            x0, y0 = random.randint(-50, IMAGE_WIDTH-50), random.randint(-50, IMAGE_HEIGHT-50)
            x1, y1 = x0 + random.randint(100, 200), y0 + random.randint(100, 200)
            color = random.choice(color_palette) + (random.randint(20, 50),) # Add alpha
            draw.rectangle([x0, y0, x1, y1], fill=color)

        # --- 4. Load Fonts ---
        script_dir = os.path.dirname(__file__)
        font_names = ["fonts/DejaVuSans-Bold.ttf", "fonts/DejaVuSerif-Bold.ttf"]
        available_font_paths = [os.path.join(script_dir, name) for name in font_names if os.path.exists(os.path.join(script_dir, name))]
        if not available_font_paths:
            raise IOError("No bundled fonts found.")

        # --- 5. Pre-calculate Character Properties (Optimized) ---
        char_configs = []
        actual_width = 0
        temp_draw = ImageDraw.Draw(Image.new('RGB',(1,1)))
        
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

        # --- 6. Render Characters onto a single transparent layer ---
        for config in char_configs:
            y_offset = random.uniform(-AMPLITUDE_RANGE[1], AMPLITUDE_RANGE[1])
            font = config['font']
            
            text_draw.text(
                (current_x, y_center + y_offset),
                config['char'],
                font=font,
                fill=random.choice(color_palette),
                anchor="mm" # Middle-Middle anchor for better centering
            )
            current_x += config['width'] + config['spacing']

        # --- 7. Apply a single, fast distortion to the text layer ---
        distorted_text_layer = self.apply_wave_transform(text_layer)
        final_img.paste(distorted_text_layer, (0,0), distorted_text_layer)
        
        # --- 8. Draw final noise elements ---
        final_draw = ImageDraw.Draw(final_img)
        for _ in range(random.randint(NOISE_LINE_COUNT[0], NOISE_LINE_COUNT[1])):
            final_draw.line([(random.randint(0, IMAGE_WIDTH), random.randint(0, IMAGE_HEIGHT)) for _ in range(2)], fill=random.choice(color_palette), width=2)
        
        pixels = final_img.load()
        for _ in range(int(IMAGE_WIDTH * IMAGE_HEIGHT * SALT_PEPPER_AMOUNT)):
            x, y = random.randint(0, IMAGE_WIDTH-1), random.randint(0, IMAGE_HEIGHT-1)
            pixels[x, y] = random.choice([(0,0,0), (255,255,255)])

        # --- 9. Serve the final image ---
        buffer = BytesIO()
        final_img.save(buffer, format="PNG")
        
        self.send_response(200)
        self.send_header('Content-type', 'image/png')
        self.end_headers()
        self.wfile.write(buffer.getvalue())
        return
