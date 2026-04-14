import cv2
import mediapipe as mp
import pyautogui
import math
import threading
import time
import winsound
import os
import subprocess
import speech_recognition as sr
import uiautomation as auto
from pynput import mouse
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# --- Configuration ---
SMOOTHING = 0.15
MARGIN = 0.15
CLICK_THRESHOLD = 0.05
MODEL_PATH = r'D:\VS Code\Adv_Python\OpenCV\HandTracking\hand_landmarker.task'

# Application Paths
LAUNCH_MAP = {
    "notepad": "notepad.exe",
    "chrome": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    "vs code": os.path.expanduser("~") + "\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe"
}

# Global control flags
trigger_requested = False
program_running = True

# Initialize Speech & Mic
recognizer = sr.Recognizer()
recognizer.pause_threshold = 1.2 
mic = sr.Microphone()

PUNCTUATION = {
    "comma": ",", "full stop": ".", "period": ".", "question mark": "?",
    "exclamation mark": "!", "new line": "\n", "space": " ", "slash": "/", "backslash": "\\"
}

def play_beep(type="start"):
    if type == "start": winsound.Beep(1000, 150)
    elif type == "command": winsound.Beep(1500, 100)
    else: winsound.Beep(500, 300)

def is_text_field():
    try:
        x, y = pyautogui.position()
        element = auto.ControlFromPoint(x, y)
        if element:
            text_types = ["EditControl", "DocumentControl", "TextControl", "PaneControl", "DataItemControl", "ListItemControl"]
            return element.ControlTypeName in text_types or element.HasKeyboardFocus
        return False
    except Exception: return False

def voice_to_type():
    global program_running
    try:
        play_beep("start")
        print("--- VOICE MODE ACTIVE ---")
        
        with mic as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.8)
            while True:
                try:
                    audio = recognizer.listen(source, timeout=None, phrase_time_limit=12)
                    text = recognizer.recognize_google(audio).lower().strip()
                    print(f"Heard: {text}")

                    # --- 1. System & Program Exit ---
                    if "terminate" in text:
                        program_running = False
                        break
                    if "finish" in text: break
                    
                    # --- 2. Window & Volume & System ---
                    if "minimise" in text or "minimize" in text:
                        pyautogui.hotkey('win', 'down')
                        play_beep("command"); continue
                    
                    if "exit" in text or "close" in text:
                        pyautogui.hotkey('alt', 'f4')
                        play_beep("command"); continue

                    if "switch" in text: # Alt + Tab
                        pyautogui.hotkey('alt', 'tab')
                        play_beep("command"); continue

                    if "volume up" in text:
                        pyautogui.press('volumeup', presses=3)
                        play_beep("command"); continue

                    if "volume down" in text:
                        pyautogui.press('volumedown', presses=3)
                        play_beep("command"); continue

                    if "mute" in text:
                        pyautogui.press('volumemute')
                        play_beep("command"); continue

                    # --- 3. YouTube Specific Commands ---
                    if "play" in text or "pause" in text:
                        pyautogui.press('k') # YouTube shortcut
                        play_beep("command"); continue
                    
                    if "full screen" in text:
                        pyautogui.press('f')
                        play_beep("command"); continue
                    
                    if "skip" in text:
                        pyautogui.press('j' if "back" in text else 'l') # J for -10s, L for +10s
                        play_beep("command"); continue

                    # --- 4. Opening Applications ---
                    if "open" in text:
                        for app in LAUNCH_MAP:
                            if app in text:
                                subprocess.Popen(LAUNCH_MAP[app])
                                play_beep("command"); break
                        continue

                    # --- 5. Navigation & Editing ---
                    if "enter" in text or "search" in text:
                        pyautogui.press('enter')
                        play_beep("command"); continue
                    
                    if "undo" in text:
                        pyautogui.hotkey('ctrl', 'z')
                        play_beep("command"); continue

                    if "previous line" in text:
                        pyautogui.press(['up', 'end'])
                        play_beep("command"); continue

                    if text == "backspace":
                        pyautogui.press('backspace')
                        play_beep("command"); continue
                    
                    if text == "clear":
                        pyautogui.hotkey('ctrl', 'a')
                        pyautogui.press('backspace')
                        play_beep("command"); continue

                    # --- 6. Typing ---
                    if text in PUNCTUATION:
                        pyautogui.write(PUNCTUATION[text])
                    else:
                        pyautogui.write(text.capitalize() + " ")
                        
                except sr.UnknownValueError: continue 
                except Exception: continue
        play_beep("stop")
    except Exception: play_beep("stop")

# --- Mouse Listener ---
def on_click(x, y, button, pressed):
    global trigger_requested
    if pressed and button == mouse.Button.left:
        trigger_requested = True

mouse_listener = mouse.Listener(on_click=on_click)
mouse_listener.start()

# --- Hand Tracking ---
base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
options = vision.HandLandmarkerOptions(base_options=base_options, num_hands=1)
detector = vision.HandLandmarker.create_from_options(options)

cap = cv2.VideoCapture(0)
screen_w, screen_h = pyautogui.size()
prev_x, prev_y = screen_w // 2, screen_h // 2
already_clicked = False 

while cap.isOpened() and program_running:
    success, img = cap.read()
    if not success: break

    img = cv2.flip(img, 1)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)
    result = detector.detect(mp_image)

    if result.hand_landmarks:
        landmarks = result.hand_landmarks[0]
        index_tip, thumb_tip = landmarks[8], landmarks[4]

        # Movement Mapping
        norm_x = max(0, min(1, (index_tip.x - MARGIN) / (1 - 2 * MARGIN)))
        norm_y = max(0, min(1, (index_tip.y - MARGIN) / (1 - 2 * MARGIN)))
        target_x, target_y = norm_x * screen_w, norm_y * screen_h
        curr_x = prev_x + (target_x - prev_x) * SMOOTHING
        curr_y = prev_y + (target_y - prev_y) * SMOOTHING
        pyautogui.moveTo(int(curr_x), int(curr_y), _pause=False)
        prev_x, prev_y = curr_x, curr_y

        dist = math.hypot(index_tip.x - thumb_tip.x, index_tip.y - thumb_tip.y)
        if dist < CLICK_THRESHOLD:
            if not already_clicked:
                pyautogui.click()
                already_clicked = True
                trigger_requested = True
        else: already_clicked = False

    if trigger_requested:
        time.sleep(0.4)
        if not any(t.name == "VoiceThread" for t in threading.enumerate()):
            v_thread = threading.Thread(target=voice_to_type, name="VoiceThread")
            v_thread.daemon = True
            v_thread.start()
        trigger_requested = False

    cv2.imshow("Full AI Assistant", img)
    if cv2.waitKey(1) & 0xFF == ord('q'): break

cap.release()
cv2.destroyAllWindows()
mouse_listener.stop()