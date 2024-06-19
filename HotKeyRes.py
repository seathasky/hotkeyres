import keyboard
import win32api
import win32con
import win32gui
import winreg
import json
import os
import sys
import time
import threading
from pystray import Icon, MenuItem, Menu
from PIL import Image, ImageDraw, ImageWin

# Constants
CONFIG_FILE = 'config.json'
current_resolution_index = 0
notification_thread = None
notification_window_handle = None
notification_lock = threading.Lock()
APP_NAME = "HotKeyRes"
STARTUP_KEY = r'Software\Microsoft\Windows\CurrentVersion\Run'
EXECUTABLE_NAME = 'HotKeyRes.exe'

# Function to create a default config file
def create_default_config():
    default_config = {
        "resolution_switch_keybind": "ctrl+f4",
        "default_resolutions": [
            {"name": "Resolution 1", "width": 1920, "height": 1080, "refresh_rate": 60},
            {"name": "Resolution 2", "width": 1280, "height": 720, "refresh_rate": 60}
        ],
        "start_at_login": False,
        "notification_duration": 2,
        "notification_position": "top"
    }
    with open(CONFIG_FILE, 'w') as f:
        json.dump(default_config, f, indent=4)

# Function to load the config file
def load_config():
    if not os.path.exists(CONFIG_FILE):
        create_default_config()
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)

    # Ensure all necessary keys are present
    if "resolution_switch_keybind" not in config:
        config["resolution_switch_keybind"] = "ctrl+f4"
    if "default_resolutions" not in config:
        config["default_resolutions"] = [
            {"name": "Resolution 1", "width": 1920, "height": 1080, "refresh_rate": 60},
            {"name": "Resolution 2", "width": 1280, "height": 720, "refresh_rate": 60}
        ]
    if "start_at_login" not in config:
        config["start_at_login"] = False
    if "notification_duration" not in config:
        config["notification_duration"] = 2
    if "notification_position" not in config:
        config["notification_position"] = "top"
    
    return config

# Function to save the config file
def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

# Load the config file
config = load_config()
resolution_switch_keybind = config["resolution_switch_keybind"]
default_resolutions = config["default_resolutions"]
start_at_login = config["start_at_login"]
notification_duration = config["notification_duration"]
notification_position = config["notification_position"]

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
            show_resolution_notification(f"Failed to change resolution. Error code: {result}")
        else:
            print(f"Resolution set to {height}p at {refresh_rate}Hz")
            show_resolution_notification(f"Resolution changed to {height}p at {refresh_rate}Hz")

    except Exception as e:
        print(f"An error occurred while setting resolution: {e}")
        show_resolution_notification(f"Error: {e}")

# Function to toggle resolution
def toggle_resolution():
    global current_resolution_index
    resolutions = config["default_resolutions"]
    current_resolution_index = (current_resolution_index + 1) % len(resolutions)
    res = resolutions[current_resolution_index]
    set_resolution(res["width"], res["height"], res["refresh_rate"])

# Function to create and show a startup notification window with an image
def show_startup_notification():
    global notification_thread

    try:
        notification_thread = threading.Thread(target=_show_startup_notification_window)
        notification_thread.start()

    except Exception as e:
        print(f"An error occurred while showing startup notification: {e}")

def _show_startup_notification_window():
    try:
        class_name = f"NotificationWindowClass_{int(time.time()*2000)}"

        screen_width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
        screen_height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)

        notification_width = 400  # width of the image
        notification_height = 150  # height of the image

        notification_x = (screen_width - notification_width) // 2
        notification_y = (screen_height - notification_height) // 2

        wc = win32gui.WNDCLASS()
        wc.lpfnWndProc = _WndProc
        wc.lpszClassName = class_name
        wc.hInstance = win32api.GetModuleHandle(None)
        wc.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
        wc.hbrBackground = win32gui.GetStockObject(win32con.WHITE_BRUSH)
        wc.style = win32con.CS_HREDRAW | win32con.CS_VREDRAW

        win32gui.RegisterClass(wc)

        global notification_window_handle
        notification_window_handle = win32gui.CreateWindowEx(
            win32con.WS_EX_TOPMOST,
            wc.lpszClassName,
            "Notification",
            win32con.WS_POPUP,
            notification_x,
            notification_y,
            notification_width,
            notification_height,
            0,
            0,
            wc.hInstance,
            None
        )

        win32gui.ShowWindow(notification_window_handle, win32con.SW_SHOWNORMAL)
        win32gui.UpdateWindow(notification_window_handle)

        # Load the image
        image_path = "resources/MainNotif.png"  # replace with the path to your image
        image = Image.open(image_path)
        image = image.resize((notification_width, notification_height), Image.LANCZOS)  # resize image as needed

        # Convert PIL image to a format suitable for Windows
        hdc = win32gui.GetDC(notification_window_handle)
        hbmp = ImageWin.Dib(image)
        hbmp.draw(hdc, (0, 0, notification_width, notification_height))  # draw image at full window size

        win32gui.ReleaseDC(notification_window_handle, hdc)

        time.sleep(notification_duration)

        win32gui.DestroyWindow(notification_window_handle)
        win32gui.UnregisterClass(wc.lpszClassName, wc.hInstance)

    except Exception as e:
        print(f"An error occurred in _show_startup_notification_window: {e}")

