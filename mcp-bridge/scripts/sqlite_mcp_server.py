#!/usr/bin/env python3
"""
Lightweight SQLite MCP Server for OpenClaw
Implements JSON-RPC 2.0 over stdio for SQLite database access.

Usage (via MCP Bridge):
    python3 ~/.openclaw/plugin-skills/mcp-bridge/scripts/mcp_manager.py add \
      --name sqlite \
      --transport stdio \
      --command python3 \
      --args '["/home/ubuntu/.openclaw/plugin-skills/mcp-bridge/scripts/sqlite_mcp_server.py","/path/to/db.sqlite"]'
"""

import sys
import json
import sqlite3
import os
import csv
import io


class SQLiteMCPServer:
    """JSON-RPC 2.0 SQLite MCP server over stdio."""

    def __init__(self, db_path: str):
        self.db_path = os.path.abspath(db_path)
        if not os.path.exists(self.db_path):
            # Auto-create with an empty schema
            conn = sqlite3.connect(self.db_path)
            conn.close()

    def handle_request(self, request: dict) -> dict:
        method = request.get("method", "")
        params = request.get("params", {})
        req_id = request.get("id", 0)

        try:
            if method == "initialize":
                return self._mkresp(req_id, {
                    "protocolVersion": "1.0",
                    "capabilities": {"tools": {}, "resources": {}},
                    "serverInfo": {"name": "sqlite-mcp", "version": "1.0.0"}
                })
            elif method == "ping":
                return self._mkresp(req_id, {})
            elif method == "tools/list":
                return self._mkresp(req_id, {"tools": self._get_tools()})
            elif method == "tools/call":
                return self._mkresp(req_id, self._call_tool(params))
            elif method == "resources/list":
                return self._mkresp(req_id, {"resources": self._get_resources()})
            elif method == "resources/read":
                return self._mkresp(req_id, self._read_resource(params))
            else:
                return self._mkerr(req_id, -32601, f"Method not found: {method}")
        except Exception as e:
            return self._mkerr(req_id, -32603, str(e))

    def _get_tools(self) -> list:
        return [
            {
                "name": "query",
                "description": "Execute a read-only SQL query on the SQLite database",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "sql": {"type": "string", "description": "SQL SELECT query"},
                        "params": {"type": "array", "description": "Query parameters", "default": []}
                    },
                    "required": ["sql"]
                }
            },
            {
                "name": "execute",
                "description": "Execute a write SQL statement (INSERT/UPDATE/DELETE/CREATE)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "sql": {"type": "string", "description": "SQL statement"},
                        "params": {"type": "array", "description": "Statement parameters", "default": []}
                    },
                    "required": ["sql"]
                }
            },
            {
                "name": "list_tables",
                "description": "List all tables in the database",
                "inputSchema": {"type": "object", "properties": {}}
            },
            {
                "name": "describe_table",
                "description": "Show table schema and column info",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "table": {"type": "string", "description": "Table name"}
                    },
                    "required": ["table"]
                }
            },
            {
                "name": "export_csv",
                "description": "Export query results as CSV",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "sql": {"type": "string", "description": "SQL SELECT query"},
                        "params": {"type": "array", "description": "Query parameters", "default": []}
                    },
                    "required": ["sql"]
                }
            },
            {
                "name": "db_info",
                "description": "Get database file info (size, path, table count)",
                "inputSchema": {"type": "object", "properties": {}}
            }
        ]

    def _get_resources(self) -> list:
        tables = self._list_tables()
        return [
            {
                "uri": f"sqlite://{self.db_path}/{t}",
                "name": f"Table: {t}",
                "description": f"SQLite table {t} in {os.path.basename(self.db_path)}",
                "mimeType": "application/json"
            }
            for t in tables
        ]

    def _read_resource(self, params: dict) -> dict:
        uri = params.get("uri", "")
        # Parse uri: sqlite://path/to/db/table_name
        parts = uri.replace("sqlite://", "").rsplit("/", 1)
        if len(parts) != 2:
            return {"error": "Invalid resource URI format: sqlite://path/db/table_name"}
        
        table = parts[1]
        rows = self._query(f"SELECT * FROM {table} LIMIT 100")
        return {"contents": [{"uri": uri, "text": json.dumps(rows, indent=2)}]}

    def _call_tool(self, params: dict) -> dict:
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})

        if tool_name == "query":
            result = self._query(arguments.get("sql", ""), arguments.get("params", []))
            return {"content": [{"type": "text", "text": json.dumps(result, indent=2, ensure_ascii=False)}]}

        elif tool_name == "execute":
            result = self._execute(arguments.get("sql", ""), arguments.get("params", []))
            return {"content": [{"type": "text", "text": json.dumps(result)}]}

        elif tool_name == "list_tables":
            tables = self._list_tables()
            return {"content": [{"type": "text", "text": json.dumps(tables, indent=2)}]}

        elif tool_name == "describe_table":
            schema = self._describe(arguments.get("table", ""))
            return {"content": [{"type": "text", "text": json.dumps(schema, indent=2)}]}

        elif tool_name == "export_csv":
            csv_data = self._export_csv(arguments.get("sql", ""), arguments.get("params", []))
            return {"content": [{"type": "text", "text": csv_data}]}

        elif tool_name == "db_info":
            info = self._db_info()
            return {"content": [{"type": "text", "text": json.dumps(info, indent=2)}]}

        else:
            return {"error": f"Unknown tool: {tool_name}"}

    def _query(self, sql: str, params=None) -> list:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.execute(sql, params or [])
            rows = [dict(row) for row in cursor.fetchall()]
            return rows
        finally:
            conn.close()

    def _execute(self, sql: str, params=None) -> dict:
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute(sql, params or [])
            conn.commit()
            return {"rowcount": cursor.rowcount, "lastrowid": cursor.lastrowid}
        finally:
            conn.close()

    def _list_tables(self) -> list:
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            return [row[0] for row in cursor.fetchall()]
        finally:
            conn.close()

    def _describe(self, table: str) -> list:
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute(f"PRAGMA table_info({table})")
            return [
                {"cid": r[0], "name": r[1], "type": r[2], "notnull": bool(r[3]),
                 "default": r[4], "pk": bool(r[5])}
                for r in cursor.fetchall()
            ]
        finally:
            conn.close()

    def _export_csv(self, sql: str, params=None) -> str:
        rows = self._query(sql, params)
        if not rows:
            return ""
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
        return output.getvalue()

    def _db_info(self) -> dict:
        tables = self._list_tables()
        size = os.path.getsize(self.db_path)
        return {
            "path": self.db_path,
            "size_bytes": size,
            "size_mb": round(size / 1048576, 2),
            "table_count": len(tables),
            "tables": tables
        }

    def _mkresp(self, rid, result):
        return {"jsonrpc": "2.0", "id": rid, "result": result}

    def _mkerr(self, rid, code, message):
        return {"jsonrpc": "2.0", "id": rid, "error": {"code": code, "message": message}}

    def run(self):
        """Main stdio loop."""
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                request = json.loads(line)
                response = self.handle_request(request)
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
            except json.JSONDecodeError:
                pass


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: sqlite_mcp_server.py <db_path>"}))
        sys.exit(1)

    db_path = sys.argv[1]
    server = SQLiteMCPServer(db_path)
    server.run()
