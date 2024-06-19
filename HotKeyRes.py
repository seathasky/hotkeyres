import keyboard
import win32api
import win32con
import win32gui
import json
import os
import time
import threading
from pystray import Icon, MenuItem, Menu
from PIL import Image, ImageDraw, ImageFont

# Constants
CONFIG_FILE = 'config.json'
DEFAULT_RESOLUTIONS = [
    {"name": "Resolution 1", "width": 2560, "height": 1600, "refresh_rate": 165},
    {"name": "Resolution 2", "width": 1280, "height": 720, "refresh_rate": 60}
]
current_resolution = None
notification_thread = None
notification_window_handle = None
notification_lock = threading.Lock()

# Function to create a default config file
def create_default_config():
    default_config = {
        "resolution_switch_keybind": "ctrl+f4",
        "default_resolutions": DEFAULT_RESOLUTIONS
    }
    with open(CONFIG_FILE, 'w') as f:
        json.dump(default_config, f, indent=4)

# Function to load the config file
def load_config():
    if not os.path.exists(CONFIG_FILE):
        create_default_config()
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
    return config

# Load the config file
config = load_config()
resolution_switch_keybind = config["resolution_switch_keybind"]
default_resolutions = config["default_resolutions"]

# Function to set resolution
def set_resolution(width, height, refresh_rate):
    try:
        devmode = win32api.EnumDisplaySettings(None, 0)
        devmode.PelsWidth = width
        devmode.PelsHeight = height
        devmode.DisplayFrequency = refresh_rate
        devmode.Fields = win32con.DM_PELSWIDTH | win32con.DM_PELSHEIGHT | win32con.DM_DISPLAYFREQUENCY

        result = win32api.ChangeDisplaySettings(devmode, 0)
        if result != win32con.DISP_CHANGE_SUCCESSFUL:
            print(f"Failed to change resolution. Error code: {result}")
        else:
            print(f"Resolution set to {height}p at {refresh_rate}Hz")
            show_notification(f"Resolution changed to {height}p at {refresh_rate}Hz")

    except Exception as e:
        print(f"An error occurred while setting resolution: {e}")

# Function to toggle resolution
def toggle_resolution():
    global current_resolution
    if current_resolution is None or current_resolution == default_resolutions[0]:
        set_resolution(default_resolutions[1]["width"], default_resolutions[1]["height"], default_resolutions[1]["refresh_rate"])
        current_resolution = default_resolutions[1]
    else:
        set_resolution(default_resolutions[0]["width"], default_resolutions[0]["height"], default_resolutions[0]["refresh_rate"])
        current_resolution = default_resolutions[0]

# Function to create and show a notification window
def show_notification(message):
    global notification_thread

    try:
        # Create a new notification window with a unique class name
        notification_thread = threading.Thread(target=_show_notification_window, args=(message,))
        notification_thread.start()

    except Exception as e:
        print(f"An error occurred while showing notification: {e}")

def _show_notification_window(message):
    try:
        # Generate a unique class name based on current timestamp
        class_name = f"NotificationWindowClass_{int(time.time()*1000)}"

        # Calculate screen dimensions
        screen_width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
        screen_height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)

        # Define notification window size and position
        notification_width = 300
        notification_height = 100
        notification_x = screen_width - notification_width - 20  # Adjust as needed
        notification_y = 20  # Top-right corner, 20 pixels from the top

        # Create a top-level window class
        wc = win32gui.WNDCLASS()
        wc.lpfnWndProc = _WndProc
        wc.lpszClassName = class_name
        wc.hInstance = win32api.GetModuleHandle(None)
        wc.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
        wc.hbrBackground = win32gui.GetStockObject(win32con.WHITE_BRUSH)
        wc.style = win32con.CS_HREDRAW | win32con.CS_VREDRAW

        # Register the window class
        win32gui.RegisterClass(wc)

        # Create the window
        global notification_window_handle
        notification_window_handle = win32gui.CreateWindowEx(
            0,                               # Extended window style
            wc.lpszClassName,                # Window class name
            "Notification",                  # Window title
            win32con.WS_POPUP,               # Window style - no minimize or close buttons
            notification_x,                  # X position
            notification_y,                  # Y position
            notification_width,              # Width
            notification_height,             # Height
            0,                               # Parent window handle
            0,                               # Menu handle
            wc.hInstance,                    # Application instance handle
            None                             # Window creation data
        )

        # Show the window
        win32gui.ShowWindow(notification_window_handle, win32con.SW_SHOWNORMAL)
        win32gui.UpdateWindow(notification_window_handle)

        # Display the message with transparent background
        hdc = win32gui.GetDC(notification_window_handle)
        win32gui.SetBkMode(hdc, win32con.TRANSPARENT)  # Set transparent text background

        # Draw centered text
        rect = (0, 0, notification_width, notification_height)
        win32gui.DrawText(hdc, message, -1, rect, win32con.DT_CENTER | win32con.DT_VCENTER | win32con.DT_SINGLELINE)

        # Release the device context
        win32gui.ReleaseDC(notification_window_handle, hdc)

        # Wait for a second
        time.sleep(1)

        # Destroy the window
        win32gui.DestroyWindow(notification_window_handle)
        win32gui.UnregisterClass(wc.lpszClassName, wc.hInstance)

    except Exception as e:
        print(f"An error occurred in _show_notification_window: {e}")

# Window procedure for the custom notification window
def _WndProc(hwnd, msg, wParam, lParam):
    if msg == win32con.WM_CLOSE:
        win32gui.DestroyWindow(hwnd)
        return 0
    elif msg == win32con.WM_DESTROY:
        win32gui.PostQuitMessage(0)
        return 0
    else:
        return win32gui.DefWindowProc(hwnd, msg, wParam, lParam)

# Function to handle hotkey press
def on_hotkey(event):
    if event.event_type == keyboard.KEY_DOWN:
        if event.name == resolution_switch_keybind.split('+')[-1] and all(keyboard.is_pressed(modifier) for modifier in resolution_switch_keybind.split('+')[:-1]):
            toggle_resolution()

# Register hotkey
keyboard.on_press_key(resolution_switch_keybind.split('+')[-1], on_hotkey)

# Function to create the system tray icon
def create_icon_with_h():
    img = Image.new('RGB', (16, 16), color="white")
    d = ImageDraw.Draw(img)
    d.rectangle([(1, 1), (15, 15)], outline="black")  # Black border
    font = ImageFont.truetype("arial.ttf", 10)  # Load a font of your choice
    d.text((4, 3), "H", font=font, fill="black")  # Draw "H" in the middle
    return img

# Create a menu for the system tray icon
menu = Menu(MenuItem("Exit", lambda: os._exit(0)))

# Create an icon
icon = Icon("HotKeyRes", create_icon_with_h(), menu=menu, title="HotKeyRes")

# Run the icon
icon.run()
