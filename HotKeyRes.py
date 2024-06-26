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
import win32event
import winerror
from pystray import Icon, MenuItem, Menu
from PIL import Image, ImageDraw, ImageWin

# Constants
BASE_DIR = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))
CONFIG_FILE = os.path.join(BASE_DIR, 'config.json')
ICON_FILE = os.path.join(BASE_DIR, "resources", "icon.ico")
IMAGE_FILE = os.path.join(BASE_DIR, "resources", "MainNotif.png")
LOG_FILE = os.path.join(BASE_DIR, 'error.log')
current_resolution_index = 0
notification_thread = None
notification_window_handle = None
notification_lock = threading.Lock()
APP_NAME = "HotKeyRes"
STARTUP_KEY = r'Software\Microsoft\Windows\CurrentVersion\Run'
EXECUTABLE_NAME = 'HotKeyRes.exe'
MUTEX_NAME = 'HotKeyRes_Mutex'
BUILD_VERSION = "2.1"  # Define your build version here

# Default configuration
DEFAULT_CONFIG = {
    "resolution_switch_keybind": "ctrl+f4",
    "default_resolutions": [
        {"name": "Resolution 1", "width": 1920, "height": 1080, "refresh_rate": 60},
        {"name": "Resolution 2", "width": 1280, "height": 720, "refresh_rate": 60}
    ],
    "start_at_login": False,
    "notification_duration": 2,
    "notification_position": "top",
    "hide_startup_splash": False
}

# Function to log errors
def log_error(message):
    with open(LOG_FILE, 'a') as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

# Function to create a default config file
def create_default_config():
    print("Creating default config file.")
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(DEFAULT_CONFIG, f, indent=4)
        print("Default config file created.")
    except Exception as e:
        log_error(f"Error creating default config file: {e}")

# Function to load the config file
def load_config():
    if not os.path.exists(CONFIG_FILE):
        create_default_config()

    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        print("Config file loaded.")
    except Exception as e:
        log_error(f"Error loading config file: {e}")
        create_default_config()
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)

    # Ensure all necessary keys are present
    for key, value in DEFAULT_CONFIG.items():
        config.setdefault(key, value)

    return config

# Function to save the config file
def save_config(config):
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        print("Config file saved.")
    except Exception as e:
        log_error(f"Error saving config file: {e}")

# Load the config file
config = load_config()
resolution_switch_keybind = config["resolution_switch_keybind"]
default_resolutions = config["default_resolutions"]
start_at_login = config["start_at_login"]
notification_duration = config["notification_duration"]
notification_position = config["notification_position"]
hide_startup_splash = config["hide_startup_splash"]

# Function to set resolution
def set_resolution(width, height, refresh_rate, resolution_name):
    try:
        devmode = win32api.EnumDisplaySettings(None, 0)
        devmode.PelsWidth = width
        devmode.PelsHeight = height
        devmode.DisplayFrequency = refresh_rate
        devmode.Fields = win32con.DM_PELSWIDTH | win32con.DM_PELSHEIGHT | win32con.DM_DISPLAYFREQUENCY

        result = win32api.ChangeDisplaySettings(devmode, 0)
        if result == win32con.DISP_CHANGE_SUCCESSFUL:
            message = f"Resolution changed to {height}p at {refresh_rate}Hz"
        else:
            message = f"Failed to change resolution. Error code: {result}"
        print(message)
        show_resolution_notification(message, resolution_name)

    except Exception as e:
        message = f"An error occurred while setting resolution: {e}"
        log_error(message)
        show_resolution_notification(message, resolution_name)

# Function to reload the configuration file
def reload_config():
    global config, resolution_switch_keybind, default_resolutions, start_at_login, notification_duration, notification_position, hide_startup_splash
    config = load_config()
    resolution_switch_keybind = config["resolution_switch_keybind"]
    default_resolutions = config["default_resolutions"]
    start_at_login = config["start_at_login"]
    notification_duration = config["notification_duration"]
    notification_position = config["notification_position"]
    hide_startup_splash = config["hide_startup_splash"]

# Function to toggle resolution
def toggle_resolution():
    global current_resolution_index
    reload_config()
    resolutions = config["default_resolutions"]
    current_resolution_index = (current_resolution_index + 1) % len(resolutions)
    res = resolutions[current_resolution_index]
    set_resolution(res["width"], res["height"], res["refresh_rate"], res["name"])

