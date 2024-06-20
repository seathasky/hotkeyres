![image](https://raw.githubusercontent.com/seathasky/hotkeyres/main/resources/MainNotif.png)<br>
[Download latest release](https://github.com/seathasky/hotkeyres/releases)<br><Br>

<b>Setup:</b><br>
Extract "HotKeyRes" folder wherever you want. Run HotKeyRes.exe.<br>
Default Keybind is CONTROL+F4 or right click system tray icon for options.<br>
Change resolutions/refresh and keybind in config.json<br><br><br>

<b>Features:</b><br>
notifications on res switch:<br><br>
![image](https://raw.githubusercontent.com/seathasky/hotkeyres/main/github/notifcations.png)

system tray icon:<br><br>
![image](https://raw.githubusercontent.com/seathasky/hotkeyres/main/github/systemtray1.png)
<br>

# build w/ python

```pip install pyautogui keyboard pywin32 pystray```

```pyinstaller --onefile --noconsole --icon="C:\Users\USERNAMEHERE\Downloads\hotkeyres-main\icon.ico" "C:\Users\USERNAMEHERE\Downloads\hotkeyres-main\HotKeyRes.py" ```

# planned features/bug fix:
<ul>
  <li>fix duplicate .exe on multiple click</li>
  <li><del>notification at .exe launch</del></li>
<li><del>add start at login feature</del></li>
 <li><del>better sys tray icon</del></li>
 <li><del>sys tray tooltip</del></li>
 </ul> 

---

Shield: [![CC BY 4.0][cc-by-shield]][cc-by]

This work is licensed under a
[Creative Commons Attribution 4.0 International License][cc-by].

[![CC BY 4.0][cc-by-image]][cc-by]

[cc-by]: http://creativecommons.org/licenses/by/4.0/
[cc-by-image]: https://i.creativecommons.org/l/by/4.0/88x31.png
[cc-by-shield]: https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg

