from http.server import BaseHTTPRequestHandler
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import random
import math

EMAIL_ADDRESS = "TFA1974@AOL.COM"
IMAGE_WIDTH = 300
IMAGE_HEIGHT = 75

INITIAL_FONT_SIZE = 30
HORIZONTAL_PADDING = 15  
VERTICAL_PADDING = 5     
DESIRED_AMPLITUDE_MIN = 5.0  
DESIRED_AMPLITUDE_MAX = 8.0
DESIRED_SPACING_MIN = 1.0  
DESIRED_SPACING_MAX = 5.0
DESIRED_ROTATION = 15  

class handler(BaseHTTPRequestHandler):
    def do_GET(self):

        bg_color = (random.randint(220, 255), random.randint(220, 255), random.randint(220, 255))
        img = Image.new('RGB', (IMAGE_WIDTH, IMAGE_HEIGHT), color=bg_color)
        draw = ImageDraw.Draw(img)

        font_names = [
            "DejaVuSans.ttf", "DejaVuSerif.ttf", "DejaVuSans-Mono.ttf",
            "LiberationSans-Regular.ttf", "LiberationSerif-Regular.ttf", "LiberationMono-Regular.ttf"
        ]
        available_font_paths = [name for name in font_names if self.font_exists(name)]
        if not available_font_paths:

            raise IOError("No suitable fonts found on the system.")

        current_font_size = INITIAL_FONT_SIZE
        while current_font_size > 10:
            font_list = [ImageFont.truetype(path, current_font_size) for path in available_font_paths]
            max_width = self.calculate_max_width(draw, EMAIL_ADDRESS, font_list)
            if max_width < (IMAGE_WIDTH - HORIZONTAL_PADDING * 2):
                break  
            current_font_size -= 1

        final_font_size = current_font_size
        final_font_list = [ImageFont.truetype(path, final_font_size) for path in available_font_paths]

        max_allowable_amplitude = (IMAGE_HEIGHT - final_font_size - VERTICAL_PADDING * 2) / 2
        safe_amplitude_max = max(0, min(DESIRED_AMPLITUDE_MAX, max_allowable_amplitude))
        safe_amplitude_min = min(DESIRED_AMPLITUDE_MIN, safe_amplitude_max)
        amplitude = random.uniform(safe_amplitude_min, safe_amplitude_max)

        char_configs = []
        actual_width = 0
        for char in EMAIL_ADDRESS:
            font = random.choice(final_font_list)
            spacing = random.uniform(DESIRED_SPACING_MIN, DESIRED_SPACING_MAX)
            width = draw.textlength(char, font=font)
            actual_width += width + spacing
            char_configs.append({'char': char, 'font': font, 'width': width, 'spacing': spacing})

        x_start = (IMAGE_WIDTH - actual_width) / 2
        y_center = IMAGE_HEIGHT / 2
        current_x = x_start

        for config in char_configs:
            y_offset = amplitude * math.sin(0.1 * current_x)
            char_y_pos = y_center + y_offset

            char_img = Image.new('RGBA', (final_font_size * 2, final_font_size * 2))
            char_draw = ImageDraw.Draw(char_img)
            text_color = (random.randint(10, 80), random.randint(10, 80), random.randint(10, 80))
            char_draw.text((10, 10), config['char'], font=config['font'], fill=text_color)

            rotation = random.uniform(-DESIRED_ROTATION, DESIRED_ROTATION)
            rotated_char = char_img.rotate(rotation, expand=True, resample=Image.BICUBIC)

            img.paste(rotated_char, (int(current_x), int(char_y_pos - rotated_char.height / 2)), rotated_char)
            current_x += config['width'] + config['spacing']

        for _ in range(random.randint(5, 7)):
            draw.line([(random.randint(0, IMAGE_WIDTH), random.randint(0, IMAGE_HEIGHT)) for _ in range(4)], 
                      fill=(random.randint(70, 170), random.randint(70, 170), random.randint(70, 170)), width=2)

        buffer = BytesIO()
        img.save(buffer, format="PNG")
        self.send_response(200)
        self.send_header('Content-type', 'image/png')
        self.end_headers()
        self.wfile.write(buffer.getvalue())

    def font_exists(self, font_name):
        try:
            ImageFont.truetype(font_name, 10)
            return True
        except IOError:
            return False

    def calculate_max_width(self, draw, text, font_list):

        max_font_width = 0
        for char in text:

            char_width = max(draw.textlength(char, font=font) for font in font_list)
            max_font_width += char_width + DESIRED_SPACING_MAX
        return max_font_width
