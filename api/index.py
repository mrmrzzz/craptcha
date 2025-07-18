from http.server import BaseHTTPRequestHandler
from io import BytesIO
from urllib.parse import urlparse, parse_qs
from PIL import Image, ImageDraw, ImageFont
from perlin_noise import PerlinNoise
import random
import math
import os

DEFAULT_TEXT = "CAPTCHA"
MAX_TEXT_LENGTH = 50

MIN_IMAGE_HEIGHT = 100
FONT_SIZE_RANGE = (38, 50)
HORIZONTAL_PADDING = 25
VERTICAL_PADDING = 20

DESIRED_AMPLITUDE_MAX = 12.0
DESIRED_SPACING_MIN = -10.0
DESIRED_SPACING_MAX = 4.0
DESIRED_ROTATION_MIN = -20
DESIRED_ROTATION_MAX = 20
BULGE_FACTOR = 0.3
INVERTED_BLOCK_CHANCE = 0.25
NOISE_LINE_COUNT = (10, 15)
SALT_PEPPER_AMOUNT = 0.05

class handler(BaseHTTPRequestHandler):

    def apply_bulge_distortion(self, image, factor):
        width, height = image.size
        center_x, center_y = float(width / 2), float(height / 2)
        max_radius = float(min(center_x, center_y))
        
        mesh_data = []
        grid_size = 10

        for j in range(grid_size):
            for i in range(grid_size):
                x0, y0 = float(i * width) / grid_size, float(j * height) / grid_size
                x1, y1 = float((i + 1) * width) / grid_size, float(j * height) / grid_size
                x2, y2 = float((i + 1) * width) / grid_size, float((j + 1) * height) / grid_size
                x3, y3 = float(i * width) / grid_size, float((j + 1) * height) / grid_size
                target_box = (x0, y0, x2, y2)

                def get_source_coords(x, y):
                    dx, dy = x - center_x, y - center_y
                    distance = math.sqrt(dx**2 + dy**2)
                    if max_radius == 0: return (x, y)
                    r = distance / max_radius
                    new_r = r + (r**2 - r) * factor
                    if distance == 0: scale = 1.0
                    else: scale = (new_r * max_radius) / distance
                    return (center_x + dx * scale, center_y + dy * scale)

                source_quad = []
                for x,y in [(x0,y0), (x1,y1), (x2,y2), (x3,y3)]:
                     source_quad.extend(get_source_coords(x,y))
                mesh_data.append((target_box, tuple(source_quad)))

        return image.transform(image.size, Image.MESH, mesh_data, Image.BICUBIC)

    def do_GET(self):
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)
        text_to_render = query_params.get('text', [DEFAULT_TEXT])[0]
        if len(text_to_render) > MAX_TEXT_LENGTH:
            text_to_render = text_to_render[:MAX_TEXT_LENGTH]

        script_dir = os.path.dirname(__file__)
        font_names = ["fonts/DejaVuSans-Bold.ttf", "fonts/DejaVuSerif-Bold.ttf"]
        available_font_paths = [os.path.join(script_dir, name) for name in font_names if os.path.exists(os.path.join(script_dir, name))]
        if not available_font_paths:
            raise IOError("No bundled fonts found.")

        char_configs = []
        actual_width = 0
        temp_draw = ImageDraw.Draw(Image.new('RGB',(1,1)))
        
        for char in text_to_render:
            font_path = random.choice(available_font_paths)
            font_size = random.randint(FONT_SIZE_RANGE[0], FONT_SIZE_RANGE[1])
            font = ImageFont.truetype(font_path, font_size)
            spacing = random.uniform(DESIRED_SPACING_MIN, DESIRED_SPACING_MAX)
            width = temp_draw.textlength(char, font=font)
            actual_width += width + spacing
            char_configs.append({'char': char, 'font': font, 'width': width, 'spacing': spacing})
        
        IMAGE_WIDTH = int(actual_width + HORIZONTAL_PADDING * 2)
        IMAGE_HEIGHT = int(MIN_IMAGE_HEIGHT + VERTICAL_PADDING * 2)

        noise = PerlinNoise(octaves=random.uniform(4, 8), seed=random.randint(1, 100))
        pic = [[noise([i/IMAGE_WIDTH, j/IMAGE_HEIGHT]) for j in range(IMAGE_HEIGHT)] for i in range(IMAGE_WIDTH)]
        final_img = Image.new('RGB', (IMAGE_WIDTH, IMAGE_HEIGHT))
        for i in range(IMAGE_WIDTH):
            for j in range(IMAGE_HEIGHT):
                color = int((pic[i][j] + 0.5) * 200) + 55
                final_img.putpixel((i, j), (color, color, int(color*0.95)))

        geo_layer = Image.new('RGBA', final_img.size, (255, 255, 255, 0))
        geo_draw = ImageDraw.Draw(geo_layer)
        for _ in range(5):
            geo_draw.line([(random.randint(0, IMAGE_WIDTH), random.randint(0, IMAGE_HEIGHT)) for _ in range(2)], fill=(random.randint(100,200), random.randint(100,200), random.randint(100,200), 64), width=1)
        final_img.paste(geo_layer, (0,0), geo_layer)

        text_layer = Image.new('RGBA', (IMAGE_WIDTH, IMAGE_HEIGHT), (0,0,0,0))
        dark_palette = [(26, 45, 82), (92, 43, 43), (44, 74, 55), (99, 57, 110)]
        light_palette = [(210, 220, 255), (255, 210, 210), (210, 255, 220)]

        x_start = HORIZONTAL_PADDING
        y_center = IMAGE_HEIGHT / 2
        current_x = x_start

        for config in char_configs:
            y_offset = random.uniform(-DESIRED_AMPLITUDE_MAX, DESIRED_AMPLITUDE_MAX)
            char_y_pos = y_center + y_offset
            
            font = config['font']
            font_size = font.size
            char_img = Image.new('RGBA', (font_size * 2, font_size * 2))
            char_draw = ImageDraw.Draw(char_img)
            
            if random.random() < INVERTED_BLOCK_CHANCE:
                block_color = random.choice(dark_palette)
                text_color = random.choice(light_palette)
                rect_size = font_size * 1.2
                rect_img = Image.new('RGBA', (int(rect_size), int(rect_size)), block_color)
                rect_rot = rect_img.rotate(random.uniform(-15,15), expand=True, resample=Image.BICUBIC)
                text_layer.paste(rect_rot, (int(current_x - rect_rot.width/4), int(char_y_pos - rect_rot.height/2)), rect_rot)
            else:
                text_color = random.choice(dark_palette)

            char_draw.text((font_size/2, font_size/2), config['char'], font=font, fill=text_color)
            rotation = random.uniform(DESIRED_ROTATION_MIN, DESIRED_ROTATION_MAX)
            rotated_char = char_img.rotate(rotation, expand=True, resample=Image.BICUBIC)
            
            text_layer.paste(rotated_char, (int(current_x), int(char_y_pos - rotated_char.height / 2)), rotated_char)
            current_x += config['width'] + config['spacing']

        distorted_text_layer = self.apply_bulge_distortion(text_layer, BULGE_FACTOR)
        final_img.paste(distorted_text_layer, (0,0), distorted_text_layer)
        
        final_draw = ImageDraw.Draw(final_img)
        for _ in range(random.randint(NOISE_LINE_COUNT[0], NOISE_LINE_COUNT[1])):
            final_draw.line([(random.randint(0, IMAGE_WIDTH), random.randint(0, IMAGE_HEIGHT)) for _ in range(random.randint(2,4))], fill=random.choice(dark_palette), width=random.randint(2,3))
        
        pixels = final_img.load()
        for _ in range(int(IMAGE_WIDTH * IMAGE_HEIGHT * SALT_PEPPER_AMOUNT)):
            x, y = random.randint(0, IMAGE_WIDTH-1), random.randint(0, IMAGE_HEIGHT-1)
            pixels[x, y] = random.choice([(0,0,0), (255,255,255)])

        buffer = BytesIO()
        final_img.save(buffer, format="PNG")
        
        self.send_response(200)
        self.send_header('Content-type', 'image/png')
        self.end_headers()
        self.wfile.write(buffer.getvalue())
        return
