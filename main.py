import time
import os
import subprocess
import RPi.GPIO as GPIO
import speech_recognition as sr
from googletrans import Translator
from gtts import gTTS
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306

# GPIO Setup
GPIO.setmode(GPIO.BCM)
SRC_BTN = 17     # Source language button
DST_BTN = 27     # Target language button
GO_BTN = 22      # Action button
GPIO.setup(SRC_BTN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(DST_BTN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(GO_BTN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Language Configuration
LANGS = [
    ("English", "en"), ("Hindi", "hi"), ("Spanish", "es"),
    ("French", "fr"), ("German", "de"), ("Chinese (Simpl.)", "zh-CN")  # Fixed code
]
src_index, dst_index = 0, 1

# OLED Display Setup
serial = i2c(port=1, address=0x3C)
display = ssd1306(serial, rotate=0)

def update_display(line1="", line2=""):
    """Update OLED display with clean output"""
    with canvas(display) as draw:
        draw.rectangle(display.bounding_box, outline="black", fill="black")
        draw.text((0, 0), f"Src: {LANGS[src_index][0]}", fill="white")
        draw.text((0, 16), f"Dst: {LANGS[dst_index][0]}", fill="white")
        draw.text((0, 32), line1, fill="white")
        draw.text((0, 48), line2, fill="white")

# Initialize Components
recognizer = sr.Recognizer()
translator = Translator()
update_display("Ready", "Press GO to start")

# Button Callbacks
def update_src(channel):
    global src_index, dst_index
    src_index = (src_index + 1) % len(LANGS)
    if src_index == dst_index:
        dst_index = (dst_index + 1) % len(LANGS)
    update_display(f"Source: {LANGS[src_index][0]}")

def update_dst(channel):
    global dst_index, src_index
    dst_index = (dst_index + 1) % len(LANGS)
    if dst_index == src_index:
        dst_index = (dst_index + 1) % len(LANGS)
    update_display(f"Target: {LANGS[dst_index][0]}")

GPIO.add_event_detect(SRC_BTN, GPIO.FALLING, callback=update_src, bouncetime=200)
GPIO.add_event_detect(DST_BTN, GPIO.FALLING, callback=update_dst, bouncetime=200)

try:
    while True:
        if GPIO.input(GO_BTN) == GPIO.LOW:
            update_display("Listening...", "")
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source)
                audio = recognizer.listen(source, timeout=5)
            
            try:
                text = recognizer.recognize_google(audio, language=LANGS[src_index][1])
            except Exception as e:
                update_display("STT Error", str(e)[:15])
                time.sleep(2)
                continue

            update_display("Processing...", text[:15])
            
            try:
                translated = translator.translate(
                    text, 
                    src=LANGS[src_index][1], 
                    dest=LANGS[dst_index][1]
                )
                trans_text = translated.text
            except Exception as e:
                update_display("Translation Err", str(e)[:15])
                time.sleep(2)
                continue

            try:
                tts = gTTS(trans_text, lang=LANGS[dst_index][1])
                tts_file = "/tmp/tts.mp3"
                tts.save(tts_file)
                subprocess.run(
                    ["mpg321", "-q", tts_file],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                os.remove(tts_file)
            except Exception as e:
                update_display("TTS Error", str(e)[:15])
                time.sleep(2)
                continue

            update_display("Translation:", trans_text[:15])
            time.sleep(2)
            update_display("Ready", "Press GO")

        time.sleep(0.1)

except KeyboardInterrupt:
    GPIO.cleanup()
