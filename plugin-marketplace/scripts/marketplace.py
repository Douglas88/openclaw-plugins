#!/usr/bin/env python3
"""
OpenClaw Plugin Marketplace — Decentralized Git-based plugin registry.
No external dependencies. Uses only stdlib.

Commands:
  list             Show all registered plugins (local + optionally remote)
  search <kw>      Search plugins
  info <name>      Show plugin details
  install <name>   Clone plugin repo into ~/.openclaw/plugin-skills/
  publish          Register a plugin with the registry
  update [name]    Git pull one or all installed plugins
  remove <name>    Remove installed plugin and optionally registry entry
  sync             Fetch remote registry and merge with local
"""

import argparse
import json
import os
import subprocess
import sys
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timezone

REGISTRY_PATH = Path.home() / ".openclaw" / "plugin-registry.json"
SKILLS_DIR = Path.home() / ".openclaw" / "plugin-skills"
REMOTE_REGISTRY_URL = "https://douglas88.github.io/openclaw-plugins/registry.json"

SEED_PLUGINS = [
    {"name": "mcp-bridge", "repo": "https://github.com/openclaw/openclaw", "subpath": "skills/mcp-bridge",
     "category": "integration", "version": "1.0.0",
     "description": "MCP protocol bridge — JSON-RPC 2.0 client + server manager for external tool integration via MCP"},
    {"name": "code-review", "repo": "https://github.com/openclaw/openclaw", "subpath": "skills/code-review",
     "category": "code-quality", "version": "1.0.0",
     "description": "Automated code review with 6-stage security/performance/quality scan and anti-pattern detection"},
    {"name": "test-generator", "repo": "https://github.com/openclaw/openclaw", "subpath": "skills/test-generator",
     "category": "testing", "version": "1.0.0",
     "description": "Generate pytest/Jest/Go tests with fixtures, mocks, parametrize, and coverage reports"},
    {"name": "doc-generator", "repo": "https://github.com/openclaw/openclaw", "subpath": "skills/doc-generator",
     "category": "documentation", "version": "1.0.0",
     "description": "Auto-generate API docs, READMEs, docstrings, and Mermaid architecture diagrams"},
    {"name": "session-tools", "repo": "https://github.com/openclaw/openclaw", "subpath": "skills/session-tools",
     "category": "utilities", "version": "1.0.0",
     "description": "Session export (md/txt/summary), history search, conversation analysis"},
    {"name": "plugin-marketplace", "repo": "https://github.com/openclaw/openclaw", "subpath": "skills/plugin-marketplace",
     "category": "system", "version": "1.0.0",
     "description": "Plugin discovery, install, publish, and update manager — Git-based decentralized registry"},
    {"name": "ide-panel", "repo": "https://github.com/openclaw/openclaw", "subpath": "skills/ide-panel",
     "category": "ide", "version": "1.0.0",
     "description": "Soft-IDE code panel — file tree, syntax viewing, LSP intelligence bridge for WebChat"},
    {"name": "lsp", "repo": "https://github.com/openclaw/openclaw", "subpath": "skills/mcp-bridge/scripts/lsp_mcp_server.py",
     "category": "intelligence", "version": "1.0.0",
     "description": "LSP MCP Server — zero-dependency Python AST-based language intelligence (go-to-def, references, hover, diagnostics)"},
]

# Markdown table header for the list output
TABLE_HEADER = "| Status | Name | Category | Version | Description |\n|--------|------|----------|---------|-------------|"


def load_registry() -> dict:
    if REGISTRY_PATH.exists():
        try:
            with open(REGISTRY_PATH) as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass
    return {"version": 1, "updated": "", "plugins": {}}


def save_registry(registry: dict):
    registry["updated"] = datetime.now(timezone.utc).isoformat() + "Z"
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REGISTRY_PATH, "w") as f:
        json.dump(registry, f, indent=2)