# Function to create and show a startup notification window with an image
def show_startup_notification():
    global notification_thread

    try:
        notification_thread = threading.Thread(target=_show_startup_notification_window)
        notification_thread.start()

    except Exception as e:
        log_error(f"An error occurred while showing startup notification: {e}")

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
        if not os.path.exists(IMAGE_FILE):
            print(f"Image not found: {IMAGE_FILE}")
            log_error(f"Image not found: {IMAGE_FILE}")
            return

        image = Image.open(IMAGE_FILE)
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
        log_error(f"An error occurred in _show_startup_notification_window: {e}")

# Function to create and show a resolution change notification window with text
def show_resolution_notification(message, resolution_name):
    global notification_thread

    try:
        notification_thread = threading.Thread(target=_show_resolution_notification_window, args=(message, resolution_name))
        notification_thread.start()

    except Exception as e:
        log_error(f"An error occurred while showing resolution notification: {e}")

def _show_resolution_notification_window(message, resolution_name):
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
        win32gui.DrawText(hdc, resolution_name, -1, rect, win32con.DT_CENTER | win32con.DT_TOP | win32con.DT_SINGLELINE)
        win32gui.DrawText(hdc, message, -1, rect, win32con.DT_CENTER | win32con.DT_VCENTER | win32con.DT_SINGLELINE)

        win32gui.ReleaseDC(notification_window_handle, hdc)

        time.sleep(notification_duration)

        win32gui.DestroyWindow(notification_window_handle)
        win32gui.UnregisterClass(wc.lpszClassName, wc.hInstance)

    except Exception as e:
        log_error(f"An error occurred in _show_resolution_notification_window: {e}")

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
    # Load the icon from the correct directory
    if not os.path.exists(ICON_FILE):
        print(f"Icon not found: {ICON_FILE}")
        log_error(f"Icon not found: {ICON_FILE}")
        return None
    return Image.open(ICON_FILE)

# Function to handle click event
def on_icon_click(icon, item):
    toggle_resolution()

# Function to add application to startup
def add_to_startup():
    if getattr(sys, 'frozen', False):
        exe_path = os.path.join(os.path.dirname(sys.executable), EXECUTABLE_NAME)
    else:
        exe_path = os.path.abspath(__file__).replace('.py', '.exe')
    
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, STARTUP_KEY, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, exe_path)
        config["start_at_login"] = True
        save_config(config)
        print("Added to startup.")
    except Exception as e:
        log_error(f"Error adding to startup: {e}")

# Function to remove application from startup
def remove_from_startup():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, STARTUP_KEY, 0, winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, APP_NAME)
    except FileNotFoundError:
        pass
    except Exception as e:
        log_error(f"Error removing from startup: {e}")
    config["start_at_login"] = False
    save_config(config)
    print("Removed from startup.")

# Function to handle the toggle start at login menu item
def toggle_start_at_login(icon, item):
    if config["start_at_login"]:
        remove_from_startup()
    else:
        add_to_startup()
    update_menu(icon)

# Function to handle the toggle hide startup splash menu item
def toggle_hide_startup_splash(icon, item):
    config["hide_startup_splash"] = not config["hide_startup_splash"]
    save_config(config)
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
        MenuItem(
            "Hide Startup Splash",
            toggle_hide_startup_splash,
            checked=lambda item: config["hide_startup_splash"]
        ),
        Menu.SEPARATOR,  # Add a separator above the build version
        MenuItem("Build Version: " + BUILD_VERSION, None, enabled=False),  # Add build version to the menu
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
    MenuItem(
        "Hide Startup Splash",
        toggle_hide_startup_splash,
        checked=lambda item: config["hide_startup_splash"]
    ),
    Menu.SEPARATOR,  # Add a separator above the build version
    MenuItem("Build Version: " + BUILD_VERSION, None, enabled=False),  # Add build version to the menu
    MenuItem("Exit", lambda: os._exit(0))
)

# Create an icon
icon_image = create_icon_with_h()
if not icon_image:
    print("Error: Icon not found. Exiting.")
    log_error("Error: Icon not found. Exiting.")
    sys.exit(1)
icon = Icon("HotKeyRes", icon_image, menu=menu, title="HotKeyRes options")

# Set up the icon click event by overriding the run method
def setup(icon):
    icon.visible = True
    if start_at_login:
        add_to_startup()
    if not hide_startup_splash:
        show_startup_notification()

# Function to show a notification if the program is already running
def show_already_running_notification():
    print("Program is already running.")
    show_resolution_notification("HotKeyRes is already running.", "Notification")

# Check for existing instances using a mutex
try:
    mutex = win32event.CreateMutex(None, True, MUTEX_NAME)
    if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
        show_already_running_notification()
        sys.exit(0)
except Exception as e:
    log_error(f"Error creating mutex: {e}")
    sys.exit(1)

# Run the icon
icon.run(setup)
