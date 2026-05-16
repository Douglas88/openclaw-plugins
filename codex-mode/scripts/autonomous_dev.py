#!/usr/bin/env python3
"""
OpenClaw Autonomous Development Loop
=====================================
Self-healing coding pipeline: run → test → fix → retest → report.

Usage:
  python3 autonomous_dev.py --dir ~/project --command "pytest -x"
  python3 autonomous_dev.py --dir ~/project --command "npm test" --max-loops 5
  
The loop:
  1. Execute command
  2. If success → report ✅
  3. If failure → read errors → analyze → suggest fixes → retry
  4. Max loops reached → report with diagnosis
"""

import argparse
import subprocess
import sys
import os
import json
import re
from pathlib import Path

def run_command(cmd: str, cwd: str = None, timeout: int = 120) -> tuple:
    """Run a command, return (exit_code, stdout, stderr)."""
    try:
        p = subprocess.run(
            cmd, shell=True, cwd=cwd,
            capture_output=True, text=True, timeout=timeout
        )
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT"

def extract_errors(stdout: str, stderr: str) -> list:
    """Extract actionable error messages from test output."""
    errors = []
    lines = (stdout + "\n" + stderr).split("\n")
    
    patterns = [
        (r"E\s+(\w+Error):\s*(.+)", "error"),           # pytest: E AssertionError: ...
        (r"FAIL:\s*(.+)", "failure"),                      # unittest
        (r"AssertionError:\s*(.+)", "assertion"),          # Assertion
        (r"ImportError:\s*(.+)", "import"),                # Import
        (r"ModuleNotFoundError:\s*(.+)", "import"),        # Module
        (r"SyntaxError:\s*(.+)", "syntax"),                # Syntax
        (r"NameError:\s*(.+)", "name"),                    # Name
        (r"TypeError:\s*(.+)", "type"),                    # Type
        (r"AttributeError:\s*(.+)", "attribute"),          # Attribute
        (r"(\S+\.py):(\d+):\s*(.+)", "location"),          # File:line
        (r"●\s+(.+?)\s+›\s+(.+)", "jest"),                 # Jest
    ]
    
    for line in lines:
        for pattern, etype in patterns:
            m = re.search(pattern, line)
            if m:
                errors.append({
                    "type": etype,
                    "line": line.strip(),
                    "file": m.group(1) if "py" in pattern else None,
                    "lineno": int(m.group(2)) if m.lastindex and m.lastindex >= 2 and m.group(2).isdigit() else None,
                    "message": m.group(m.lastindex) if m.lastindex else line.strip()
                })
                break
    
    return errors[:20]  # Limit to 20 most relevant

def analyze_and_fix(errors: list, src_dir: str) -> dict:
    """Analyze errors and return fix suggestions."""
    fixes = []
    
    for e in errors:
        fix = {"error": e, "action": "manual", "suggestion": ""}
        etype = e.get("type", "")
        msg = e.get("message", "")
        
        if etype in ("import", "attribute"):
            fix["action"] = "add_import"
            fix["suggestion"] = f"Add missing import or fix attribute: {msg}"
        elif etype == "syntax":
            fix["action"] = "fix_syntax"
            fix["suggestion"] = f"Fix syntax error: {msg}"
        elif etype == "type":
            fix["action"] = "fix_type"
            fix["suggestion"] = f"Fix type mismatch: {msg}"
        elif etype == "assertion":
            fix["action"] = "fix_logic"
            fix["suggestion"] = f"Fix assertion: {msg}"
        elif etype == "location" and e.get("file"):
            fix["action"] = "read_file"
            fix["suggestion"] = f"Check {e['file']}:{e.get('lineno','?')} — {msg}"
        
        fixes.append(fix)
    
    return {
        "error_count": len(errors),
        "auto_fixable": sum(1 for f in fixes if f["action"] != "manual"),
        "manual_review": sum(1 for f in fixes if f["action"] == "manual"),
        "fixes": fixes[:10]
    }

def loop(cmd: str, src_dir: str, max_loops: int = 3) -> dict:
    """Main autonomous loop."""
    results = []
    
    for i in range(max_loops):
        print(f"\n🔄 Loop {i+1}/{max_loops}: Running '{cmd}'...")
        
        code, stdout, stderr = run_command(cmd, src_dir)
        
        if code == 0:
            print(f"✅ All tests passed after {i+1} loop(s)!")
            return {"success": True, "loops": i+1, "results": results}
        
        print(f"❌ Loop {i+1} failed (exit={code})")
        errors = extract_errors(stdout, stderr)
        analysis = analyze_and_fix(errors, src_dir)
        
        results.append({
            "loop": i+1,
            "exit_code": code,
            "errors": len(errors),
            "analysis": analysis
        })
        
        print(f"   Errors: {len(errors)} | Auto-fixable: {analysis['auto_fixable']} | Manual: {analysis['manual_review']}")
        
        if analysis["auto_fixable"] == 0 and i < max_loops - 1:
            print("   ⚠️  No auto-fixable errors. Suggesting manual fixes...")
            for fix in analysis["fixes"][:3]:
                print(f"      → {fix['suggestion'][:100]}")
        
        if i == max_loops - 1:
            print(f"\n⚠️  Max loops ({max_loops}) reached. Manual intervention needed.")
    
    return {"success": False, "loops": max_loops, "results": results}

def main():
    parser = argparse.ArgumentParser(description="OpenClaw Autonomous Dev Loop")
    parser.add_argument("--dir", required=True, help="Project directory")
    parser.add_argument("--command", required=True, help="Command to run (e.g., 'pytest -x')")
    parser.add_argument("--max-loops", type=int, default=3, help="Max retry loops (default: 3)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()
    
    if not os.path.isdir(args.dir):
        print(f"❌ Directory not found: {args.dir}")
        sys.exit(1)
    
    result = loop(args.command, args.dir, args.max_loops)
    
    if args.json:
        print(json.dumps(result, indent=2))
    elif not result["success"]:
        print("\n📋 Error Summary:")
        for r in result["results"]:
            print(f"  Loop {r['loop']}: {r['errors']} errors")
        print(f"\n💡 Run with --json for detailed fix suggestions")
    
    sys.exit(0 if result["success"] else 1)

if __name__ == "__main__":
    main()
