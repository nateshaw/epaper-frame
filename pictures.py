#!/usr/bin/env python3
import sys
import os
import time
import random
import threading
import base64
import io
from flask import Flask, redirect, request
from PIL import Image, ImageOps, ImageDraw, ImageFont

# Add Waveshare driver path
sys.path.append('/home/nate/e-Paper/RaspberryPi_JetsonNano/python/lib')
from waveshare_epd import epd7in3e

# Configuration
IMAGE_DIR = '/home/nate/dropbox/media/Photos'
FALLBACK_IMAGE = '/home/nate/Pictures/Shaw_Family_Photos_Cover.png'
SLEEP_SECONDS = 300
SHUFFLE_IMAGES = True
EPD_WIDTH = 800
EPD_HEIGHT = 480

app = Flask(__name__)
image_control = {
    "advance": False,
    "reverse": False,
    "paused": False,
    "current_path": None,
    "casted_path": None,
    "cast_displayed": False
}

@app.route("/")
def home():
    current_path = image_control.get("current_path")
    thumbnail_data = ""
    if current_path and os.path.exists(current_path):
        try:
            with Image.open(current_path) as img:
                img = ImageOps.exif_transpose(img)
                img.thumbnail((400, 300))
                buf = io.BytesIO()
                img.save(buf, format="JPEG")
                thumbnail_data = base64.b64encode(buf.getvalue()).decode('utf-8')
        except Exception as e:
            print(f"Thumbnail error: {e}")

    return f"""
    <html>
    <head>
        <title>Digital Frame Remote</title>
        <style>
            body {{ font-family: sans-serif; text-align: center; margin-top: 40px; }}
            .button-row {{ display: flex; justify-content: center; gap: 20px; flex-wrap: wrap; margin-top: 20px; }}
            button {{
                font-size: 2em;
                padding: 20px 30px;
                border: none;
                background-color: #444;
                color: white;
                border-radius: 10px;
                cursor: pointer;
            }}
            button:hover {{ background-color: #666; }}
            img.thumbnail {{
                max-width: 90%;
                height: auto;
                border-radius: 10px;
                margin-top: 20px;
                box-shadow: 0 0 10px #aaa;
            }}
        </style>
    </head>
    <body>
        <h1>📷 Digital Frame Remote</h1>
        {f'<img class="thumbnail" src="data:image/jpeg;base64,{thumbnail_data}">' if thumbnail_data else '<p>No image loaded.</p>'}
        <div class="button-row">
            <form action="/previous"><button>⏮️ Previous</button></form>
            <form action="/toggle-pause"><button>⏸️ Pause/Resume</button></form>
            <form action="/next"><button>⏭️ Next</button></form>
        </div>
        <form action="/cast" method="POST" enctype="multipart/form-data" style="margin-top: 30px;">
            <label for="image" style="font-size: 1.2em;">📤 Cast an Image:</label><br>
            <input type="file" name="image" accept="image/*" required style="font-size: 1.2em; margin-top: 10px;"><br>
            <button type="submit" style="margin-top: 15px; font-size: 1.5em;">📲 Upload & Cast</button>
        </form>
        <form action="/resume" method="GET" style="margin-top: 15px;">
            <button type="submit" style="font-size: 1.2em;">🔁 Resume Slideshow</button>
        </form>
    </body>
    </html>
    """

@app.route("/next")
def next_image():
    image_control["advance"] = True
    return redirect("/")

@app.route("/previous")
def previous_image():
    image_control["reverse"] = True
    return redirect("/")

@app.route("/toggle-pause")
def toggle_pause():
    image_control["paused"] = not image_control["paused"]
    return redirect("/")

@app.route("/cast", methods=["POST"])
def cast_image():
    file = request.files.get("image")
    if file:
        path = "/tmp/casted_image.jpg"
        file.save(path)
        image_control["paused"] = True
        image_control["casted_path"] = path
        image_control["cast_displayed"] = False
        return redirect("/")
    return "No image uploaded", 400

@app.route("/resume")
def resume_slideshow():
    image_control["paused"] = False
    image_control["casted_path"] = None
    image_control["cast_displayed"] = False
    return redirect("/")

def get_image_list(directory):
    image_paths = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
                image_paths.append(os.path.join(root, file))
    return random.sample(image_paths, len(image_paths)) if SHUFFLE_IMAGES else sorted(image_paths)

def prepare_image(path):
    try:
        img = Image.open(path)
        img = ImageOps.exif_transpose(img).convert('RGB')
    except Exception as e:
        print(f"Error opening image: {e}")
        return None

    was_rotated = False
    if img.height > img.width:
        img = img.rotate(270, expand=True)
        was_rotated = True

    img.thumbnail((EPD_WIDTH, EPD_HEIGHT), Image.LANCZOS)
    canvas = Image.new('RGB', (EPD_WIDTH, EPD_HEIGHT), (255, 255, 255))
    x_offset = (EPD_WIDTH - img.width) // 2
    y_offset = (EPD_HEIGHT - img.height) // 2
    canvas.paste(img, (x_offset, y_offset))

    draw = ImageDraw.Draw(canvas)
    filename = os.path.basename(path)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
    except:
        font = ImageFont.load_default()

    padding = 6
    bbox = draw.textbbox((0, 0), filename, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = EPD_WIDTH - text_width - padding
    y = EPD_HEIGHT - text_height - padding
    draw.rectangle((x - padding, y - padding, x + text_width + padding, y + text_height + padding), fill=(255, 255, 255))
    draw.text((x, y), filename, font=font, fill=(0, 0, 0))

    if was_rotated:
        icon = "↻"
        icon_bbox = draw.textbbox((padding, padding), icon, font=font)
        draw.rectangle((padding - 6, padding - 6, icon_bbox[2] + 6, icon_bbox[3] + 6), fill=(255, 255, 255))
        draw.text((padding, padding), icon, font=font, fill=(0, 0, 0))

    return canvas

def initialize_display():
    epd = epd7in3e.EPD()
    epd.init()
    epd.Clear()
    return epd

def slideshow_loop(epd):
    index = 0
    while True:
        if image_control["casted_path"]:
            if not image_control["cast_displayed"]:
                cast_image = prepare_image(image_control["casted_path"])
                if cast_image:
                    epd.display(epd.getbuffer(cast_image))
                    image_control["cast_displayed"] = True
            time.sleep(0.5)
            continue

        images = get_image_list(IMAGE_DIR)
        if not images:
            image = prepare_image(FALLBACK_IMAGE)
            if image:
                epd.display(epd.getbuffer(image))
            time.sleep(30)
            continue

        if image_control["reverse"]:
            index = (index - 1) % len(images)
            image_control["reverse"] = False
        elif image_control["advance"] or not image_control["paused"]:
            index = (index + 1) % len(images)
            image_control["advance"] = False

        path = images[index]
        image_control["current_path"] = path
        image = prepare_image(path)
        if image:
            epd.display(epd.getbuffer(image))

        waited = 0
        while waited < SLEEP_SECONDS:
            if image_control["advance"] or image_control["reverse"] or image_control["casted_path"]:
                break
            if image_control["paused"]:
                time.sleep(0.2)
                continue
            time.sleep(0.5)
            waited += 0.5

if __name__ == '__main__':
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)).start()
    try:
        epd = initialize_display()
        slideshow_loop(epd)
    except KeyboardInterrupt:
        epd7in3e.epdconfig.module_exit()