def seed_registry():
    """Initialize registry with seed plugins if empty."""
    registry = load_registry()
    if not registry["plugins"]:
        for p in SEED_PLUGINS:
            registry["plugins"][p["name"]] = p
        save_registry(registry)
    return registry


def is_installed(name: str) -> bool:
    """Check if a plugin is locally installed."""
    return (SKILLS_DIR / name / "SKILL.md").exists()


def fetch_remote_registry() -> dict:
    """Fetch remote registry JSON from GitHub."""
    try:
        req = urllib.request.Request(REMOTE_REGISTRY_URL, headers={"User-Agent": "OpenClaw-Marketplace/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return {"version": 1, "plugins": {}}


def cmd_list(args):
    registry = seed_registry()
    local = registry["plugins"]
    remote = {} if args.local_only else fetch_remote_registry().get("plugins", {})

    all_plugins = {**remote, **local}  # Local overrides remote
    if not all_plugins:
        print("No plugins registered. Use 'publish' to add plugins, or 'sync' to fetch remote registry.")
        return

    print(f"\n# OpenClaw Plugin Marketplace  (local: {len(local)}, remote: {len(remote)})\n")
    print(TABLE_HEADER)
    for name, p in sorted(all_plugins.items()):
        installed = is_installed(name)
        status = "✅" if installed else "⬜"
        desc = p.get("description", "")[:60]
        ver = p.get("version", "?")
        cat = p.get("category", "unknown")
        print(f"| {status} | {name:<20} | {cat:<14} | v{ver:<6} | {desc} |")


def cmd_search(args):
    registry = seed_registry()
    remote = fetch_remote_registry().get("plugins", {})
    all_plugins = {**remote, **registry["plugins"]}
    kw = args.keyword.lower()
    matches = {n: p for n, p in all_plugins.items() if kw in n.lower() or kw in p.get("description", "").lower()}
    if not matches:
        print(f"No plugins found matching '{args.keyword}'")
        return
    print(TABLE_HEADER)
    for name, p in sorted(matches.items()):
        status = "✅" if is_installed(name) else "⬜"
        print(f"| {status} | {name:<20} | {p.get('category','?'):<14} | v{p.get('version','?'):<6} | {p.get('description','')[:60]} |")


def cmd_info(args):
    registry = seed_registry()
    p = registry["plugins"].get(args.name)
    if not p:
        remote = fetch_remote_registry().get("plugins", {})
        p = remote.get(args.name)
    if not p:
        print(f"Plugin '{args.name}' not found. Use 'list' to see available plugins.")
        return
    print(json.dumps(p, indent=2))
    print(f"\nInstalled: {'✅ yes' if is_installed(args.name) else '⬜ no'}")


def cmd_install(args):
    registry = seed_registry()
    p = registry["plugins"].get(args.name)
    if not p:
        remote = fetch_remote_registry().get("plugins", {})
        p = remote.get(args.name)
    if not p:
        print(f"Plugin '{args.name}' not found in any registry.")
        return

    repo = p.get("repo", "")
    subpath = p.get("subpath", "")
    if not repo:
        print(f"Plugin '{args.name}' has no repo URL. Cannot install.")
        return

    dest = SKILLS_DIR / args.name
    if dest.exists():
        print(f"Plugin '{args.name}' already installed at {dest}")
        print("Use 'update' to refresh, or 'remove' first.")
        return

    print(f"Installing {args.name} from {repo}...")
    if subpath:
        # Clone repo to temp, then copy subpath (file or directory)
        import tempfile, shutil
        tmpdir = Path(tempfile.mkdtemp())
        try:
            subprocess.run(["git", "clone", "--depth", "1", repo, str(tmpdir)], check=True)
            src = tmpdir / subpath
            if src.is_dir():
                shutil.copytree(src, dest)
            elif src.is_file():
                dest.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest / src.name)
            else:
                print(f"❌ Subpath '{subpath}' not found in repo")
                return
            print(f"✅ Installed {args.name} v{p.get('version','?')}")
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)
    else:
        subprocess.run(["git", "clone", "--depth", "1", repo, str(dest)], check=True)
        print(f"✅ Installed {args.name} v{p.get('version','?')}")


