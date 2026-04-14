import cv2
import mediapipe as mp
import pyautogui
import math
import threading
import time
import winsound
import os
import subprocess
import shutil
import speech_recognition as sr
import uiautomation as auto
from pynput import mouse
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

SMOOTHING_BASE = 0.2
MARGIN = 0.15
CLICK_THRESHOLD = 0.05
FREEZE_DURATION = 0.25 
MODEL_PATH = r'D:\VS Code\Adv_Python\OpenCV\HandTracking\hand_landmarker.task'

if not os.path.exists(MODEL_PATH):
    MODEL_PATH = os.path.join(os.getcwd(), 'hand_landmarker.task')

HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20),
    (0, 17), (5, 9), (9, 13), (13, 17)
]

def find_app(name, default_path):
    if shutil.which(name): return name
    if os.path.exists(default_path): return default_path
    return None

LAUNCH_MAP = {
    "notepad": find_app("notepad.exe", "notepad.exe"),
    "chrome": find_app("chrome.exe", "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"),
    "vs code": find_app("code.exe", os.path.expanduser("~") + "\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe")
}

trigger_requested = False
program_running = True
is_voice_mode = False
last_click_time = 0

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

def is_text_field(x=None, y=None):
    try:
        if x is None or y is None:
            x, y = pyautogui.position()
        element = auto.ControlFromPoint(x, y)
        if element:
            text_types = ["EditControl", "DocumentControl", "TextControl", "PaneControl", "DataItemControl", "ListItemControl"]
            return element.ControlTypeName in text_types or element.HasKeyboardFocus
        return False
    except Exception: return False

def draw_hand_custom(img, landmarks, clicked):
    h, w, _ = img.shape
    color = (0, 0, 255) if clicked else (0, 255, 0)
    for connection in HAND_CONNECTIONS:
        start_idx, end_idx = connection
        p1 = (int(landmarks[start_idx].x * w), int(landmarks[start_idx].y * h))
        p2 = (int(landmarks[end_idx].x * w), int(landmarks[end_idx].y * h))
        cv2.line(img, p1, p2, color, 2)
    for lm in landmarks:
        cv2.circle(img, (int(lm.x * w), int(lm.y * h)), 3, (255, 255, 255), -1)

def voice_to_type():
    global program_running, is_voice_mode
    is_voice_mode = True
    try:
        play_beep("start")
        print("--- VOICE MODE ACTIVE ---")
        with mic as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.8)
            while True:
                try:
                    audio = recognizer.listen(source, timeout=None, phrase_time_limit=12)
                    text = recognizer.recognize_google(audio).lower().strip()
                    if "terminate" in text:
                        program_running = False; break
                    if "finish" in text: break
                    if "minimise" in text: pyautogui.hotkey('win', 'down'); play_beep("command"); continue
                    if "exit" in text or "close" in text: pyautogui.hotkey('alt', 'f4'); play_beep("command"); continue
                    if "switch" in text: pyautogui.hotkey('alt', 'tab'); play_beep("command"); continue
                    if "volume up" in text: pyautogui.press('volumeup', presses=3); play_beep("command"); continue
                    if "volume down" in text: pyautogui.press('volumedown', presses=3); play_beep("command"); continue
                    if "mute" in text: pyautogui.press('volumemute'); play_beep("command"); continue
                    if "play" in text or "pause" in text: pyautogui.press('k'); play_beep("command"); continue
                    if "full screen" in text: pyautogui.press('f'); play_beep("command"); continue
                    if "skip" in text: pyautogui.press('j' if "back" in text else 'l'); play_beep("command"); continue
                    if "open" in text:
                        for app in LAUNCH_MAP:
                            if LAUNCH_MAP[app] and app in text: subprocess.Popen(LAUNCH_MAP[app]); play_beep("command"); break
                        continue
                    if "enter" in text or "search" in text: pyautogui.press('enter'); play_beep("command"); continue
                    if "undo" in text: pyautogui.hotkey('ctrl', 'z'); play_beep("command"); continue
                    if text == "backspace": pyautogui.press('backspace'); play_beep("command"); continue
                    if is_text_field():
                        if text in PUNCTUATION: pyautogui.write(PUNCTUATION[text])
                        else: pyautogui.write(text.capitalize() + " ")
                except: continue
    finally:
        is_voice_mode = False
        play_beep("stop")

def on_click(x, y, button, pressed):
    global trigger_requested
    if pressed and button == mouse.Button.left:
        trigger_requested = True

mouse_listener = mouse.Listener(on_click=on_click)
mouse_listener.start()

base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
options = vision.HandLandmarkerOptions(base_options=base_options, num_hands=1)
detector = vision.HandLandmarker.create_from_options(options)

cap = cv2.VideoCapture(0)
screen_w, screen_h = pyautogui.size()
prev_x, prev_y = screen_w // 2, screen_h // 2
already_clicked = False 
frame_count = 0
in_text_field = False

while cap.isOpened() and program_running:
    success, img = cap.read()
    if not success: break
    img = cv2.flip(img, 1)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)
    result = detector.detect(mp_image)

    if result.hand_landmarks:
        landmarks = result.hand_landmarks[0]
        draw_hand_custom(img, landmarks, already_clicked)
        
        index_tip, thumb_tip = landmarks[8], landmarks[4]
        
        norm_x = max(0, min(1, (index_tip.x - MARGIN) / (1 - 2 * MARGIN)))
        norm_y = max(0, min(1, (index_tip.y - MARGIN) / (1 - 2 * MARGIN)))
        target_x, target_y = norm_x * screen_w, norm_y * screen_h
        
        dist_moved = math.hypot(target_x - prev_x, target_y - prev_y)
        smoothing = SMOOTHING_BASE if dist_moved > 50 else 0.08
        
        frame_count += 1
        if frame_count % 10 == 0:
            in_text_field = is_text_field(int(prev_x), int(prev_y))
        
        if in_text_field: smoothing *= 0.4
        
        curr_x = prev_x + (target_x - prev_x) * smoothing
        curr_y = prev_y + (target_y - prev_y) * smoothing
        
        if (time.time() - last_click_time) > FREEZE_DURATION:
            pyautogui.moveTo(int(curr_x), int(curr_y), _pause=False)
            prev_x, prev_y = curr_x, curr_y

        dist = math.hypot(index_tip.x - thumb_tip.x, index_tip.y - thumb_tip.y)
        if dist < CLICK_THRESHOLD:
            if not already_clicked:
                pyautogui.click()
                already_clicked = True
                last_click_time = time.time()
                trigger_requested = True
        else: already_clicked = False

    if trigger_requested:
        time.sleep(0.4)
        if not any(t.name == "VoiceThread" for t in threading.enumerate()):
            v_thread = threading.Thread(target=voice_to_type, name="VoiceThread", daemon=True)
            v_thread.start()
        trigger_requested = False

    status_text = "VOICE MODE" if is_voice_mode else "MOUSE MODE"
    status_color = (0, 255, 255) if is_voice_mode else (0, 255, 0)
    cv2.putText(img, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)
    
    if (time.time() - last_click_time) < FREEZE_DURATION:
        cv2.putText(img, "PRECISION LOCK", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    elif in_text_field:
        cv2.putText(img, "MAGNETIC AIM", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

    cv2.imshow("Full AI Assistant (Precision Mode)", img)
    if cv2.waitKey(1) & 0xFF == ord('q'): break

cap.release()
cv2.destroyAllWindows()
mouse_listener.stop()

