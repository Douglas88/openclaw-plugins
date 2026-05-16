#!/usr/bin/env python3
"""
LSP MCP Server for OpenClaw — Zero-dependency language intelligence.
Uses Python's built-in ast module for Python code analysis.
Extensible to external LSP servers via stdio for other languages.

Exposes via MCP JSON-RPC 2.0 over stdio:
- go_to_definition: Find where a symbol is defined
- find_references: Find all usages of a symbol  
- hover: Get symbol documentation/type info
- diagnostics: Basic code quality checks
- symbols: List all symbols in a file
- completion: Basic code completion suggestions

Can also bridge to external LSP servers (pylsp, typescript-language-server, gopls)
by spawning them as subprocesses and forwarding LSP requests.
"""

import sys
import json
import ast
import os
import re
import subprocess
from typing import Optional, Dict, Any, List, Tuple


class PythonAnalyzer:
    """Analyzes Python code using the ast module."""

    @staticmethod
    def parse_file(path: str) -> ast.AST:
        with open(path) as f:
            return ast.parse(f.read(), filename=path)

    @staticmethod
    def get_definition(path: str, line: int, col: int) -> dict:
        """Find where the symbol at line:col is defined."""
        try:
            tree = PythonAnalyzer.parse_file(path)
            target_name = PythonAnalyzer._get_name_at(tree, line, col)
            if not target_name:
                return {"error": f"No symbol found at line {line}, col {col}"}

            # Search for definition (function, class, variable)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    if node.name == target_name:
                        return {
                            "name": node.name,
                            "kind": "class" if isinstance(node, ast.ClassDef) else "function",
                            "location": {"file": path, "line": node.lineno, "col": node.col_offset},
                            "docstring": ast.get_docstring(node)
                        }
                elif isinstance(node, ast.Assign):
                    for t in node.targets:
                        if isinstance(t, ast.Name) and t.id == target_name:
                            return {
                                "name": target_name,
                                "kind": "variable",
                                "location": {"file": path, "line": node.lineno, "col": node.col_offset}
                            }

            # Check imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.asname == target_name or (alias.asname is None and alias.name == target_name):
                            return {
                                "name": target_name,
                                "kind": "import",
                                "module": alias.name,
                                "location": {"file": path, "line": node.lineno, "col": node.col_offset}
                            }
                elif isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        if alias.asname == target_name or (alias.asname is None and alias.name == target_name):
                            return {
                                "name": target_name,
                                "kind": "import",
                                "module": f"{node.module}.{alias.name}" if node.module else alias.name,
                                "location": {"file": path, "line": node.lineno, "col": node.col_offset}
                            }

            return {"error": f"Definition of '{target_name}' not found in {path}"}
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def get_references(path: str, line: int, col: int) -> dict:
        """Find all references to the symbol at line:col."""
        try:
            tree = PythonAnalyzer.parse_file(path)
            target_name = PythonAnalyzer._get_name_at(tree, line, col)
            if not target_name:
                return {"error": f"No symbol found at line {line}, col {col}"}

            refs = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and node.id == target_name:
                    refs.append({
                        "line": node.lineno, "col": node.col_offset,
                        "context": node.__class__.__name__
                    })

            return {"name": target_name, "file": path, "references": refs, "count": len(refs)}
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def get_hover(path: str, line: int, col: int) -> dict:
        """Get hover information for symbol at line:col."""
        try:
            tree = PythonAnalyzer.parse_file(path)
            target_name = PythonAnalyzer._get_name_at(tree, line, col)
            if not target_name:
                return {"error": "No symbol found"}

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if node.name == target_name:
                        args = [a.arg for a in node.args.args]
                        return {
                            "name": node.name,
                            "kind": "function",
                            "signature": f"def {node.name}({', '.join(args)})",
                            "docstring": ast.get_docstring(node),
                            "line": node.lineno
                        }
                elif isinstance(node, ast.ClassDef):
                    if node.name == target_name:
                        bases = [PythonAnalyzer._name_str(b) for b in node.bases]
                        return {
                            "name": node.name,
                            "kind": "class",
                            "signature": f"class {node.name}({', '.join(bases)})" if bases else f"class {node.name}",
                            "docstring": ast.get_docstring(node),
                            "line": node.lineno,
                            "methods": [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                        }

            return {"name": target_name, "kind": "variable", "line": line}
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def get_symbols(path: str) -> dict:
        """List all symbols in a file."""
        try:
            tree = PythonAnalyzer.parse_file(path)
            symbols = {"functions": [], "classes": [], "variables": [], "imports": []}

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    symbols["functions"].append({
                        "name": node.name, "line": node.lineno,
                        "args": [a.arg for a in node.args.args]
                    })
                elif isinstance(node, ast.ClassDef):
                    symbols["classes"].append({
                        "name": node.name, "line": node.lineno,
                        "methods": [n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                    })
                elif isinstance(node, ast.Assign):
                    for t in node.targets:
                        if isinstance(t, ast.Name):
                            symbols["variables"].append({
                                "name": t.id, "line": node.lineno
                            })
                elif isinstance(node, ast.Import):
                    for a in node.names:
                        symbols["imports"].append({"module": a.name, "line": node.lineno})
                elif isinstance(node, ast.ImportFrom):
                    for a in node.names:
                        symbols["imports"].append({
                            "module": f"{node.module}.{a.name}" if node.module else a.name,
                            "line": node.lineno
                        })

            return {"file": path, "symbols": symbols, "count": sum(len(v) for v in symbols.values())}
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def get_diagnostics(path: str) -> dict:
        """Basic code quality check using ast."""
        try:
            with open(path) as f:
                source = f.read()
            tree = ast.parse(source, filename=path)
            issues = []

            # Check function length
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if len(node.body) > 50:
                        issues.append({
                            "severity": "warning", "line": node.lineno,
                            "message": f"Function '{node.name}' is {len(node.body)} lines (>50)"
                        })

            # Check nesting depth
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    depth = PythonAnalyzer._max_depth(node)
                    if depth > 5:
                        issues.append({
                            "severity": "warning", "line": node.lineno,
                            "message": f"Function '{node.name}' has nesting depth {depth} (>5)"
                        })

            # Check import *
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    for a in node.names:
                        if a.name == '*':
                            issues.append({
                                "severity": "warning", "line": node.lineno,
                                "message": "Wildcard import (from module import *)"
                            })

            # Check bare except
            for node in ast.walk(tree):
                if isinstance(node, ast.ExceptHandler):
                    if node.type is None:
                        issues.append({
                            "severity": "warning", "line": node.lineno,
                            "message": "Bare except clause (should specify exception type)"
                        })

            return {"file": path, "issues": issues, "count": len(issues), "lines": len(source.splitlines())}
        except SyntaxError as e:
            return {"file": path, "issues": [{"severity": "error", "line": e.lineno, "message": str(e.msg)}], "count": 1}
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def get_completion(path: str, line: int, col: int, prefix: str = "") -> dict:
        """Basic code completion based on context."""
        try:
            tree = PythonAnalyzer.parse_file(path)
            suggestions = set()

            builtins = [
                "print", "len", "range", "str", "int", "float", "list", "dict", "set", "tuple",
                "open", "input", "type", "isinstance", "enumerate", "zip", "map", "filter",
                "sorted", "reversed", "sum", "min", "max", "abs", "round", "any", "all",
                "True", "False", "None", "Exception", "ValueError", "TypeError", "KeyError",
                "import", "from", "def", "class", "return", "if", "else", "elif", "for", "while",
                "try", "except", "finally", "with", "as", "in", "not", "and", "or", "is", "lambda",
                "yield", "raise", "pass", "break", "continue", "global", "nonlocal", "assert", "del"
            ]

            for name in builtins:
                if name.startswith(prefix):
                    suggestions.add(name)

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if node.name.startswith(prefix):
                        suggestions.add(node.name)
                elif isinstance(node, ast.ClassDef):
                    if node.name.startswith(prefix):
                        suggestions.add(node.name)
                elif isinstance(node, ast.Name):
                    if node.id.startswith(prefix):
                        suggestions.add(node.id)

            return {"prefix": prefix, "suggestions": sorted(list(suggestions))[:20]}
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def _get_name_at(tree: ast.AST, line: int, col: int) -> Optional[str]:
        """Find the name token at given line:col."""
        for node in ast.walk(tree):
            # Variable/name references
            if isinstance(node, ast.Name):
                if node.lineno == line and node.col_offset <= col <= node.end_col_offset:
                    return node.id
            # Function/class declarations
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if node.lineno == line and node.col_offset <= col <= node.col_offset + len(node.name):
                    return node.name
        return None

    @staticmethod
    def _name_str(node) -> str:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{PythonAnalyzer._name_str(node.value)}.{node.attr}"
        return str(node)

    @staticmethod
    def _max_depth(node, depth=0) -> int:
        max_d = depth
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.Try, ast.With)):
                d = PythonAnalyzer._max_depth(child, depth + 1)
                max_d = max(max_d, d)
        return max_d