def cmd_publish(args):
    registry = seed_registry()
    registry["plugins"][args.name] = {
        "name": args.name,
        "repo": args.repo or "",
        "subpath": args.subpath or "",
        "category": args.category or "unknown",
        "version": args.version or "0.1.0",
        "description": args.description or "",
        "author": args.author or ""
    }
    save_registry(registry)
    print(f"✅ Published {args.name} v{args.version} to local registry")
    print("To share publicly, add this entry to the remote registry.json and push to GitHub.")


def cmd_update(args):
    if args.name:
        names = [args.name]
    else:
        names = [d.name for d in SKILLS_DIR.iterdir() if d.is_dir() and (d / ".git").exists()]

    for name in names:
        d = SKILLS_DIR / name
        if not d.exists():
            print(f"⚠️  {name}: not installed")
            continue
        try:
            subprocess.run(["git", "-C", str(d), "pull"], check=True)
            print(f"✅ {name}: updated")
        except subprocess.CalledProcessError:
            print(f"⚠️  {name}: update failed (check git remote)")


def cmd_remove(args):
    dest = SKILLS_DIR / args.name
    if dest.exists():
        import shutil
        shutil.rmtree(dest, ignore_errors=True)
        print(f"✅ Removed {args.name} from plugin-skills")
    else:
        print(f"⚠️  {args.name} was not installed")

    if args.also_unregister:
        registry = load_registry()
        if args.name in registry.get("plugins", {}):
            del registry["plugins"][args.name]
            save_registry(registry)
            print(f"✅ Unregistered {args.name} from local registry")


def cmd_sync(args):
    remote = fetch_remote_registry()
    if not remote.get("plugins"):
        print("⚠️  Remote registry is empty or unreachable.")
        print(f"   URL: {REMOTE_REGISTRY_URL}")
        return

    local = load_registry()
    merged = {**remote.get("plugins", {}), **local.get("plugins", {})}
    local["plugins"] = merged
    save_registry(local)
    print(f"✅ Synced {len(remote['plugins'])} remote + {len(local['plugins'])} local plugins")
    new_count = len(remote["plugins"]) - len([p for p in remote["plugins"] if p in local.get("plugins", {})])
    if new_count > 0:
        print(f"   {new_count} new plugins available. Use 'list' to see all.")


def main():
    parser = argparse.ArgumentParser(description="OpenClaw Plugin Marketplace")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("list", help="List all plugins").add_argument("--local-only", action="store_true")
    sp = sub.add_parser("search", help="Search plugins"); sp.add_argument("keyword")
    sp = sub.add_parser("info", help="Show plugin details"); sp.add_argument("name")
    sp = sub.add_parser("install", help="Install a plugin"); sp.add_argument("name")
    sp = sub.add_parser("sync", help="Sync with remote registry")

    pb = sub.add_parser("publish", help="Register a plugin")
    pb.add_argument("--name", required=True); pb.add_argument("--repo"); pb.add_argument("--subpath")
    pb.add_argument("--category"); pb.add_argument("--version"); pb.add_argument("--description"); pb.add_argument("--author")

    up = sub.add_parser("update", help="Update installed plugins"); up.add_argument("name", nargs="?")
    rm = sub.add_parser("remove", help="Remove a plugin"); rm.add_argument("name")
    rm.add_argument("--also-unregister", action="store_true")

    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        return

    seed_registry()  # Auto-seed if empty
    {"list": cmd_list, "search": cmd_search, "info": cmd_info,
     "install": cmd_install, "publish": cmd_publish, "update": cmd_update,
     "remove": cmd_remove, "sync": cmd_sync}[args.cmd](args)


if __name__ == "__main__":
    main()
