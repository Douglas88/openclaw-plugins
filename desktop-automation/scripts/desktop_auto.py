#!/usr/bin/env python3
"""
OpenClaw Desktop Automation — Cross-platform GUI control
============================================================================
Unified abstraction over OS-specific desktop automation tools.

macOS:   osascript (AppleScript) + screencapture + cliclick
Windows: PowerShell UIAutomation + .NET Windows.Forms
Linux:   xdotool + wmctrl + import (ImageMagick) + xclip

Usage:
  python3 desktop_auto.py click 100 200
  python3 desktop_auto.py type "Hello World"
  python3 desktop_auto.py screenshot /tmp/screen.png
  python3 desktop_auto.py find "Firefox"
  python3 desktop_auto.py key enter
  python3 desktop_auto.py move 500 300
  python3 desktop_auto.py scroll 3
  python3 desktop_auto.py info
  python3 desktop_auto.py clipboard --get
  python3 desktop_auto.py clipboard --set "text"
"""

import argparse
import os
import platform
import subprocess
import sys
import time
import json

OS = platform.system()  # Darwin | Windows | Linux


# ══════════════════════════════════════════════════════════
# macOS (Darwin) — AppleScript + screencapture
# ══════════════════════════════════════════════════════════

def _macos_applescript(script: str) -> str:
    p = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=10)
    return p.stdout.strip()

def macos_click(x: int, y: int):
    """Click at coordinates using cliclick or AppleScript."""
    if _has("cliclick"):
        _run(["cliclick", f"c:{x},{y}"])
    else:
        _macos_applescript(f'''
            tell application "System Events"
                click at {{{x}, {y}}}
            end tell
        ''')

def macos_type(text: str):
    _macos_applescript(f'tell application "System Events" to keystroke "{text}"')

def macos_key(key: str):
    _macos_applescript(f'tell application "System Events" to key code {_keycode_mac(key)}')

def macos_move(x: int, y: int):
    if _has("cliclick"):
        _run(["cliclick", f"m:{x},{y}"])
    else:
        import Quartz  # pyobjc-framework-Quartz
        Quartz.CGEventPost(Quartz.kCGHIDEventTap,
            Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventMouseMoved, (x, y), 0))

def macos_screenshot(path: str):
    _run(["screencapture", "-x", path])

def macos_find_window(name: str) -> list:
    script = f'''
        tell application "System Events"
            set wList to every window of (every process whose visible is true)
            set out to ""
            repeat with w in wList
                set wName to name of w
                if wName contains "{name}" then
                    set wPos to position of w
                    set wSize to size of w
                    set out to out & wName & "|" & item 1 of wPos & "," & item 2 of wPos & "|" & item 1 of wSize & "," & item 2 of wSize & "||"
                end if
            end repeat
            return out
        end tell
    '''
    result = _macos_applescript(script)
    windows = []
    for entry in result.split("||"):
        if not entry.strip(): continue
        parts = entry.split("|")
        if len(parts) >= 2:
            windows.append({"name": parts[0], "position": parts[1], "size": parts[2] if len(parts) > 2 else ""})
    return windows

def macos_info() -> dict:
    return {
        "os": "macOS",
        "tools": {
            "cliclick": _has("cliclick"),
            "screencapture": _has("screencapture"),
            "osascript": _has("osascript")
        },
        "display": _get_display_size_mac()
    }

def _get_display_size_mac() -> str:
    try:
        out = _run_cap(["system_profiler", "SPDisplaysDataType"])
        for line in out.split("\n"):
            if "Resolution:" in line:
                return line.split(":")[1].strip()
    except: pass
    return "unknown"

def _keycode_mac(key: str) -> str:
    codes = {"enter": "36", "space": "49", "tab": "48", "escape": "53",
             "left": "123", "right": "124", "up": "126", "down": "125",
             "delete": "51", "home": "115", "end": "119"}
    return codes.get(key.lower(), key)


