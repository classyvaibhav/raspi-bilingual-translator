import time
import os
import subprocess
import logging
import RPi.GPIO as GPIO
import speech_recognition as sr
from googletrans import Translator
from gtts import gTTS
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306

# Configure logging
logging.basicConfig(filename='translator.log', level=logging.ERROR)

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
    ("French", "fr"), ("German", "de"), ("Chinese", "zh-CN")
]
src_index, dst_index = 0, 1

# OLED Display Setup
try:
    serial = i2c(port=1, address=0x3C)
    display = ssd1306(serial, rotate=0)
except Exception as e:
    logging.error(f"OLED Init Failed: {str(e)}")
    exit(1)

def update_display(line1="", line2=""):
    """Update OLED display with clean output"""
    try:
        with canvas(display) as draw:
            draw.rectangle(display.bounding_box, outline="black", fill="black")
            draw.text((0, 0), f"Src: {LANGS[src_index][0]}", fill="white")
            draw.text((0, 16), f"Dst: {LANGS[dst_index][0]}", fill="white")
            draw.text((0, 32), line1, fill="white")
            draw.text((0, 48), line2, fill="white")
    except Exception as e:
        logging.error(f"Display Error: {str(e)}")

# Initialize Components
recognizer = sr.Recognizer()
translator = Translator()
update_display("Ready", "Press GO to start")

# Button Callbacks
def update_src(channel):
    global src_index, dst_index
    try:
        src_index = (src_index + 1) % len(LANGS)
        if src_index == dst_index:
            dst_index = (dst_index + 1) % len(LANGS)
        update_display(f"Source: {LANGS[src_index][0]}")
    except Exception as e:
        logging.error(f"SRC Button Error: {str(e)}")

def update_dst(channel):
    global dst_index, src_index
    try:
        dst_index = (dst_index + 1) % len(LANGS)
        if dst_index == src_index:
            dst_index = (dst_index + 1) % len(LANGS)
        update_display(f"Target: {LANGS[dst_index][0]}")
    except Exception as e:
        logging.error(f"DST Button Error: {str(e)}")

# Set up button interrupts
GPIO.add_event_detect(SRC_BTN, GPIO.FALLING, callback=update_src, bouncetime=200)
GPIO.add_event_detect(DST_BTN, GPIO.FALLING, callback=update_dst, bouncetime=200)

def play_audio(file_path):
    """Play audio through GPIO PWM pins"""
    try:
        # Convert to PWM-compatible WAV format
        subprocess.run([
            "ffmpeg", "-y", "-i", file_path,
            "-ar", "22050", "-ac", "1", "/tmp/tts.wav"
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Play using ALSA with hardware device
        subprocess.run([
            "aplay", "-D", "plughw:0,0", "/tmp/tts.wav"
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        logging.error(f"Audio Playback Error: {str(e)}")
        raise

try:
    while True:
        if GPIO.input(GO_BTN) == GPIO.LOW:
            try:
                # Speech Recognition
                update_display("Listening...", "")
                with sr.Microphone() as source:
                    recognizer.adjust_for_ambient_noise(source, duration=1)
                    audio = recognizer.listen(source, timeout=8, phrase_time_limit=10)
                
                # Speech to Text
                text = recognizer.recognize_google(audio, language=LANGS[src_index][1])
                update_display("Processing...", text[:15])

                # Translation
                translated = translator.translate(
                    text, 
                    src=LANGS[src_index][1], 
                    dest=LANGS[dst_index][1]
                )
                trans_text = translated.text

                # Text to Speech
                tts = gTTS(trans_text, lang=LANGS[dst_index][1])
                tts_file = "/tmp/tts.mp3"
                tts.save(tts_file)

                # Audio Playback
                play_audio(tts_file)
                update_display("Translation:", trans_text[:15])
                time.sleep(2)

            except sr.UnknownValueError:
                update_display("Could not", "understand audio")
            except sr.RequestError as e:
                update_display("STT Service", "Unavailable")
            except Exception as e:
                update_display("Error:", str(e)[:15])
                logging.error(f"Main Loop Error: {str(e)}")
            finally:
                # Cleanup temporary files
                for f in [tts_file, "/tmp/tts.wav"]:
                    try:
                        if os.path.exists(f):
                            os.remove(f)
                    except Exception as e:
                        logging.error(f"File Cleanup Error: {str(e)}")
                update_display("Ready", "Press GO")

        time.sleep(0.1)

except KeyboardInterrupt:
    GPIO.cleanup()
except Exception as e:
    logging.error(f"Fatal Error: {str(e)}")
    update_display("System Error", "Check logs")
    time.sleep(5)
    GPIO.cleanup()
    exit(1)
