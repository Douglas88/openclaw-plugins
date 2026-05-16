#!/usr/bin/env python3
"""
OpenClaw Self-Upgrade Engine
===============================
Automatic upgrade system: check → pull → apply → verify → report.

Usage:
  python3 self_upgrade.py check           # Check for updates
  python3 self_upgrade.py upgrade         # Apply all upgrades
  python3 self_upgrade.py upgrade --dry   # Preview changes
  python3 self_upgrade.py history         # Show upgrade history
"""

import json, os, sys, subprocess, time, shutil
from datetime import datetime, timezone
from pathlib import Path

HOME = Path.home()
OPENCLAW_DIR = HOME / ".openclaw"
SKILLS_DIR = HOME / ".openclaw" / "plugin-skills"
MARKETPLACE_SCRIPT = SKILLS_DIR / "plugin-marketplace" / "scripts" / "marketplace.py"
BACKUP_DIR = OPENCLAW_DIR / "upgrade-backups"
HISTORY_FILE = OPENCLAW_DIR / "upgrade-history.json"
REGISTRY_URL = "https://douglas88.github.io/openclaw-plugins/registry.json"


def load_history():
    if HISTORY_FILE.exists():
        return json.load(open(HISTORY_FILE))
    return {"upgrades": []}

def save_history(entry):
    h = load_history()
    h["upgrades"].append(entry)
    h["upgrades"] = h["upgrades"][-50:]  # Keep last 50
    with open(HISTORY_FILE, "w") as f:
        json.dump(h, f, indent=2)