# ══════════════════════════════════════════════════════════
# Linux (Ubuntu) — xdotool + import + wmctrl
# ══════════════════════════════════════════════════════════

def linux_click(x: int, y: int):
    _run(["xdotool", "mousemove", str(x), str(y), "click", "1"])

def linux_type(text: str):
    _run(["xdotool", "type", "--delay", "50", text])

def linux_key(key: str):
    _run(["xdotool", "key", key])

def linux_move(x: int, y: int):
    _run(["xdotool", "mousemove", str(x), str(y)])

def linux_screenshot(path: str):
    _run(["import", "-window", "root", path])  # ImageMagick

def linux_find_window(name: str) -> list:
    try:
        out = _run_cap(["wmctrl", "-l"])
        windows = []
        for line in out.split("\n"):
            if name.lower() in line.lower():
                parts = line.split(None, 3)
                if len(parts) >= 2:
                    windows.append({"id": parts[0], "desktop": parts[1], "name": parts[3] if len(parts) > 3 else ""})
        return windows
    except: return []

def linux_scroll(clicks: int):
    btn = "4" if clicks > 0 else "5"
    for _ in range(abs(clicks)):
        _run(["xdotool", "click", btn])

def linux_info() -> dict:
    return {
        "os": "Linux",
        "tools": {
            "xdotool": _has("xdotool"),
            "wmctrl": _has("wmctrl"),
            "import": _has("import") or _has("scrot")
        },
        "display": os.environ.get("DISPLAY", "not set")
    }


# ══════════════════════════════════════════════════════════
# Windows — PowerShell UIAutomation
# ══════════════════════════════════════════════════════════

def windows_click(x: int, y: int):
    ps = f'''
        Add-Type -AssemblyName System.Windows.Forms
        [System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point({x},{y})
        Add-Type -MemberDefinition '[DllImport("user32.dll")] public static extern void mouse_event(int dwFlags, int dx, int dy, int dwData, int dwExtraInfo);' -Name Win32 -Namespace System
        [System.Win32]::mouse_event(0x0002,0,0,0,0)
        Start-Sleep -Milliseconds 50
        [System.Win32]::mouse_event(0x0004,0,0,0,0)
    '''
    _run(["powershell", "-Command", ps])

def windows_type(text: str):
    ps = f'''
        Add-Type -AssemblyName System.Windows.Forms
        [System.Windows.Forms.SendKeys]::SendWait("{text}")
    '''
    _run(["powershell", "-Command", ps])

def windows_key(key: str):
    mapping = {"enter": "{ENTER}", "tab": "{TAB}", "space": " ", "escape": "{ESC}",
               "left": "{LEFT}", "right": "{RIGHT}", "up": "{UP}", "down": "{DOWN}"}
    k = mapping.get(key.lower(), key)
    windows_type(k)

def windows_screenshot(path: str):
    ps = f'''
        Add-Type -AssemblyName System.Windows.Forms
        $b = New-Object System.Drawing.Bitmap([System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Width, [System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Height)
        $g = [System.Drawing.Graphics]::FromImage($b)
        $g.CopyFromScreen(0,0,0,0,$b.Size)
        $b.Save("{path}")
        $g.Dispose(); $b.Dispose()
    '''
    _run(["powershell", "-Command", ps])

def windows_find_window(name: str) -> list:
    ps = f'Get-Process | Where-Object {{ $_.MainWindowTitle -like "*{name}*" }} | Select-Object Id, MainWindowTitle | ConvertTo-Json'
    try:
        out = _run_cap(["powershell", "-Command", ps])
        procs = json.loads(out)
        if isinstance(procs, dict): procs = [procs]
        return [{"pid": p.get("Id"), "title": p.get("MainWindowTitle")} for p in procs]
    except: return []

def windows_info() -> dict:
    return {
        "os": "Windows",
        "tools": {"powershell": _has("powershell")},
        "display": "primary"
    }


# ══════════════════════════════════════════════════════════
# Clipboard
# ══════════════════════════════════════════════════════════

