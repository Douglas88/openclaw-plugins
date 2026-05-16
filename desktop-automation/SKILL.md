---
name: desktop-automation
description: Cross-platform GUI automation — control mouse, keyboard, windows, and screenshots on macOS, Windows, and Ubuntu. Use when: (1) automating desktop interactions, (2) clicking/typing in GUI apps, (3) taking screenshots, (4) finding and focusing windows, (5) clipboard operations, (6) macro-like desktop workflows. Uses AppleScript (macOS), xdotool/wmctrl (Linux), PowerShell UIA (Windows) via unified scripts/desktop_auto.py.
version: "1.0.0"
---

# Desktop Automation Skill

Cross-platform GUI control — mouse, keyboard, windows, screenshots, clipboard.

## Quick Start

```bash
python3 scripts/desktop_auto.py info            # Check platform & available tools
python3 scripts/desktop_auto.py click 500 300   # Click at coordinates
python3 scripts/desktop_auto.py type "Hello"    # Type text at cursor
python3 scripts/desktop_auto.py key enter        # Press a key
python3 scripts/desktop_auto.py screenshot /tmp/cap.png  # Screenshot
python3 scripts/desktop_auto.py find "Chrome"   # Find window by name
python3 scripts/desktop_auto.py clipboard --get # Read clipboard
```

## Supported Operations

| Command | macOS | Windows | Linux |
|---------|-------|---------|-------|
| `click X Y` | AppleScript / cliclick | PowerShell UIA | xdotool |
| `type "text"` | AppleScript keystroke | SendKeys | xdotool type |
| `key enter` | AppleScript key code | SendKeys | xdotool key |
| `move X Y` | cliclick / Quartz | PowerShell | xdotool |
| `screenshot path` | screencapture | .NET Graphics | import (ImageMagick) |
| `find "name"` | System Events | Get-Process | wmctrl |
| `scroll N` | — | — | xdotool |
| `clipboard --get` | pbpaste | Get-Clipboard | xclip |
| `clipboard --set "x"` | pbcopy | Set-Clipboard | xclip |
| `info` | ✅ | ✅ | ✅ |

## Prerequisites

| Platform | Required Tools | Install |
|----------|---------------|---------|
| **macOS** | Built-in (osascript) | None required; cliclick optional |
| **Windows** | Built-in (PowerShell) | None required |
| **Linux** | xdotool, wmctrl, ImageMagick | `sudo apt install xdotool wmctrl imagemagick xclip` |

## Workflows

### 1. Screenshot + Analyze
```bash
python3 scripts/desktop_auto.py screenshot /tmp/screen.png
# Then use the file with OpenClaw's read tool for analysis
```

### 2. Automated Form Filling
```bash
python3 scripts/desktop_auto.py find "Login"
python3 scripts/desktop_auto.py click 400 300   # username field
python3 scripts/desktop_auto.py type "user@email.com"
python3 scripts/desktop_auto.py key tab
python3 scripts/desktop_auto.py type "password123"
python3 scripts/desktop_auto.py key enter
```

### 3. Window Management
```bash
python3 scripts/desktop_auto.py find "Terminal"  # Find all terminal windows
# Use returned window IDs with platform-specific tools for focus/resize
```

### 4. Macro Recording Helper
```bash
# Get current mouse position (Linux)
xdotool getmouselocation
# Click + type + screenshot — all from one tool
```

## Platform Notes

See `references/platform_notes.md` for per-platform details, key mappings, and troubleshooting.
