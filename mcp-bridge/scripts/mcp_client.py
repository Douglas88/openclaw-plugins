#!/usr/bin/env python3
"""
MCP Bridge Client - OpenClaw MCP Protocol Implementation
Implements JSON-RPC 2.0 over stdio and HTTP transports for MCP servers.

Usage:
    # List tools from a server
    python3 mcp_client.py --action list_tools --server github

    # Call a tool
    python3 mcp_client.py --action call_tool --server github --tool search_repos --args '{"query":"openclaw"}'

    # List resources
    python3 mcp_client.py --action list_resources --server db

    # Read a resource
    python3 mcp_client.py --action read_resource --server db --uri "db://users/table"

    # Initialize connection (test)
    python3 mcp_client.py --action ping --server github
"""

import json
import subprocess
import sys
import os
import time
import urllib.request
import urllib.error
import argparse
from typing import Optional, Dict, Any, List


class MCPStdioClient:
    """MCP client using stdio transport (local processes)."""

    def __init__(self, command: str, args: List[str], env: Dict[str, str] = None):
        self.command = command
        self.args = args
        self.env = {**os.environ, **(env or {})}

    def _send_request(self, method: str, params: dict = None) -> dict:
        """Send a JSON-RPC request and get response."""
        request = {
            "jsonrpc": "2.0",
            "id": int(time.time() * 1000),
            "method": method,
            "params": params or {}
        }

        proc = subprocess.Popen(
            [self.command] + self.args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=self.env,
            text=True
        )

        request_json = json.dumps(request)
        stdout, stderr = proc.communicate(input=request_json + "\n", timeout=30)

        if proc.returncode != 0 and not stdout:
            return {"error": f"Process exited with code {proc.returncode}: {stderr}"}

        if not stdout.strip():
            return {"error": f"No response from server: {stderr}"}

        try:
            # MCP servers may send multiple lines; take the last JSON response
            lines = [l.strip() for l in stdout.strip().split("\n") if l.strip()]
            for line in reversed(lines):
                try:
                    return json.loads(line)
                except json.JSONDecodeError:
                    continue
            return {"error": f"No valid JSON response. Raw: {stdout[:500]}"}
        except Exception as e:
            return {"error": str(e)}

    def initialize(self) -> dict:
        return self._send_request("initialize", {
            "protocolVersion": "1.0",
            "capabilities": {},
            "clientInfo": {"name": "openclaw-mcp-bridge", "version": "1.0.0"}
        })

    def list_tools(self) -> dict:
        return self._send_request("tools/list")

    def call_tool(self, name: str, arguments: dict = None) -> dict:
        return self._send_request("tools/call", {
            "name": name,
            "arguments": arguments or {}
        })

    def list_resources(self) -> dict:
        return self._send_request("resources/list")

    def read_resource(self, uri: str) -> dict:
        return self._send_request("resources/read", {"uri": uri})

    def ping(self) -> dict:
        return self._send_request("ping")


class MCPHttpClient:
    """MCP client using HTTP transport (remote servers)."""

    def __init__(self, url: str, headers: Dict[str, str] = None):
        self.url = url.rstrip("/")
        self.headers = headers or {}

    def _send_request(self, method: str, params: dict = None) -> dict:
        request = {
            "jsonrpc": "2.0",
            "id": int(time.time() * 1000),
            "method": method,
            "params": params or {}
        }

        data = json.dumps(request).encode("utf-8")
        req = urllib.request.Request(
            self.url,
            data=data,
            headers={**self.headers, "Content-Type": "application/json"},
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            return {"error": f"HTTP {e.code}: {e.reason}"}
        except Exception as e:
            return {"error": str(e)}

    def initialize(self) -> dict:
        return self._send_request("initialize", {
            "protocolVersion": "1.0",
            "capabilities": {},
            "clientInfo": {"name": "openclaw-mcp-bridge", "version": "1.0.0"}
        })

    def list_tools(self) -> dict:
        return self._send_request("tools/list")

    def call_tool(self, name: str, arguments: dict = None) -> dict:
        return self._send_request("tools/call", {
            "name": name,
            "arguments": arguments or {}
        })

    def list_resources(self) -> dict:
        return self._send_request("resources/list")

    def read_resource(self, uri: str) -> dict:
        return self._send_request("resources/read", {"uri": uri})

    def ping(self) -> dict:
        return self._send_request("ping")


def load_server_config(server_name: str) -> dict:
    """Load MCP server configuration from registry."""
    config_path = os.path.expanduser("~/.openclaw/mcp_servers.json")
    
    if not os.path.exists(config_path):
        print(json.dumps({"error": f"MCP config not found at {config_path}. Add a server first."}))
        sys.exit(1)

    with open(config_path) as f:
        config = json.load(f)

    servers = config.get("servers", {})
    if server_name not in servers:
        print(json.dumps({"error": f"Server '{server_name}' not found. Available: {list(servers.keys())}"}))
        sys.exit(1)

    return servers[server_name]


def create_client(server_config: dict):
    """Create appropriate client based on server transport type."""
    transport = server_config.get("transport", "stdio")

    if transport == "http":
        url = server_config.get("url", "")
        headers = server_config.get("headers", {})
        return MCPHttpClient(url, headers)
    else:
        command = server_config.get("command", "")
        args = server_config.get("args", [])
        env = server_config.get("env", {})
        return MCPStdioClient(command, args, env)


def main():
    parser = argparse.ArgumentParser(description="OpenClaw MCP Bridge Client")
    parser.add_argument("--action", required=True, 
                       choices=["list_tools", "call_tool", "list_resources", "read_resource", "ping", "list_servers"],
                       help="Action to perform")
    parser.add_argument("--server", required=True, help="MCP server name")
    parser.add_argument("--tool", help="Tool name (for call_tool)")
    parser.add_argument("--uri", help="Resource URI (for read_resource)")
    parser.add_argument("--args", default="{}", help="JSON arguments (for call_tool)")
    parser.add_argument("--config", default="~/.openclaw/mcp_servers.json", 
                       help="Path to MCP server config")

    args = parser.parse_args()

    if args.action == "list_servers":
        config_path = os.path.expanduser(args.config)
        if os.path.exists(config_path):
            with open(config_path) as f:
                config = json.load(f)
            print(json.dumps(config.get("servers", {}), indent=2))
        else:
            print(json.dumps({}))
        return

    server_config = load_server_config(args.server)
    client = create_client(server_config)

    try:
        if args.action == "ping":
            result = client.ping()
        elif args.action == "list_tools":
            result = client.list_tools()
        elif args.action == "call_tool":
            if not args.tool:
                print(json.dumps({"error": "--tool is required for call_tool"}))
                sys.exit(1)
            tool_args = json.loads(args.args)
            result = client.call_tool(args.tool, tool_args)
        elif args.action == "list_resources":
            result = client.list_resources()
        elif args.action == "read_resource":
            if not args.uri:
                print(json.dumps({"error": "--uri is required for read_resource"}))
                sys.exit(1)
            result = client.read_resource(args.uri)
        else:
            result = {"error": f"Unknown action: {args.action}"}

        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