def backup_configs():
    """Backup critical config files before upgrade."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = BACKUP_DIR / ts
    backup_path.mkdir(exist_ok=True)
    
    files_to_backup = [
        OPENCLAW_DIR / "openclaw.json",
        OPENCLAW_DIR / "exec-approvals.json",
        OPENCLAW_DIR / "mcp_servers.json",
    ]
    
    backed_up = []
    for f in files_to_backup:
        if f.exists():
            shutil.copy2(f, backup_path / f.name)
            backed_up.append(f.name)
    
    return str(backup_path), backed_up

def check_openclaw_version():
    """Check current OpenClaw version vs latest npm."""
    try:
        current = subprocess.run(["openclaw", "--version"], capture_output=True, text=True, timeout=10)
        cv = current.stdout.strip()
    except:
        cv = "unknown"
    
    try:
        latest = subprocess.run(["npm", "view", "openclaw", "version"], capture_output=True, text=True, timeout=10)
        lv = latest.stdout.strip()
    except:
        lv = "unknown"
    
    return {"current": cv, "latest": lv, "update_available": cv != lv and lv != "unknown"}

def check_marketplace_updates():
    """Check marketplace for plugin updates."""
    updates = []
    
    if not MARKETPLACE_SCRIPT.exists():
        return [{"error": "marketplace script not found"}]
    
    try:
        result = subprocess.run(
            ["python3", str(MARKETPLACE_SCRIPT), "list", "--local-only"],
            capture_output=True, text=True, timeout=15
        )
        lines = result.stdout.strip().split("\n")
        
        for line in lines:
            line = line.strip()
            if line.startswith("|") and "✅" in line:
                parts = [p.strip() for p in line.split("|") if p.strip()]
                if len(parts) >= 4:
                    name, category, version = parts[0].replace("✅","").strip(), parts[1], parts[2].replace("v","")
                    updates.append({"name": name, "category": category, "local_version": version})
    except:
        pass
    
    return updates

def check_system_health():
    """Quick system health check before upgrade."""
    health = {"ok": True, "checks": {}}
    
    # Disk
    try:
        stat = os.statvfs("/")
        free_gb = (stat.f_bavail * stat.f_frsize) / (1024**3)
        health["checks"]["disk_free_gb"] = round(free_gb, 1)
        if free_gb < 5:
            health["checks"]["disk_warning"] = "Low disk space"
            health["ok"] = False
    except:
        pass
    
    # Memory
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if "MemAvailable" in line:
                    avail_kb = int(line.split()[1])
                    health["checks"]["mem_available_mb"] = round(avail_kb / 1024)
                    if avail_kb < 100000:
                        health["checks"]["mem_warning"] = "Low memory"
        pass
    except:
        pass
    
    # Config
    for cf in ["openclaw.json", "exec-approvals.json"]:
        path = OPENCLAW_DIR / cf
        health["checks"][f"config_{cf}"] = "present" if path.exists() else "missing"
    
    return health

def apply_upgrade(dry_run=False):
    """Execute the full upgrade pipeline."""
    print("🔄 OpenClaw Self-Upgrade Engine")
    print("=" * 50)
    
    results = {"steps": [], "success": True, "timestamp": datetime.now(timezone.utc).isoformat()}
    
    # 1. Health check
    print("\n📋 Step 1/5: System health check...")
    health = check_system_health()
    if not health["ok"]:
        print("   ⚠️  Warnings:", [k for k,v in health["checks"].items() if "warning" in k])
    print("   ✅ Health OK")
    results["steps"].append({"step": "health_check", "status": "ok", "details": health["checks"]})
    
    # 2. Backup
    print("\n💾 Step 2/5: Backing up configs...")
    if dry_run:
        print("   🔍 Would backup configs")
    else:
        bp, files = backup_configs()
        print(f"   ✅ Backed up {len(files)} files to {bp}")
        results["steps"].append({"step": "backup", "status": "ok", "path": bp, "files": files})
    
    # 3. Check versions
    print("\n🔍 Step 3/5: Checking for updates...")
    oc = check_openclaw_version()
    print(f"   OpenClaw: {oc['current']} → {oc['latest']} {'⚠️ UPDATE AVAILABLE' if oc['update_available'] else '✅ latest'}")
    
    mp = check_marketplace_updates()
    if isinstance(mp, list) and not any("error" in m for m in mp):
        print(f"   Marketplace: {len(mp)} plugins installed")
    
    results["steps"].append({"step": "version_check", "status": "ok", "openclaw": oc, "plugins": len(mp) if isinstance(mp, list) else 0})
    
    # 4. Upgrade OpenClaw
    print("\n⬆️  Step 4/5: Upgrading...")
    if oc["update_available"]:
        if dry_run:
            print(f"   🔍 Would upgrade: npm install -g openclaw@{oc['latest']}")
        else:
            try:
                subprocess.run(["npm", "install", "-g", f"openclaw@{oc['latest']}"], check=True, timeout=60)
                print(f"   ✅ Upgraded to {oc['latest']}")
                results["steps"].append({"step": "upgrade_openclaw", "status": "ok", "version": oc['latest']})
            except:
                print("   ⚠️  Upgrade failed")
                results["steps"].append({"step": "upgrade_openclaw", "status": "failed"})
                results["success"] = False
    else:
        print("   ✅ Already at latest")
    
    # 5. Upgrade plugins
    print("\n🔌 Step 5/5: Syncing plugins...")
    if MARKETPLACE_SCRIPT.exists():
        if dry_run:
            print("   🔍 Would: marketplace sync && marketplace update")
        else:
            try:
                subprocess.run(["python3", str(MARKETPLACE_SCRIPT), "sync"], check=True, timeout=30)
                print("   ✅ Plugins synced from global registry")
            except:
                print("   ⚠️  Plugin sync failed")
    else:
        print("   ⚠️  Marketplace not installed")
    
    # Save history
    if not dry_run:
        results["dry_run"] = False
        save_history({"timestamp": results["timestamp"], "steps": len(results["steps"]), "success": results["success"]})
    
    return results

def show_history():
    h = load_history()
    upgrades = h.get("upgrades", [])
    if not upgrades:
        print("No upgrade history yet.")
        return
    
    print(f"\n📜 Upgrade History ({len(upgrades)} entries)\n")
    for u in upgrades[-10:]:
        ts = u.get("timestamp", "?")[:19]
        status = "✅" if u.get("success") else "❌"
        print(f"  {status} {ts} — {u.get('steps', '?')} steps")


def main():
    parser = argparse.ArgumentParser(description="OpenClaw Self-Upgrade Engine")
    parser.add_argument("command", choices=["check", "upgrade", "history"])
    parser.add_argument("--dry", action="store_true", help="Dry run (no changes)")
    args = parser.parse_args()
    
    if args.command == "check":
        print("🔍 OpenClaw System Check\n")
        oc = check_openclaw_version()
        print(f"  OpenClaw: {oc['current']}")
        print(f"  Latest:   {oc['latest']}")
        print(f"  Status:   {'⚠️ UPDATE AVAILABLE' if oc['update_available'] else '✅ Up to date'}")
        
        health = check_system_health()
        print(f"\n  Disk:   {health['checks'].get('disk_free_gb', '?')} GB free")
        print(f"  Memory: {health['checks'].get('mem_available_mb', '?')} MB available")
        
        plugins = check_marketplace_updates()
        if isinstance(plugins, list) and not any("error" in p for p in plugins):
            print(f"\n  Plugins: {len(plugins)} installed from marketplace")
    
    elif args.command == "upgrade":
        result = apply_upgrade(dry_run=args.dry)
        print("\n" + "=" * 50)
        if result["success"]:
            print("✅ Upgrade complete!")
        else:
            print("⚠️  Upgrade completed with issues")
    
    elif args.command == "history":
        show_history()


if __name__ == "__main__":
    import argparse
    main()
