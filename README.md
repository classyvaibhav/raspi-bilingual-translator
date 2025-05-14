# Portable Bilingual Language Translator

A compact, real-time bilingual translator built using Raspberry Pi Zero 2 W. This device captures spoken input, translates it between selected languages, and outputs the translated speech—ideal for multilingual communication on the go.

---

## 🎯 Features

- 🎤 **Speech Recognition** – Converts speech to text using `SpeechRecognition`.
- 🌐 **Language Translation** – Supports English, Hindi, Spanish, French, German, and Simplified Chinese using `googletrans`.
- 🔊 **Text-to-Speech (TTS)** – Plays translated speech using `gTTS`.
- 🖥️ **OLED Feedback** – Displays system status and selected languages using a 128x64 I2C OLED screen.
- 🔘 **Button-Controlled Interface** – 3 buttons for language selection and translation trigger.
- ⚡ **Portable Design** – Compact and battery-friendly using Raspberry Pi Zero 2 W.

---

## 🛠️ Hardware Requirements

| Component              | Description                      |
|------------------------|----------------------------------|
| Raspberry Pi Zero 2 W  | Main controller                  |
| USB Microphone         | For voice input                  |
| 128x64 OLED Display    | SSD1306 I2C display for feedback |
| 3x Tactile Buttons     | Language & control input         |
| PAM8403 Amplifier      | Audio output driver              |
| 3W Mini Speaker        | For output playback              |
| 5V/2A Power Supply     | USB adapter or battery pack      |

---

## ⚙️ Setup Instructions

### 1. 📦 Install Dependencies

```bash
sudo apt update
sudo apt install python3-pip python3-dev i2c-tools mpg321 portaudio19-dev
pip3 install SpeechRecognition googletrans==4.0.0-rc1 gTTS RPi.GPIO luma.oled pillow pyaudio
```

### 2. 🔧 Enable Interfaces

```bash
sudo raspi-config
# Under Interfacing Options:
# → Enable I2C
# → Enable SSH (optional for remote access)
```

### 3. 🔊 Configure Audio Output

Edit `/boot/config.txt`:
```ini
dtoverlay=audremap,pins_18_13
dtparam=i2c_arm=on
```

Then reboot:
```bash
sudo reboot
```

---

## 🔌 Wiring & GPIO Mapping

| Component        | GPIO Pin | Physical Pin |
|------------------|----------|--------------|
| OLED SDA         | GPIO2    | Pin 3        |
| OLED SCL         | GPIO3    | Pin 5        |
| Source Button    | GPIO17   | Pin 11       |
| Target Button    | GPIO27   | Pin 13       |
| Action Button    | GPIO22   | Pin 15       |
| PAM8403 VCC      | 5V       | Pin 2        |
| PAM8403 GND      | GND      | Pin 6        |

---

## ▶️ How to Use

1. Power on the Raspberry Pi.
2. The OLED will display current language settings.
3. Use:
   - **Left Button (GPIO17):** Change source language.
   - **Right Button (GPIO27):** Change target language.
   - **Center Button (GPIO22):** Record speech.
4. Speak clearly into the USB microphone.
5. The translated speech is automatically played through the speaker.

---

## 🧪 Troubleshooting

| Issue                 | Solution                                                                 |
|-----------------------|--------------------------------------------------------------------------|
| No audio output       | Use `sudo raspi-config → Audio → Force 3.5mm output`                     |
| Microphone not found  | Run `arecord -l` to verify device is detected                            |
| OLED not displaying   | Check I2C address with `i2cdetect -y 1` and confirm connections           |
| Translation errors    | Ensure internet connectivity is stable                                   |
| `googletrans` errors  | Use version `4.0.0-rc1` as others may be unstable                        |

---

## 📁 File Structure

```
Portable-Bilingual-Translator/
├── translator.py          # Main Python script
├── README.md              # Project documentation
├── LICENSE                # MIT License
├── docs/
│   ├── circuit_diagram.png
│   └── wiring_guide.png
```

---

## 📜 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## 🙌 Credits

Developed as a final year engineering project, inspired by Elektor’s Pi Translate and related community builds.

---

## 🔗 Useful Links

- [gTTS Docs](https://pypi.org/project/gTTS/)
- [Googletrans GitHub](https://github.com/ssut/py-googletrans)
- [SpeechRecognition](https://pypi.org/project/SpeechRecognition/)
- [luma.oled Docs](https://luma-oled.readthedocs.io/)
