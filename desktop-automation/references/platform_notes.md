# Platform-Specific Desktop Automation Notes

## macOS

**Built-in (no install needed):**
- `osascript` — AppleScript/JavaScript for GUI control
- `screencapture` — Screenshot utility
- `pbpaste` / `pbcopy` — Clipboard

**Optional (enhanced):**
- `cliclick` — Faster, more reliable mouse ops: `brew install cliclick`

**Key codes** (for `key` command):
```
enter=36, space=49, tab=48, escape=53
left=123, right=124, up=126, down=125
delete=51, home=115, end=119
```

**Permissions:** Enable Accessibility access in System Preferences → Security → Privacy → Accessibility for the terminal app.

## Windows

**Built-in (no install needed):**
- PowerShell with System.Windows.Forms
- user32.dll mouse_event

**Optional:**
- `pywinauto` — Python GUI automation library
- `AutoIt` — Windows automation tool

**Key mapping:** enter={ENTER}, tab={TAB}, escape={ESC}, left={LEFT}, right={RIGHT}, up={UP}, down={DOWN}

## Linux (Ubuntu/Debian)

**Required:**
```bash
sudo apt install xdotool wmctrl imagemagick xclip
```

**Display:** Must have `$DISPLAY` set. For headless servers, use Xvfb:
```bash
sudo apt install xvfb
Xvfb :99 -screen 0 1920x1080x24 &
export DISPLAY=:99
```

**Mouse position:**
```bash
xdotool getmouselocation  # Get current position
xdotool mousemove_relative -- 10 0  # Move right 10px
```

**Window operations:**
```bash
wmctrl -l                      # List all windows
wmctrl -a "Firefox"            # Focus window
wmctrl -r "Firefox" -e 0,0,0,800,600  # Resize/move
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| "DISPLAY not set" (Linux) | `export DISPLAY=:0` or start Xvfb |
| Permission denied (macOS) | Enable Accessibility in System Preferences |
| click doesn't work (Windows) | Run PowerShell as Administrator |
| xdotool not found (Linux) | `sudo apt install xdotool` |
