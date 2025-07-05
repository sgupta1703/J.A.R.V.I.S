import struct
import json
import requests
import pyttsx3
import sounddevice as sd
import pvporcupine
from vosk import Model, KaldiRecognizer
import subprocess
import webbrowser
import datetime
import os
import ctypes
import pyautogui
import pyperclip
import time
from dotenv import load_dotenv

engine = pyttsx3.init()
voices = engine.getProperty('voices')
for v in voices:
    if 'david' in v.name.lower():
        engine.setProperty('voice', v.id)
        break
engine.setProperty('rate', 206)
engine.setProperty('volume', 1.0)

def speak(text: str, display_callback=None, visualizer_callback=None):
    if visualizer_callback:
        try:
            visualizer_callback(True)
        except Exception:
            pass
    if display_callback:
        try:
            display_callback(text)
        except Exception:
            pass
    try:
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        if display_callback:
            try:
                display_callback(f"(TTS error: {e})")
            except Exception:
                pass
        print(f"TTS error: {e}")
    if visualizer_callback:
        try:
            visualizer_callback(False)
        except Exception:
            pass


load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def ask_jarvis(prompt: str, display_callback=None, visualizer_callback=None):
    """
    Send the prompt to Gemini API (Generative Language) and get a response.
    Forward status and reply via display_callback, and speak via speak().
    """
    if GEMINI_API_KEY is None:
        err = "GEMINI_API_KEY is not set. Cannot contact Gemini API."
        print(err)
        speak(err, display_callback=display_callback, visualizer_callback=visualizer_callback)
        return

    url = (
        "https://generativelanguage.googleapis.com/"
        "v1beta/models/gemini-2.0-flash:generateContent"
        f"?key={GEMINI_API_KEY}"
    )
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{
            "parts": [
                {"text": (
                    "You are JARVIS (Just A Rather Very Intelligent System), a brief, to-the-point AI assistant. "
                    "Always refer to the user as 'sir'. Make sure to be as concise as possible, up to the point. Also ensure to refer to the JARVIS assistant in the Iron Man movies as a reference for your responses but do not include anything about the movies themselves. "
                )},
                {"text": prompt}
            ]
        }]
    }
    if display_callback:
        try:
            display_callback(f"(Sending prompt to Gemini: \"{prompt}\")")
        except Exception:
            pass

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
    except Exception as e:
        err = f"Error contacting Gemini API: {e}"
        print(err)
        speak(err, display_callback=display_callback, visualizer_callback=visualizer_callback)
        return

    try:
        data = resp.json()
    except ValueError:
        err = "Sorry, I got a non-JSON response from Gemini."
        speak(err, display_callback=display_callback, visualizer_callback=visualizer_callback)
        print("Non-JSON response:", resp.text)
        return

    if resp.status_code != 200:
        err_msg = data.get("error", {}).get("message", resp.text)
        err = f"Sorry, Gemini returned an error: {err_msg}"
        speak(err, display_callback=display_callback, visualizer_callback=visualizer_callback)
        return

    candidates = data.get("candidates")
    if not candidates or not isinstance(candidates, list):
        err = "Sorry, I didn’t receive any candidates from Gemini."
        speak(err, display_callback=display_callback, visualizer_callback=visualizer_callback)
        return

    first = candidates[0].get("content", {})
    parts = first.get("parts")
    if not parts or not isinstance(parts, list):
        err = "Sorry, unexpected response format from Gemini."
        speak(err, display_callback=display_callback, visualizer_callback=visualizer_callback)
        return

    reply = parts[0].get("text")
    if not isinstance(reply, str):
        err = "Sorry, I couldn't read the assistant’s reply."
        speak(err, display_callback=display_callback, visualizer_callback=visualizer_callback)
        return

    print("\nJARVIS:", reply)
    if display_callback:
        try:
            display_callback(reply)
        except Exception:
            pass
    speak(reply, display_callback=display_callback, visualizer_callback=visualizer_callback)


try:
    vosk_model = Model("model")
except Exception as e:
    print(f"Failed to load VOSK model: {e}")
    vosk_model = None

porc = None
try:
    porc = pvporcupine.create(
        access_key=os.getenv("access_key"),
        keywords=["jarvis"]
    )
except Exception as e:
    print(f"Failed to initialize Porcupine wake-word detector: {e}")
    porc = None

