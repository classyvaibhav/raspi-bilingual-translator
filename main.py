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

# Setup GPIO
GPIO.setmode(GPIO.BCM)
SRC_BTN = 17     # GPIO pin for source language button
DST_BTN = 27     # GPIO pin for target language button
GO_BTN  = 22     # GPIO pin for start/translate button
GPIO.setup(SRC_BTN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(DST_BTN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(GO_BTN,  GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# Language lists (name and code)
LANGS = [
    ("English", "en"), ("Hindi", "hi"), ("Spanish", "es"),
    ("French", "fr"), ("German", "de"), ("Chinese (Simpl.)", "zh-cn")
]
src_index = 0
dst_index = 1  # default target

# Initialize OLED display (I2C address 0x3C typical)
serial = i2c(port=1, address=0x3C)
display = ssd1306(serial)

def update_display(line1="", line2="", line3=""):
    """Helper to update 3-line text on the OLED display."""
    with canvas(display) as draw:
        draw.text((0, 0), f"Src: {LANGS[src_index][0]}", fill="white")
        draw.text((0, 16), f"Dst: {LANGS[dst_index][0]}", fill="white")
        draw.text((0, 32), line1, fill="white")
        draw.text((0, 48), line2, fill="white")
        # (You can add more text lines if needed)
        
# Initialize STT and Translator
recognizer = sr.Recognizer()
translator = Translator()

# Main loop
try:
    update_display("Press Go", "to speak")
    while True:
        # Check source language button
        if GPIO.input(SRC_BTN) == GPIO.HIGH:
            time.sleep(0.2)
            src_index = (src_index + 1) % len(LANGS)
            # Ensure src and dst are not same
            if src_index == dst_index:
                dst_index = (dst_index + 1) % len(LANGS)
            update_display("Source: " + LANGS[src_index][0])
            time.sleep(0.5)  # debounce
            
        # Check target language button
        if GPIO.input(DST_BTN) == GPIO.HIGH:
            time.sleep(0.2)
            dst_index = (dst_index + 1) % len(LANGS)
            if dst_index == src_index:
                dst_index = (dst_index + 1) % len(LANGS)
            update_display("Target: " + LANGS[dst_index][0])
            time.sleep(0.5)  # debounce

        # Check translate button
        if GPIO.input(GO_BTN) == GPIO.HIGH:
            update_display("Listening...", "")
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = recognizer.listen(source)
            try:
                # Recognize speech using Google STT
                src_lang_code = LANGS[src_index][1]
                text = recognizer.recognize_google(audio, language=src_lang_code)
            except sr.UnknownValueError:
                update_display("Could not understand", "Speech")
                time.sleep(2)
                update_display("Press Go to speak", "")
                continue
            except sr.RequestError as e:
                update_display("STT error", str(e))
                time.sleep(2)
                continue

            update_display("You said:", text[:15] + "...")
            time.sleep(1)

            # Translate text
            translated = translator.translate(text, 
                                              src=src_lang_code, 
                                              dest=LANGS[dst_index][1])
            trans_text = translated.text
            update_display("Translated:", trans_text[:15] + "...")
            time.sleep(1)

            # Text-to-Speech (gTTS)
            tts = gTTS(text=trans_text, lang=LANGS[dst_index][1])
            tts_file = "/home/pi/tts_out.mp3"
            tts.save(tts_file)
            # Play the mp3 file
            subprocess.run(["mpg321", tts_file])

            update_display("Done. Press Go", "for next")
            time.sleep(0.5)

        time.sleep(0.1)

except KeyboardInterrupt:
    GPIO.cleanup()