# Function to create and show a resolution change notification window with text
def show_resolution_notification(message):
    global notification_thread

    try:
        notification_thread = threading.Thread(target=_show_resolution_notification_window, args=(message,))
        notification_thread.start()

    except Exception as e:
        print(f"An error occurred while showing resolution notification: {e}")

def _show_resolution_notification_window(message):
    try:
        class_name = f"NotificationWindowClass_{int(time.time()*2000)}"

        screen_width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
        screen_height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)

        notification_width = 400
        notification_height = 100

        notification_x = (screen_width - notification_width) // 2
        notification_y = 20

        wc = win32gui.WNDCLASS()
        wc.lpfnWndProc = _WndProc
        wc.lpszClassName = class_name
        wc.hInstance = win32api.GetModuleHandle(None)
        wc.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
        wc.hbrBackground = win32gui.GetStockObject(win32con.WHITE_BRUSH)
        wc.style = win32con.CS_HREDRAW | win32con.CS_VREDRAW

        win32gui.RegisterClass(wc)

        global notification_window_handle
        notification_window_handle = win32gui.CreateWindowEx(
            win32con.WS_EX_TOPMOST,
            wc.lpszClassName,
            "Notification",
            win32con.WS_POPUP,
            notification_x,
            notification_y,
            notification_width,
            notification_height,
            0,
            0,
            wc.hInstance,
            None
        )

        win32gui.ShowWindow(notification_window_handle, win32con.SW_SHOWNORMAL)
        win32gui.UpdateWindow(notification_window_handle)

        hdc = win32gui.GetDC(notification_window_handle)
        win32gui.SetBkMode(hdc, win32con.TRANSPARENT)

        rect = (0, 0, notification_width, notification_height)

        # Draw black border
        win32gui.FrameRect(hdc, rect, win32gui.CreateSolidBrush(win32api.RGB(0, 0, 0)))

        # Draw text
        win32gui.DrawText(hdc, message, -1, rect, win32con.DT_CENTER | win32con.DT_VCENTER | win32con.DT_SINGLELINE)

        win32gui.ReleaseDC(notification_window_handle, hdc)

        time.sleep(notification_duration)

        win32gui.DestroyWindow(notification_window_handle)
        win32gui.UnregisterClass(wc.lpszClassName, wc.hInstance)

    except Exception as e:
        print(f"An error occurred in _show_resolution_notification_window: {e}")

def _WndProc(hwnd, msg, wParam, lParam):
    if msg == win32con.WM_CLOSE:
        win32gui.DestroyWindow(hwnd)
        return 0
    elif msg == win32con.WM_DESTROY:
        win32gui.PostQuitMessage(0)
        return 0
    else:
        return win32gui.DefWindowProc(hwnd, msg, wParam, lParam)

def on_hotkey(event):
    if event.event_type == keyboard.KEY_DOWN:
        if event.name == resolution_switch_keybind.split('+')[-1] and all(keyboard.is_pressed(modifier) for modifier in resolution_switch_keybind.split('+')[:-1]):
            toggle_resolution()

keyboard.on_press_key(resolution_switch_keybind.split('+')[-1], on_hotkey)

def create_icon_with_h():
    # Get the directory of the current script or executable
    if getattr(sys, 'frozen', False):
        dir_path = os.path.dirname(sys.executable)
    else:
        dir_path = os.path.dirname(os.path.abspath(__file__))
    # Load the icon from the correct directory
    return Image.open(os.path.join(dir_path, "resources/icon.ico"))

# Function to handle click event
def on_icon_click(icon, item):
    toggle_resolution()

# Function to add application to startup
def add_to_startup():
    if getattr(sys, 'frozen', False):
        exe_path = os.path.join(os.path.dirname(sys.executable), EXECUTABLE_NAME)
    else:
        exe_path = os.path.abspath(__file__).replace('.py', '.exe')
    
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, STARTUP_KEY, 0, winreg.KEY_SET_VALUE)
    winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, exe_path)
    winreg.CloseKey(key)
    config["start_at_login"] = True
    save_config(config)

# Function to remove application from startup
def remove_from_startup():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, STARTUP_KEY, 0, winreg.KEY_SET_VALUE)
        winreg.DeleteValue(key, APP_NAME)
        winreg.CloseKey(key)
    except FileNotFoundError:
        pass
    config["start_at_login"] = False
    save_config(config)

# Function to handle the toggle start at login menu item
def toggle_start_at_login(icon, item):
    if config["start_at_login"]:
        remove_from_startup()
    else:
        add_to_startup()
    update_menu(icon)

# Function to update the system tray menu dynamically
def update_menu(icon):
    icon.menu = Menu(
        MenuItem("Toggle Resolution", on_icon_click),
        MenuItem(
            "Start at Windows Login",
            toggle_start_at_login,
            checked=lambda item: config["start_at_login"]
        ),
        MenuItem("Exit", lambda: os._exit(0))
    )

# Menu for system tray icon
menu = Menu(
    MenuItem("Toggle Resolution", on_icon_click),
    MenuItem(
        "Start at Windows Login",
        toggle_start_at_login,
        checked=lambda item: config["start_at_login"]
    ),
    MenuItem("Exit", lambda: os._exit(0))
)

# Create an icon
icon = Icon("HotKeyRes", create_icon_with_h(), menu=menu, title="HotKeyRes options")

# Set up the icon click event by overriding the run method
def setup(icon):
    icon.visible = True
    if start_at_login:
        add_to_startup()
    show_startup_notification()

# Run the icon
icon.run(setup)