def handle_command(wav_stream):
    if vosk_model is None:
        print("VOSK model not loaded; cannot recognize speech.")
        return ""

    rec = KaldiRecognizer(vosk_model, porc.sample_rate if porc else 16000)
    print("[Listening for command…]")
    while True:
        try:
            data, _ = wav_stream.read(porc.frame_length if porc else 4000)
        except Exception as e:
            print(f"Error reading from audio stream: {e}")
            return ""
        try:
            pcm = struct.unpack_from(f"<{porc.frame_length}h", data) if porc else None
        except Exception:
            pcm = None
        if vosk_model and pcm is not None:
            if rec.AcceptWaveform(bytes(data)):
                try:
                    result = json.loads(rec.Result())
                except Exception:
                    continue
                text = result.get("text", "").strip().lower()
                print(f"You said: {text}")
                return text
        else:
            return ""

def get_my_location():
    try:
        r = requests.get("http://ip-api.com/json/", timeout=3)
        r.raise_for_status()
        loc = r.json()
        return (
            loc.get("city"),
            loc.get("regionName"),
            loc.get("lat"),
            loc.get("lon")
        )
    except Exception as e:
        print("Location lookup failed:", e)
        return (None, None, None, None)

def tell_weather(display_callback=None, visualizer_callback=None):
    """
    Fetch current weather via WeatherAPI and speak/display it.
    """
    WEATHER_API_KEY = os.getenv("weather_api_key")
    if WEATHER_API_KEY is None:
        err = "weather_api_key not set; cannot fetch weather."
        speak(err, display_callback=display_callback, visualizer_callback=visualizer_callback)
        return

    city, region, lat, lon = get_my_location()
    if city:
        query = city
    elif lat is not None and lon is not None:
        query = f"{lat},{lon}"
    else:
        speak("Sorry, I couldn't figure out your location, sir.",
              display_callback=display_callback, visualizer_callback=visualizer_callback)
        return

    url = (
        f"http://api.weatherapi.com/v1/current.json"
        f"?key={WEATHER_API_KEY}"
        f"&q={query}"
        f"&aqi=no"
    )
    if display_callback:
        try:
            display_callback(f"(Fetching weather for {query})")
        except Exception:
            pass

    try:
        resp = requests.get(url, timeout=5)
        data = resp.json()
    except Exception as e:
        print("WeatherAPI request failed:", e)
        speak("Sorry, I couldn't connect to the weather service, sir.",
              display_callback=display_callback, visualizer_callback=visualizer_callback)
        return

    if resp.status_code == 200 and "current" in data:
        temp_c = data["current"].get("temp_c")
        cond = data["current"].get("condition", {}).get("text", "")
        loc_name = data.get("location", {}).get("name", "")
        msg = f"The weather in {loc_name} is {cond} with a temperature of {temp_c} degrees Celsius, sir."
        speak(msg, display_callback=display_callback, visualizer_callback=visualizer_callback)
    elif "error" in data:
        msg = data["error"].get("message", "an unknown error")
        speak(f"WeatherAPI error: {msg}, sir.",
              display_callback=display_callback, visualizer_callback=visualizer_callback)
    else:
        speak("Sorry, I couldn't fetch the weather, sir.",
              display_callback=display_callback, visualizer_callback=visualizer_callback)

def tell_time(display_callback=None, visualizer_callback=None):
    now = datetime.datetime.now()
    timestr = now.strftime('%I:%M %p')
    msg = f"The current time is {timestr}, sir."
    speak(msg, display_callback=display_callback, visualizer_callback=visualizer_callback)

def take_screenshot(display_callback=None, visualizer_callback=None):
    try:
        ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        pdir = os.path.join(os.environ.get('USERPROFILE', ''), 'Pictures')
        if not pdir:
            raise RuntimeError("USERPROFILE not set")
        os.makedirs(pdir, exist_ok=True)
        path = os.path.join(pdir, f'screenshot_{ts}.png')
        pyautogui.screenshot().save(path)
        msg = f"Screenshot saved: {path}, sir."
        speak(msg, display_callback=display_callback, visualizer_callback=visualizer_callback)
    except Exception as e:
        print(f"Screenshot error: {e}")
        speak(f"Failed to take screenshot: {e}", display_callback=display_callback,
              visualizer_callback=visualizer_callback)

def empty_recycle_bin(display_callback=None, visualizer_callback=None):
    try:
        ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 0)
        msg = "Recycle bin emptied, sir."
        speak(msg, display_callback=display_callback, visualizer_callback=visualizer_callback)
    except Exception as e:
        print(f"Empty recycle bin error: {e}")
        speak(f"Failed to empty recycle bin: {e}", display_callback=display_callback,
              visualizer_callback=visualizer_callback)

def lock_screen(display_callback=None, visualizer_callback=None):
    try:
        ctypes.windll.user32.LockWorkStation()
    except Exception as e:
        print(f"Lock screen error: {e}")
        speak(f"Failed to lock screen: {e}", display_callback=display_callback,
              visualizer_callback=visualizer_callback)

