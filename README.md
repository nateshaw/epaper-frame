# Raspberry Pi ePaper Digital Photo Frame

This guide explains how to create a Wi-Fi-controlled ePaper digital photo frame using a Raspberry Pi and a Waveshare e-Paper display.

---

## 🧰 Hardware Required

- Raspberry Pi 4B or any compatible model
- Waveshare 7.3" e-Paper display (connected via SPI)
- microSD card with Raspberry Pi OS Bookworm
- Power supply, case, and optional stand

---

## 🛠️ Step-by-Step Setup

### 1. Setup Raspberry Pi OS

- Flash Raspberry Pi OS Bookworm using Raspberry Pi Imager
- Boot, connect to Wi-Fi, and enable SSH (optional: `sudo raspi-config`)
- Update packages:

```bash
sudo apt update && sudo apt upgrade -y
```

---

### 2. Connect the Waveshare Display

- Connect the display via SPI (check your Waveshare model’s pinout)
- Enable SPI:

```bash
sudo raspi-config
# Interface Options -> SPI -> Enable
```

- Reboot:

```bash
sudo reboot
```

---

### 3. Install Dependencies

```bash
sudo apt install python3-pip python3-pil python3-flask python3-rpi.gpio git -y
```

- Optional (for virtual environment):

```bash
sudo apt install python3-venv
python3 -m venv ~/venv_picframe
source ~/venv_picframe/bin/activate
```

---

### 4. Install the Waveshare Driver

```bash
git clone https://github.com/waveshare/e-Paper.git ~/e-Paper
```

> Modify `epdconfig.py` to avoid gpiozero issues. Use the fixed version provided in this project.

---

### 5. Download the Project Script

Place `pictures.py` in your Pi’s home or code directory:

```bash
wget http://your-server-or-copy/pictures.py -O ~/pictures.py
chmod +x ~/pictures.py
```

---

### 6. Test the Frame

Run it manually:

```bash
source ~/venv_picframe/bin/activate
python3 ~/pictures.py
```

Visit the Flask interface on your phone:

```
http://<your-pi-ip>:5000
```

You should see:
- Image thumbnail
- ⏮️ ⏸️ ⏭️ buttons
- Live cycling of images from `~/dropbox/media/Photos`

---

### 7. Auto Start on Boot

Create a systemd service file:

```ini
# /etc/systemd/system/picframe.service
[Unit]
Description=Digital Picture Frame with Web Interface
After=network.target

[Service]
User=pi
ExecStart=/home/pi/venv_picframe/bin/python3 /home/pi/pictures.py
WorkingDirectory=/home/pi
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable picframe
sudo systemctl start picframe
```

---

## ✅ Features

- Automatic slideshow of images (with shuffle)
- Portrait auto-rotate + burn-in filename
- Flask web interface for control:
  - ⏮️ Previous / ⏭️ Next / ⏸️ Pause
  - Live thumbnail view of current image

---

## 📂 Recommended Directory Layout

```
~/dropbox/media/Photos/         # Source for your images
~/Pictures/Shaw_Family_Photos_Cover.png  # Default fallback image
~/e-Paper/                      # Waveshare driver repo
~/pictures.py                   # Main script
~/venv_picframe/                # Python virtual environment
```

---

## 🧩 Optional Enhancements

- Dropbox sync via `rclone` or mount script
- Face detection to skip blank slides
- Battery monitoring for mobile use
- Weather or calendar overlay