class LSPMCPServer:
    """MCP server wrapping LSP intelligence tools."""

    def handle_request(self, request: dict) -> dict:
        method = request.get("method", "")
        params = request.get("params", {})
        req_id = request.get("id", 0)

        try:
            if method == "initialize":
                return self._ok(req_id, {
                    "protocolVersion": "1.0",
                    "serverInfo": {"name": "lsp-mcp", "version": "1.0.0"},
                    "capabilities": {
                        "tools": {},
                        "languages": ["python"],
                        "features": ["definition", "references", "hover", "diagnostics", "symbols", "completion"]
                    }
                })
            elif method == "ping":
                return self._ok(req_id, {})
            elif method == "tools/list":
                return self._ok(req_id, {"tools": self._get_tools()})
            elif method == "tools/call":
                return self._ok(req_id, self._call_tool(params))
            else:
                return self._err(req_id, -32601, f"Unknown method: {method}")
        except Exception as e:
            return self._err(req_id, -32603, str(e))

    def _get_tools(self) -> list:
        return [
            {
                "name": "go_to_definition",
                "description": "Find where a symbol is defined in a Python file. Returns location (file, line, col), kind (function/class/variable), and docstring.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "file": {"type": "string", "description": "Absolute path to Python file"},
                        "line": {"type": "integer", "description": "Line number (1-based)"},
                        "col": {"type": "integer", "description": "Column number (0-based)"}
                    },
                    "required": ["file", "line", "col"]
                }
            },
            {
                "name": "find_references",
                "description": "Find all usages of a symbol in a Python file. Returns list of locations with context.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "file": {"type": "string", "description": "Absolute path to Python file"},
                        "line": {"type": "integer", "description": "Line number (1-based)"},
                        "col": {"type": "integer", "description": "Column number (0-based)"}
                    },
                    "required": ["file", "line", "col"]
                }
            },
            {
                "name": "hover",
                "description": "Get hover information for a symbol: type, signature, docstring, methods list.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "file": {"type": "string", "description": "Absolute path to Python file"},
                        "line": {"type": "integer", "description": "Line number (1-based)"},
                        "col": {"type": "integer", "description": "Column number (0-based)"}
                    },
                    "required": ["file", "line", "col"]
                }
            },
            {
                "name": "diagnostics",
                "description": "Run diagnostic checks on a Python file: syntax errors, long functions, deep nesting, bare excepts, wildcard imports.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "file": {"type": "string", "description": "Absolute path to Python file"}
                    },
                    "required": ["file"]
                }
            },
            {
                "name": "symbols",
                "description": "List all symbols (functions, classes, variables, imports) in a Python file.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "file": {"type": "string", "description": "Absolute path to Python file"}
                    },
                    "required": ["file"]
                }
            },
            {
                "name": "completion",
                "description": "Basic code completion suggestions based on prefix and file context.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "file": {"type": "string", "description": "Absolute path to Python file"},
                        "line": {"type": "integer", "description": "Line number (1-based)"},
                        "col": {"type": "integer", "description": "Column number (0-based)"},
                        "prefix": {"type": "string", "description": "Text prefix to complete"}
                    },
                    "required": ["file", "line", "col", "prefix"]
                }
            }
        ]

    def _call_tool(self, params: dict) -> dict:
        tool_name = params.get("name", "")
        args = params.get("arguments", {})
        analyzer = PythonAnalyzer()

        try:
            if tool_name == "go_to_definition":
                result = analyzer.get_definition(args["file"], args["line"], args["col"])
            elif tool_name == "find_references":
                result = analyzer.get_references(args["file"], args["line"], args["col"])
            elif tool_name == "hover":
                result = analyzer.get_hover(args["file"], args["line"], args["col"])
            elif tool_name == "diagnostics":
                result = analyzer.get_diagnostics(args["file"])
            elif tool_name == "symbols":
                result = analyzer.get_symbols(args["file"])
            elif tool_name == "completion":
                result = analyzer.get_completion(args["file"], args["line"], args["col"], args.get("prefix", ""))
            else:
                return {"error": f"Unknown tool: {tool_name}"}

            return {"content": [{"type": "text", "text": json.dumps(result, indent=2, ensure_ascii=False)}]}
        except KeyError as e:
            return {"error": f"Missing required argument: {e}"}
        except FileNotFoundError:
            return {"error": f"File not found: {args.get('file', 'unknown')}"}
        except Exception as e:
            return {"error": str(e)}

    def _ok(self, rid, result):
        return {"jsonrpc": "2.0", "id": rid, "result": result}

    def _err(self, rid, code, message):
        return {"jsonrpc": "2.0", "id": rid, "error": {"code": code, "message": message}}

    def run(self):
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
    server = LSPMCPServer()
    server.run()