def open_application(name: str, display_callback=None, visualizer_callback=None):
    apps = {
        'browser': lambda: webbrowser.open('https://www.google.com'),
        'youtube': lambda: webbrowser.open('https://www.youtube.com'),
        'notepad': lambda: subprocess.Popen(['notepad']),
        'calculator': lambda: subprocess.Popen(['calc']),
        'terminal': lambda: subprocess.Popen(['wt']),
        'spotify': lambda: subprocess.Popen([
            os.path.expandvars(r'%USERPROFILE%\AppData\Roaming\Spotify\Spotify.exe')
        ]),
        'vscode': lambda: subprocess.Popen([
            os.path.expandvars(r'%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe')
        ]),
        'epic': lambda: subprocess.Popen([
            os.path.expandvars(r'%ProgramFiles(x86)%\Epic Games\Launcher\Portal\Binaries\Win32\EpicGamesLauncher.exe')
        ]),
        'dashboard': lambda: launch_dashboard(display_callback=display_callback, visualizer_callback=visualizer_callback),
        'teams': lambda: subprocess.Popen([
            os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Teams\current\Teams.exe')
        ]),
    }
    try:
        action = apps.get(name)
        if action:
            action()
            msg = f"Opening {name}, sir."
            speak(msg, display_callback=display_callback, visualizer_callback=visualizer_callback)
        else:
            msg = "I don't know that application, sir."
            speak(msg, display_callback=display_callback, visualizer_callback=visualizer_callback)
    except Exception as e:
        print(f"Error opening {name}: {e}")
        speak(f"Something went wrong opening {name}, sir.",
              display_callback=display_callback, visualizer_callback=visualizer_callback)

def handle_action(command: str, display_callback=None, visualizer_callback=None):
    cmd = command.lower().strip()
    if not cmd:
        return
    if any(k in cmd for k in ('weather', 'temperature', 'forecast')):
        tell_weather(display_callback=display_callback, visualizer_callback=visualizer_callback)
        return

    if 'downloads' in cmd:
        path = os.path.join(os.environ.get('USERPROFILE', ''), 'Downloads')
        try:
            subprocess.Popen(['explorer', path])
            msg = "Opening Downloads folder, sir."
            speak(msg, display_callback=display_callback, visualizer_callback=visualizer_callback)
        except Exception as e:
            print(f"Open Downloads error: {e}")
            speak(f"Failed to open Downloads: {e}", display_callback=display_callback,
                  visualizer_callback=visualizer_callback)
        return
    if 'documents' in cmd:
        path = os.path.join(os.environ.get('USERPROFILE', ''), 'Documents')
        try:
            subprocess.Popen(['explorer', path])
            msg = "Opening Documents folder, sir."
            speak(msg, display_callback=display_callback, visualizer_callback=visualizer_callback)
        except Exception as e:
            print(f"Open Documents error: {e}")
            speak(f"Failed to open Documents: {e}", display_callback=display_callback,
                  visualizer_callback=visualizer_callback)
        return
    if 'desktop' in cmd:
        path = os.path.join(os.environ.get('USERPROFILE', ''), 'Desktop')
        try:
            subprocess.Popen(['explorer', path])
            msg = "Opening Desktop folder, sir."
            speak(msg, display_callback=display_callback, visualizer_callback=visualizer_callback)
        except Exception as e:
            print(f"Open Desktop error: {e}")
            speak(f"Failed to open Desktop: {e}", display_callback=display_callback,
                  visualizer_callback=visualizer_callback)
        return

    if any(k in cmd for k in ('screenshot', 'screen shot', 'screen capture', 'screen grab', 'take a picture')):
        take_screenshot(display_callback=display_callback, visualizer_callback=visualizer_callback)
        return

    if 'recycle' in cmd:
        empty_recycle_bin(display_callback=display_callback, visualizer_callback=visualizer_callback)
        return

    if any(k in cmd for k in ('lock', 'lock screen', 'lock the screen', 'close the screen')):
        lock_screen(display_callback=display_callback, visualizer_callback=visualizer_callback)
        return

    if any(k in cmd for k in ('clipboard', 'search this', 'search clipboard')):
        speak("Searching the clipboard, sir.", display_callback=display_callback, visualizer_callback=visualizer_callback)
        time.sleep(1)
        try:
            q = pyperclip.paste().strip()
        except Exception:
            q = ""
        if q:
            webbrowser.open(f"https://www.google.com/search?q={q.replace(' ', '+')}")
            msg = "Here are the search results, sir."
            speak(msg, display_callback=display_callback, visualizer_callback=visualizer_callback)
        else:
            speak("Clipboard is empty, sir.", display_callback=display_callback, visualizer_callback=visualizer_callback)
        return

    if any(k in cmd for k in ('open', 'launch', 'start')):
        aliases = {
            'browser': ['browser', 'chrome', 'firefox', 'edge', 'google', 'web'],
            'youtube': ['youtube', 'yt', 'you tube', 'tube'],
            'notepad': ['notepad', 'notes'],
            'calculator': ['calc', 'calculator'],
            'terminal': ['terminal', 'cmd', 'powershell', 'shell'],
            'spotify': ['spotify', 'music'],
            'vscode': ['vscode', 'code', 'visual studio code'],
            'epic': ['epic', 'epic games'],
            'dashboard': ['dashboard', 'home', 'panel'],
            'teams': ['teams', 'microsoft teams', 'ms teams'],
        }
        for name, keys in aliases.items():
            if any(k in cmd for k in keys):
                open_application(name, display_callback=display_callback, visualizer_callback=visualizer_callback)
                return
        speak("Which application should I open, sir?", display_callback=display_callback,
              visualizer_callback=visualizer_callback)
        return

    if 'time' in cmd:
        tell_time(display_callback=display_callback, visualizer_callback=visualizer_callback)
        return

    if cmd.startswith("search "):
        query = cmd.replace("search", "", 1).strip()
        if query:
            msg = f"Searching for {query}, sir."
            speak(msg, display_callback=display_callback, visualizer_callback=visualizer_callback)
            webbrowser.open(f"https://www.google.com/search?q={query.replace(' ', '+')}")
            speak("Here are the search results, sir.", display_callback=display_callback, visualizer_callback=visualizer_callback)
        else:
            speak("What would you like me to search for, sir?", display_callback=display_callback,
                  visualizer_callback=visualizer_callback)
        return

    ask_jarvis(cmd, display_callback=display_callback, visualizer_callback=visualizer_callback)

