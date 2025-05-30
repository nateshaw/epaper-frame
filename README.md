# ePaper Picture Frame

A Raspberry Pi-powered digital picture frame using a Waveshare 7.3" e-Paper display. Images are displayed from a slideshow folder, with support for:

- Uploading images from a web interface (desktop or mobile)
- Casting temporary images from a phone or computer
- Resume slideshow after casting
- Touch-friendly web controls
- Image caching and cycling with configurable delay

## Requirements

- Raspberry Pi (Zero 2 W or newer recommended)
- Waveshare 7.3" e-Paper display (model 7in3e)
- Python 3.9+
- Flask
- Pillow
- gpiozero

## Setup

1. Clone the repo:
   ```bash
   git clone https://github.com/nateshaw/epaper-frame.git
   cd epaper-frame

## Setup a virtual environment
   ```bash
   python3 -m venv venv_picframe
   source venv_picframe/bin/activate
   pip install -r requirements.txt


## Run the frame:
   ```bash
   ./start_picframe.sh
