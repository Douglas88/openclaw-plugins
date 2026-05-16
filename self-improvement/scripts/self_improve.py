#!/usr/bin/env python3
"""
OpenClaw Self-Improvement Analyzer
====================================
Analyzes OpenClaw performance and suggests optimizations.

Usage:
  python3 self_improve.py analyze    # Analyze current state
  python3 self_improve.py apply      # Apply suggested optimizations
  python3 self_improve.py report     # Generate improvement report
"""

import json, os, sys, subprocess
from pathlib import Path
from datetime import datetime, timezone

HOME = Path.home()


def analyze_sessions():
    """Analyze session data for patterns."""
    sessions_json = HOME / ".openclaw" / "agents" / "main" / "sessions" / "sessions.json"
    if not sessions_json.exists():
        return {"error": "No sessions data"}
    
    with open(sessions_json) as f:
        data = json.load(f)
    
    sessions = data.get("sessions", data)
    stats = {"count": len(sessions), "total_tokens": 0, "total_cost": 0, "models": {}}
    
    for k, v in sessions.items():
        tokens = v.get("totalTokens", 0) or 0
        cost = v.get("estimatedCostUsd", 0) or 0
        model = v.get("model", "unknown")
        stats["total_tokens"] += tokens
        stats["total_cost"] += cost
        stats["models"][model] = stats["models"].get(model, 0) + 1
    
    return stats

def analyze_config():
    """Check configuration health."""
    issues = []
    
    config = HOME / ".openclaw" / "openclaw.json"
    if config.exists():
        with open(config) as f:
            cfg = json.load(f)
        
        if cfg.get("gateway", {}).get("bind") == "loopback":
            pass  # Good for local
        else:
            issues.append("Gateway not loopback-bound — check exposure")
        
        model = cfg.get("agents", {}).get("defaults", {}).get("model", {}).get("primary", "")
        if "flash" in model.lower() and "pro" not in model.lower():
            issues.append("Using flash model for main — consider Pro for complex tasks")
    
    return issues

def analyze_skills():
    """Check skill coverage gaps."""
    builtin = HOME / ".nvm/versions/node/v24.15.0/lib/node_modules/openclaw/skills"
    custom = HOME / ".openclaw" / "plugin-skills"
    
    all_skills = set()
    for d in [builtin, custom]:
        if d.exists():
            all_skills.update(s.name for s in d.iterdir() if s.is_dir() and (s / "SKILL.md").exists())
    
    recommendations = []
    desired = {
        "code-review": "Code review capability",
        "test-generator": "Automated test generation",
        "doc-generator": "Documentation generation",
        "mcp-bridge": "MCP protocol support",
        "desktop-automation": "Desktop GUI control",
        "codex-mode": "Autonomous coding loop",
        "reasoning-engine": "Advanced reasoning",
        "self-improvement": "Self-optimization",
    }
    
    for skill, desc in desired.items():
        if skill not in all_skills:
            recommendations.append(f"Install {skill}: {desc}")
    
    return len(all_skills), recommendations

def analyze_heartbeat():
    """Check heartbeat configuration."""
    hb = HOME / ".openclaw" / "workspace" / "HEARTBEAT.md"
    if hb.exists():
        content = hb.read_text()
        if "High Priority" in content and "Medium Priority" in content:
            return "✅ Active monitoring (3-tier)"
        elif "empty" in content.lower() or len(content) < 100:
            return "⚠️  Empty/minimal heartbeat — add monitoring tasks"
    return "❌ No heartbeat configured"

def generate_report():
    """Full self-improvement report."""
    print("🔍 OpenClaw Self-Improvement Report")
    print("=" * 50)
    print(f"  Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print()
    
    # Sessions
    sessions = analyze_sessions()
    if "error" not in sessions:
        print("📊 Session Analytics:")
        print(f"   Sessions: {sessions['count']}")
        print(f"   Tokens: {sessions['total_tokens']:,}")
        print(f"   Cost: ${sessions['total_cost']:.4f}")
        if sessions['models']:
            print(f"   Models: {sessions['models']}")
    
    # Config
    print("\n⚙️  Configuration:")
    issues = analyze_config()
    if issues:
        for i in issues:
            print(f"   ⚠️  {i}")
    else:
        print("   ✅ No issues found")
    
    # Skills
    count, recs = analyze_skills()
    print(f"\n🧩 Skills: {count} installed")
    if recs:
        for r in recs:
            print(f"   📦 {r}")
    
    # Heartbeat
    hb = analyze_heartbeat()
    print(f"\n💓 Heartbeat: {hb}")
    
    # Benchmark
    bench_script = HOME / ".openclaw" / "plugin-skills" / "plugin-marketplace" / "scripts" / "benchmark.py"
    if bench_script.exists():
        try:
            result = subprocess.run(["python3", str(bench_script)], capture_output=True, text=True, timeout=15)
            lines = result.stdout.split("\n")
            for line in lines:
                if "Grade:" in line or "Score:" in line or "vs Codex" in line or "vs Claude" in line:
                    print(f"   {line.strip()}")
        except:
            pass
    
    print("\n" + "=" * 50)
    print("💡 Run 'python3 self_improve.py apply' to auto-install missing skills")


def apply_improvements():
    """Auto-install missing recommended skills."""
    _, recs = analyze_skills()
    
    if not recs:
        print("✅ All recommended skills installed!")
        return
    
    marketplace = HOME / ".openclaw" / "plugin-skills" / "plugin-marketplace" / "scripts" / "marketplace.py"
    if not marketplace.exists():
        print("❌ Marketplace not installed. Run: curl ... | bash")
        return
    
    print("📦 Installing missing skills...")
    for rec in recs:
        skill = rec.split(":")[0].replace("Install ", "").strip()
        print(f"   Installing {skill}...")
        try:
            subprocess.run(["python3", str(marketplace), "install", skill], timeout=60)
        except:
            print(f"   ⚠️  Could not auto-install {skill}")
    
    print("\n✅ Improvement cycle complete. Run benchmark to compare.")


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("analyze", "apply", "report"):
        print("Usage: python3 self_improve.py [analyze|apply|report]")
        sys.exit(1)
    
    cmd = sys.argv[1]
    if cmd == "report" or cmd == "analyze":
        generate_report()
    elif cmd == "apply":
        apply_improvements()
