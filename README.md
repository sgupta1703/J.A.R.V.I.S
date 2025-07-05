# JARVIS: Just A Rather Very Intelligent System

JARVIS is a voice-activated AI assistant built with wake-word detection, real-time speech recognition, generative AI (Gemini), and a PyQt6-powered interactive UI — all working seamlessly on your local machine.

> "Yes, sir?" — JARVIS wakes up with your voice and serves your commands like the iconic assistant from Iron Man.

---

## Features

- **Wake-Word Activation**: Say "Jarvis" to wake the assistant using Porcupine
- **Voice Recognition**: Real-time command transcription with Vosk
- **Conversational AI**: Powered by Google Gemini for smart replies
- **Weather Forecasting**: Fetch live weather via WeatherAPI
- **Time Announcements**: Ask for current time
- **System Commands**: Take screenshots, empty recycle bin, lock screen
- **Clipboard Search**: Automatically Google search your clipboard text
- **App Launcher**: Voice-launch apps like Chrome, VS Code, Spotify, Notepad, etc.
- **Dynamic UI**: PyQt6 + PyQtGraph visualizer mimics JARVIS's voice modulation in real-time

---

## Demo Preview

> *(Include a video demo here during the hackathon submission)*  
> ![demo](demo.gif) or [Watch demo on YouTube](https://your-demo-link)

---

## Tech Stack

| Component         | Libraries / Tools Used             |
|------------------|-------------------------------------|
| GUI               | PyQt6, PyQtGraph                   |
| Speech-to-Text    | Vosk                               |
| Wake Word         | Porcupine (by Picovoice)           |
| TTS               | pyttsx3                            |
| LLM               | Gemini API                         |
| Weather API       | WeatherAPI                         |
| Audio Processing  | sounddevice, struct                |
| OS Integration    | subprocess, ctypes, os             |
| GUI Automation    | pyautogui                          |
| Clipboard Access  | pyperclip                          |
| HTTP & Web APIs   | requests, json, webbrowser         |
| Env Management    | python-dotenv                      |
| Time & Date       | datetime, time                     |
| Math & Graphing   | numpy                              |

---

## Setup Instructions

Follow the steps below to set up and run JARVIS on your local machine.

---

### Clone the Repository

```
git clone https://github.com/sgupta1703/J.A.R.V.I.S.git
cd J.A.R.V.I.S
```

### Set Up the .env file

Create a .env file and populate as such. Use your own API keys.

```
GEMINI_API_KEY=your_gemini_api_key_here
weather_api_key=your_weatherapi_key_here
access_key=your_porcupine_access_key_here
```

### Install Python Dependencies

Make sure you have Python 3.8+ installed. Then, install all required packages:

```
pip install -r requirements.txt
```

### Download the Vosk Speech Model

Download *vosk-model-small-en-us-0.15* from **[VOSK Models](https://alphacephei.com/vosk/models)** to enable offline speech recognition.
Unzip it and rename the folder to **model**
Place it in your project root like this:

```
J.A.R.V.I.S/
├── model/
│   └── vosk files here
```

Ultimately your folder structure should be as such:

```
J.A.R.V.I.S/
├── __pycache__
├── model/
    └── vosk-model-small-en-us-0.15/
├── .env
├── app.py
├── jarvis_chat.py
├── requirements.txt
```

### Run the App

To start the assistant:

```
python app.py
```
You should see the GUI appear. Say "Jarvis" to wake the assistant and wait till the end of "Yes, sir" to request your question.






