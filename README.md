# HotKeyRes
[Download latest release](https://github.com/seathasky/hotkeyres/releases)<br><Br>
Extract HotKeyRes folder wherever you want. Run HotKeyRes.exe.<br>
Default Keybind is CONTROL+F4 or right click system tray icon to toggle resolution.<br>
Change resolutions/refresh and keybind in config.json<br><br>
notifications on res switch:<br><br>
![image](https://raw.githubusercontent.com/seathasky/hotkeyres/main/notifcations.png)

system tray image:<br><br>
![image](https://raw.githubusercontent.com/seathasky/hotkeyres/main/systemtray1.png)
<br>

# build w/ python

```pip install pyautogui keyboard pywin32 pystray```

```pyinstaller --onefile --noconsole --icon="C:\Users\USERNAMEHERE\Downloads\hotkeyres-main\icon.ico" "C:\Users\USERNAMEHERE\Downloads\hotkeyres-main\HotKeyRes.py" ```

# planned features/bug fix:
<ul>
  <li>duplicate .exe on multiple click</li>
 <li><del>better sys tray icon</del></li>
 <li><del>sys tray tooltip</del></li>
 </ul> 