def clipboard_get() -> str:
    if OS == "Darwin":
        return _run_cap(["pbpaste"])
    elif OS == "Windows":
        return _run_cap(["powershell", "-Command", "Get-Clipboard"])
    else:
        return _run_cap(["xclip", "-selection", "clipboard", "-o"])

def clipboard_set(text: str):
    if OS == "Darwin":
        _run(["pbcopy"], input=text)
    elif OS == "Windows":
        _run(["powershell", "-Command", f"Set-Clipboard -Value '{text}'"])
    else:
        _run(["xclip", "-selection", "clipboard"], input=text)


# ══════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════

def _has(cmd: str) -> bool:
    return subprocess.run(["which", cmd] if OS != "Windows" else ["where", cmd],
                         capture_output=True).returncode == 0

def _run(cmd: list, input: str = None, timeout: int = 15):
    p = subprocess.run(cmd, input=input, capture_output=True, text=True, timeout=timeout)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.strip() or f"Command failed: {' '.join(cmd)}")

def _run_cap(cmd: list) -> str:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=10).stdout.strip()


# ══════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════

COMMANDS = {
    "Darwin":  {"click": macos_click, "type": macos_type, "key": macos_key,
                "move": macos_move, "screenshot": macos_screenshot,
                "find": macos_find_window, "info": macos_info},
    "Linux":   {"click": linux_click, "type": linux_type, "key": linux_key,
                "move": linux_move, "screenshot": linux_screenshot,
                "find": linux_find_window, "info": linux_info, "scroll": linux_scroll},
    "Windows": {"click": windows_click, "type": windows_type, "key": windows_key,
                "screenshot": windows_screenshot, "find": windows_find_window, "info": windows_info},
}

def main():
    parser = argparse.ArgumentParser(description="OpenClaw Desktop Automation")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("info")
    sp = sub.add_parser("click"); sp.add_argument("x", type=int); sp.add_argument("y", type=int)
    sp = sub.add_parser("type"); sp.add_argument("text")
    sp = sub.add_parser("key"); sp.add_argument("key_name")
    sp = sub.add_parser("move"); sp.add_argument("x", type=int); sp.add_argument("y", type=int)
    sp = sub.add_parser("screenshot"); sp.add_argument("path")
    sp = sub.add_parser("find"); sp.add_argument("name")
    sp = sub.add_parser("scroll"); sp.add_argument("clicks", type=int)

    cb = sub.add_parser("clipboard")
    cb_sub = cb.add_subparsers(dest="cb_cmd")
    cb_sub.add_parser("--get")
    sp2 = cb_sub.add_parser("--set"); sp2.add_argument("text")

    args = parser.parse_args()

    if args.cmd == "clipboard":
        if args.cb_cmd == "--get":
            print(clipboard_get())
        elif args.cb_cmd == "--set":
            clipboard_set(args.text)
            print("✅ clipboard set")
        return

    cmds = COMMANDS.get(OS, {})
    func = cmds.get(args.cmd)
    if not func:
        print(f"Command '{args.cmd}' not supported on {OS}")
        sys.exit(1)

    if args.cmd == "info":
        print(json.dumps(func(), indent=2))
    elif args.cmd == "click":
        func(args.x, args.y); print(f"✅ clicked ({args.x},{args.y})")
    elif args.cmd == "type":
        func(args.text); print(f"✅ typed")
    elif args.cmd == "key":
        func(args.key_name); print(f"✅ key {args.key_name}")
    elif args.cmd == "move":
        func(args.x, args.y); print(f"✅ moved to ({args.x},{args.y})")
    elif args.cmd == "screenshot":
        func(args.path); print(f"✅ screenshot saved to {args.path}")
    elif args.cmd == "find":
        result = func(args.name)
        print(json.dumps(result, indent=2))
    elif args.cmd == "scroll":
        func(args.clicks); print(f"✅ scrolled {args.clicks}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