def launch_dashboard(display_callback=None, visualizer_callback=None):
    try:
        ps1_path = os.path.expandvars(r"%USERPROFILE%\J.A.R.V.I.S\synq-start.ps1")
        subprocess.Popen(["powershell", "-ExecutionPolicy", "Bypass", "-File", ps1_path])
        time.sleep(3)
        webbrowser.open("http://localhost:3000", new=2)
        msg = "Dashboard launched, sir."
        speak(msg, display_callback=display_callback, visualizer_callback=visualizer_callback)
    except Exception as e:
        print("Error launching dashboard:", e)
        speak(f"Error launching dashboard: {e}", display_callback=display_callback,
              visualizer_callback=visualizer_callback)

def run_jarvis(display_callback=None, visualizer_callback=None):
    print("Jarvis is ready, sir.")


    if porc is None:
        print("Wake-word detector not initialized. Exiting run_jarvis.")
        if display_callback:
            try:
                display_callback("Wake-word detector not initialized.")
            except Exception:
                pass
        return

    try:
        with sd.RawInputStream(
            samplerate=porc.sample_rate,
            blocksize=porc.frame_length,
            dtype="int16",
            channels=1,
        ) as stream:
            try:
                while True:
                    data = stream.read(porc.frame_length)[0]
                    pcm = struct.unpack_from(f"<{porc.frame_length}h", data)
                    if porc.process(pcm) >= 0:
                        print("\n[Wake-word detected!]")
                        speak("Yes, sir?", visualizer_callback=visualizer_callback)
                        cmd = handle_command(stream)
                        if not cmd:
                            continue
                        if any(w in cmd for w in ("exit", "quit", "goodbye", "stop", "bye")):
                            speak("Goodbye, sir.", display_callback=display_callback, visualizer_callback=visualizer_callback)
                            break
                        handle_action(cmd, display_callback=display_callback, visualizer_callback=visualizer_callback)
            except KeyboardInterrupt:
                print("\nInterrupted by user")
                if display_callback:
                    try:
                        display_callback("Interrupted by user.")
                    except Exception:
                        pass
            except Exception as e:
                print(f"Error in run_jarvis loop: {e}")
                if display_callback:
                    try:
                        display_callback(f"Error in main loop: {e}")
                    except Exception:
                        pass
            finally:
                try:
                    porc.delete()
                except Exception:
                    pass
    except Exception as e:
        print(f"Failed to open audio stream: {e}")
        if display_callback:
            try:
                display_callback(f"Audio stream error: {e}")
            except Exception:
                pass


if __name__ == "__main__":
    run_jarvis()
