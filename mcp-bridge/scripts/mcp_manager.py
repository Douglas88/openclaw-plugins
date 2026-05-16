#!/usr/bin/env python3
"""
MCP Server Manager - OpenClaw MCP Server Registry
Manages MCP server configurations in ~/.openclaw/mcp_servers.json

Usage:
    # Add a stdio server
    python3 mcp_manager.py add --name github --transport stdio --command npx --args '-y,@anthropic/mcp-server-github'

    # Add an HTTP server
    python3 mcp_manager.py add --name slack --transport http --url https://mcp.slack.com/mcp --headers '{"Authorization":"Bearer xxxx"}'

    # List servers
    python3 mcp_manager.py list

    # Get server details
    python3 mcp_manager.py get --name github

    # Remove a server
    python3 mcp_manager.py remove --name github
"""

import json
import os
import sys
import argparse
from typing import Dict, Any


CONFIG_PATH = os.path.expanduser("~/.openclaw/mcp_servers.json")


def load_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return {"version": 1, "servers": {}}


def save_config(config: dict):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)


def cmd_add(args):
    config = load_config()
    name = args.name
    
    server = {"transport": args.transport}
    
    if args.transport == "stdio":
        if not args.command:
            print(json.dumps({"error": "--command is required for stdio transport"}))
            sys.exit(1)
        server["command"] = args.command
        server["args"] = json.loads(args.args) if args.args else []
        server["env"] = json.loads(args.env) if args.env else {}
    elif args.transport == "http":
        if not args.url:
            print(json.dumps({"error": "--url is required for http transport"}))
            sys.exit(1)
        server["url"] = args.url
        server["headers"] = json.loads(args.headers) if args.headers else {}
    
    if args.description:
        server["description"] = args.description
    
    config["servers"][name] = server
    save_config(config)
    print(json.dumps({"status": "ok", "message": f"Server '{name}' added successfully"}))


def cmd_remove(args):
    config = load_config()
    name = args.name
    
    if name not in config["servers"]:
        print(json.dumps({"error": f"Server '{name}' not found"}))
        sys.exit(1)
    
    del config["servers"][name]
    save_config(config)
    print(json.dumps({"status": "ok", "message": f"Server '{name}' removed"}))


def cmd_list(args):
    config = load_config()
    servers = config.get("servers", {})
    
    if args.format == "json":
        print(json.dumps(servers, indent=2))
    else:
        if not servers:
            print("No MCP servers configured.")
            print(f"\nConfig file: {CONFIG_PATH}")
            print("\nQuick start - add a test server:")
            print('  python3 mcp_manager.py add --name test --transport stdio --command echo --args \'["hello"]\'')
            return
        
        print(f"{'Name':<20} {'Transport':<10} {'Command/URL'}")
        print("-" * 60)
        for name, srv in servers.items():
            transport = srv.get("transport", "stdio")
            if transport == "http":
                detail = srv.get("url", "")
            else:
                detail = f"{srv.get('command', '')} {' '.join(srv.get('args', []))}"
            desc = srv.get("description", "")
            print(f"{name:<20} {transport:<10} {detail[:40]}")
            if desc:
                print(f"  → {desc}")


def cmd_get(args):
    config = load_config()
    name = args.name
    
    if name not in config["servers"]:
        print(json.dumps({"error": f"Server '{name}' not found"}))
        sys.exit(1)
    
    server = config["servers"][name]
    print(json.dumps(server, indent=2))


def main():
    parser = argparse.ArgumentParser(description="OpenClaw MCP Server Manager")
    subparsers = parser.add_subparsers(dest="action", help="Command")

    # add
    add_parser = subparsers.add_parser("add", help="Add an MCP server")
    add_parser.add_argument("--name", required=True)
    add_parser.add_argument("--transport", required=True, choices=["stdio", "http"])
    add_parser.add_argument("--command")
    add_parser.add_argument("--args", default="[]")
    add_parser.add_argument("--env", default="{}")
    add_parser.add_argument("--url")
    add_parser.add_argument("--headers", default="{}")
    add_parser.add_argument("--description")

    # remove
    rm_parser = subparsers.add_parser("remove", help="Remove an MCP server")
    rm_parser.add_argument("--name", required=True)

    # list
    list_parser = subparsers.add_parser("list", help="List MCP servers")
    list_parser.add_argument("--format", default="table", choices=["table", "json"])

    # get
    get_parser = subparsers.add_parser("get", help="Get server details")
    get_parser.add_argument("--name", required=True)

    args = parser.parse_args()

    if args.action == "add":
        cmd_add(args)
    elif args.action == "remove":
        cmd_remove(args)
    elif args.action == "list":
        cmd_list(args)
    elif args.action == "get":
        cmd_get(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
