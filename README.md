# AI Hand Gesture & Voice Screen Controller

A powerful AI-driven assistant that allows you to control your computer using intuitive hand gestures and voice commands. 

## 🚀 Features

- **Hand Gesture Mouse Control**: Move your mouse cursor by simply moving your index finger in front of the camera.
- **Gesture Clicking**: Use a "pinch" gesture (touching index finger and thumb) to trigger left clicks.
- **Voice Commands**: Perform variety of system and application actions using your voice.
- **Application Integration**:
  - **Media Control**: Play/Pause, Skip, Fullscreen, and Volume adjustment for YouTube and other media players.
  - **Window Management**: Minimize, Exit/Close, and Switch (Alt+Tab) windows.
  - **Application Launching**: Quickly open Notepad, Chrome, or VS Code.
  - **Voice Typing**: Dictate text directly into text fields with support for basic punctuation.
  - **Editing**: Support for Undo, Enter, Backspace, and Clear commands.

## 🛠️ Setup & Installation

### Prerequisites
- Python 3.8+
- Webcam (for hand tracking)
- Microphone (for voice commands)

### Installation Steps

1. **Clone the repository**:
   ```bash
   git clone https://github.com/divyansh2102t-dev/Hand-Gesture-Screen-Control.git
   cd Hand-Gesture-Screen-Control
   ```

2. **Install dependencies**:
   ```bash
   pip install opencv-python mediapipe pyautogui SpeechRecognition pynput winsound uiautomation
   ```

3. **Download the MediaPipe Model**:
   Download the `hand_landmarker.task` file and update the `MODEL_PATH` in `main.py` to point to its location on your system.
   > [!IMPORTANT]
   > Ensure the `MODEL_PATH` in `main.py` is correct for your local environment.

## 🖱️ Usage

1. **Run the Application**:
   ```bash
   python main.py
   ```
2. **Move Cursor**: Point your index finger at the camera and move it.
3. **Left Click**: Pinch your index finger and thumb together.
4. **Trigger Voice Mode**: Performing a click (pinch) will activate the voice listener (you will hear a beep).
5. **Voice Actions**:
   - Say **"open chrome"** to launch the browser.
   - Say **"volume up"** or **"volume down"** to adjust audio.
   - Say **"play"** or **"pause"** for video control.
   - Say **"minimise"** to hide the current window.
   - Say **"finish"** to stop the voice mode.
   - Say **"terminate"** to exit the entire program.

## ⚙️ Configuration

You can adjust the following parameters in `main.py`:
- `SMOOTHING`: Adjusts mouse movement sensitivity (default: 0.15).
- `MARGIN`: Sets the active area for hand tracking (default: 0.15).
- `CLICK_THRESHOLD`: Sensitivity for the pinch gesture (default: 0.05).
- `LAUNCH_MAP`: Add or update paths to your favorite applications.

## ⚖️ License
This project is licensed under the MIT License.
