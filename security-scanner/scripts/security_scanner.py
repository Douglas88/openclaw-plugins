#!/usr/bin/env python3
"""
OpenClaw Security Scanner — Automated Vulnerability Discovery
==============================================================
Multi-layer vulnerability scanning engine.

Scan types:
  python3 security_scanner.py scan --target ./src --type code      # Code pattern scan
  python3 security_scanner.py scan --target ./project --type deps   # Dependency CVE check
  python3 security_scanner.py scan --target http://localhost --type web  # Web vuln scan
  python3 security_scanner.py scan --target 192.168.1.1 --type network  # Network scan
  python3 security_scanner.py full --target ./project               # All scans
  python3 security_scanner.py quick --target ./project              # Fast scan only

⚠️  WARNING: Only scan targets you own or have explicit permission to test.
   Unauthorized scanning is illegal. Use responsibly.
"""

import argparse, json, os, re, socket, ssl, subprocess, sys, urllib.request
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

SEVERITY = {"CRITICAL": 10, "HIGH": 8, "MEDIUM": 5, "LOW": 3, "INFO": 1}
VULN_DB = Path.home() / ".openclaw" / "vuln_findings.json"

# ═══════════════════════════════════════════════
# Code Pattern Scanner
# ═══════════════════════════════════════════════

CODE_PATTERNS = {
    "SQL Injection": {
        "patterns": [
            (r"execute\(.*%.*\b", "String formatting in SQL"),
            (r"execute\(.*f['\"].*\{.*\}.*['\"]", "f-string in SQL query"),
            (r"\.execute\(.*\+.*\)", "String concatenation in SQL"),
            (r"format\(.*SELECT", "format() with SQL"),
        ], "severity": "CRITICAL", "fix": "Use parameterized queries"
    },
    "Command Injection": {
        "patterns": [
            (r"os\.system\(.*\+", "Shell command with concatenation"),
            (r"subprocess\.\w+\(.*shell\s*=\s*True", "subprocess with shell=True"),
            (r"eval\(.*input", "eval() with user input"),
            (r"exec\(.*request", "exec() with request data"),
        ], "severity": "CRITICAL", "fix": "Use subprocess.run with list args"
    },
    "XSS": {
        "patterns": [
            (r"innerHTML\s*=", "innerHTML assignment"),
            (r"dangerouslySetInnerHTML", "React dangerouslySetInnerHTML"),
            (r"document\.write\(", "document.write()"),
            (r"\.html\(.*\{.*\}.*\)", "jQuery .html() with variable"),
        ], "severity": "HIGH", "fix": "Use textContent or escape output"
    },
    "Hardcoded Secrets": {
        "patterns": [
            (r"(?:api_key|apikey|API_KEY)\s*=\s*['\"][^'\"]{8,}['\"]", "Hardcoded API key"),
            (r"(?:password|passwd|secret)\s*=\s*['\"][^'\"]+['\"]", "Hardcoded password"),
            (r"(?:token|TOKEN)\s*=\s*['\"][A-Za-z0-9_\-]{20,}['\"]", "Hardcoded token"),
            (r"-----BEGIN (?:RSA |EC |DSA )?PRIVATE KEY-----", "Private key in code"),
        ], "severity": "CRITICAL", "fix": "Use environment variables"
    },
    "Path Traversal": {
        "patterns": [
            (r"os\.path\.join\(.*request", "Path join with user input"),
            (r"open\(.*\+.*request", "File open with concatenated path"),
            (r"\.\./", "Path traversal pattern"),
        ], "severity": "HIGH", "fix": "Validate and sanitize file paths"
    },
    "Insecure Deserialization": {
        "patterns": [
            (r"pickle\.loads?\(", "Pickle deserialization"),
            (r"yaml\.load\(.*(?!Loader)", "Unsafe YAML load"),
            (r"marshal\.loads?\(", "Marshal deserialization"),
        ], "severity": "HIGH", "fix": "Use safe_load or JSON"
    },
    "SSRF": {
        "patterns": [
            (r"urllib\.request\.urlopen\(.*request", "urlopen with user URL"),
            (r"requests\.(?:get|post)\(.*request", "HTTP request with user URL"),
            (r"httpx\.(?:get|post)\(.*input", "httpx with user input"),
        ], "severity": "MEDIUM", "fix": "Validate and whitelist URLs"
    },
}

def scan_code_patterns(target_dir: str) -> list:
    """Scan code files for vulnerability patterns."""
    findings = []
    extensions = {".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs", ".java", ".rb", ".php", ".sh", ".yaml", ".yml", ".json"}
    
    for root, dirs, files in os.walk(target_dir):
        # Skip hidden dirs, node_modules, venv, .git
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("node_modules", "venv", "__pycache__", "dist", "build")]
        
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext not in extensions and file not in ("Dockerfile", "Makefile"):
                continue
            
            fpath = os.path.join(root, file)
            try:
                with open(fpath, errors="ignore") as f:
                    content = f.read()
            except:
                continue
            
            for vuln_name, vuln_info in CODE_PATTERNS.items():
                for pattern, description in vuln_info["patterns"]:
                    matches = list(re.finditer(pattern, content, re.IGNORECASE))
                    for m in matches:
                        line_no = content[:m.start()].count("\n") + 1
                        findings.append({
                            "type": "code_pattern",
                            "vulnerability": vuln_name,
                            "severity": vuln_info["severity"],
                            "file": fpath,
                            "line": line_no,
                            "match": m.group(0)[:100],
                            "description": description,
                            "fix": vuln_info["fix"]
                        })
    
    return findings


# ═══════════════════════════════════════════════
# Dependency CVE Scanner
# ═══════════════════════════════════════════════

def scan_dependencies(target_dir: str) -> list:
    """Check dependencies for known vulnerabilities using npm audit / pip audit."""
    findings = []
    
    # Python: safety check / pip-audit
    req_file = os.path.join(target_dir, "requirements.txt")
    if os.path.exists(req_file):
        try:
            result = subprocess.run(
                ["pip", "list", "--outdated", "--format", "json"],
                capture_output=True, text=True, timeout=30, cwd=target_dir
            )
            if result.returncode == 0:
                outdated = json.loads(result.stdout)
                for pkg in outdated:
                    findings.append({
                        "type": "dependency",
                        "vulnerability": "Outdated Package",
                        "severity": "MEDIUM",
                        "package": pkg.get("name"),
                        "current": pkg.get("version"),
                        "latest": pkg.get("latest_version"),
                        "fix": f"pip install --upgrade {pkg.get('name')}"
                    })
        except:
            pass
    
    # Node.js: npm audit
    pkg_file = os.path.join(target_dir, "package.json")
    if os.path.exists(pkg_file):
        try:
            result = subprocess.run(
                ["npm", "audit", "--json"],
                capture_output=True, text=True, timeout=60, cwd=target_dir
            )
            if result.stdout.strip():
                try:
                    audit = json.loads(result.stdout)
                    for adv_id, adv in audit.get("advisories", {}).items():
                        findings.append({
                            "type": "dependency",
                            "vulnerability": adv.get("title", "Unknown"),
                            "severity": adv.get("severity", "moderate").upper(),
                            "package": adv.get("module_name"),
                            "cve": adv.get("cves", []),
                            "fix": adv.get("recommendation", "Update package")
                        })
                except:
                    pass
        except:
            pass
    
    return findings


# ═══════════════════════════════════════════════
# Web Scanner
# ═══════════════════════════════════════════════

WEB_TESTS = {
    "SQL Injection": {
        "payloads": ["' OR '1'='1", "1' OR '1'='1' --", '" OR "1"="1'],
        "indicators": ["sql", "mysql", "syntax", "error in your SQL"],
        "severity": "CRITICAL"
    },
    "XSS": {
        "payloads": ["<script>alert(1)</script>", '"><script>alert(1)</script>', "javascript:alert(1)"],
        "indicators": ["<script>alert(1)</script>"],
        "severity": "HIGH"
    },
    "Path Traversal": {
        "payloads": ["../../../etc/passwd", "..\\..\\..\\windows\\win.ini"],
        "indicators": ["root:", "[fonts]", "boot loader"],
        "severity": "HIGH"
    },
}

def scan_web(target_url: str) -> list:
    """Basic web vulnerability scan."""
    findings = []
    
    if not target_url.startswith("http"):
        target_url = "http://" + target_url
    
    for vuln_name, test in WEB_TESTS.items():
        for payload in test["payloads"][:2]:  # Limit payloads per scan
            try:
                # Test in query parameter
                test_url = f"{target_url}/?q={urllib.parse.quote(payload)}"
                req = urllib.request.Request(test_url, headers={"User-Agent": "OpenClaw-Security-Scanner/1.0"})
                with urllib.request.urlopen(req, timeout=5) as resp:
                    body = resp.read().decode("utf-8", errors="ignore").lower()
                    for indicator in test["indicators"]:
                        if indicator.lower() in body:
                            findings.append({
                                "type": "web",
                                "vulnerability": vuln_name,
                                "severity": test["severity"],
                                "url": target_url,
                                "payload": payload,
                                "indicator": indicator,
                                "fix": f"Sanitize input. Apply appropriate encoding/filtering for {vuln_name}."
                            })
                            break
            except:
                pass  # Timeout/error is not necessarily a vulnerability
    
    # Check headers
    try:
        req = urllib.request.Request(target_url, headers={"User-Agent": "OpenClaw-Security-Scanner/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            headers = resp.headers
            if "X-Content-Type-Options" not in headers:
                findings.append({"type": "web", "vulnerability": "Missing Security Header", "severity": "LOW",
                    "url": target_url, "detail": "X-Content-Type-Options missing", "fix": "Add: X-Content-Type-Options: nosniff"})
            if "X-Frame-Options" not in headers:
                findings.append({"type": "web", "vulnerability": "Missing Security Header", "severity": "LOW",
                    "url": target_url, "detail": "X-Frame-Options missing", "fix": "Add: X-Frame-Options: DENY"})
    except:
        findings.append({"type": "web", "vulnerability": "Connection Failed", "severity": "INFO",
            "url": target_url, "detail": "Could not connect to target"})
    
    return findings


# ═══════════════════════════════════════════════
# Network Scanner (lightweight)
# ═══════════════════════════════════════════════

COMMON_PORTS = {21:"FTP", 22:"SSH", 23:"Telnet", 25:"SMTP", 53:"DNS", 80:"HTTP", 110:"POP3",
                143:"IMAP", 443:"HTTPS", 993:"IMAPS", 995:"POP3S", 3306:"MySQL", 3389:"RDP",
                5432:"PostgreSQL", 6379:"Redis", 8080:"HTTP-Alt", 8443:"HTTPS-Alt", 27017:"MongoDB"}

def scan_network(target: str, ports: list = None) -> list:
    """Lightweight port scan."""
    findings = []
    if ports is None:
        ports = [80, 443, 22, 8080, 8443, 3306, 5432, 6379, 27017, 21, 25]
    
    host = target.split("://")[-1].split("/")[0].split(":")[0]
    
    def check_port(port):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((host, port))
            sock.close()
            if result == 0:
                service = COMMON_PORTS.get(port, "Unknown")
                return {"type": "network", "host": host, "port": port, "service": service,
                        "severity": "INFO", "finding": f"Port {port} ({service}) open"}
        except:
            pass
        return None
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(check_port, p): p for p in ports}
        for future in as_completed(futures):
            result = future.result()
            if result:
                findings.append(result)
    
    return sorted(findings, key=lambda x: x["port"])


# ═══════════════════════════════════════════════
# Main Scanner
# ═══════════════════════════════════════════════

def save_findings(findings: list):
    """Append findings to vulnerability database."""
    VULN_DB.parent.mkdir(parents=True, exist_ok=True)
    db = {"scans": []}
    if VULN_DB.exists():
        try: db = json.load(open(VULN_DB))
        except: pass
    db["scans"].append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "findings": findings,
        "count": len(findings)
    })
    with open(VULN_DB, "w") as f:
        json.dump(db, f, indent=2)

def print_report(findings: list, target: str):
    """Print formatted scan report."""
    critical = sum(1 for f in findings if f.get("severity") == "CRITICAL")
    high = sum(1 for f in findings if f.get("severity") == "HIGH")
    medium = sum(1 for f in findings if f.get("severity") == "MEDIUM")
    low = sum(1 for f in findings if f.get("severity") == "LOW")
    
    print(f"""
╔══════════════════════════════════════════╗
║     OpenClaw Security Scan Report        ║
╠══════════════════════════════════════════╣
║  Target: {target:<30} ║
║  Date:   {datetime.now().strftime('%Y-%m-%d %H:%M'):<30} ║
╠══════════════════════════════════════════╣
║  🔴 CRITICAL: {critical:<3}  🟠 HIGH: {high:<3}          ║
║  🟡 MEDIUM:   {medium:<3}  🔵 LOW:  {low:<3}          ║
║  📊 TOTAL:    {len(findings):<3}                        ║
╚══════════════════════════════════════════╝
""")
    
    for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]:
        sev_findings = [f for f in findings if f.get("severity") == sev]
        if not sev_findings:
            continue
        print(f"\n{'='*60}")
        print(f"  {sev}")
        print(f"{'='*60}")
        for f in sev_findings:
            print(f"  📍 {f.get('vulnerability', '?')}")
            if "file" in f: print(f"     File: {f['file']}:{f.get('line','?')}")
            if "url" in f: print(f"     URL: {f['url']}")
            if "port" in f: print(f"     Port: {f['port']} ({f.get('service','?')})")
            if "fix" in f: print(f"     Fix: {f['fix']}")


def main():
    parser = argparse.ArgumentParser(description="OpenClaw Security Scanner ⚠️ Auth required")
    sub = parser.add_subparsers(dest="cmd")
    
    sc = sub.add_parser("scan", help="Run specific scan")
    sc.add_argument("--target", required=True)
    sc.add_argument("--type", choices=["code", "deps", "web", "network"], required=True)
    
    sub.add_parser("full", help="Full scan").add_argument("--target", required=True)
    sub.add_parser("quick", help="Quick scan (code only)").add_argument("--target", required=True)
    
    args = parser.parse_args()
    
    findings = []
    target = args.target
    
    if args.cmd == "scan":
        if args.type == "code":
            findings = scan_code_patterns(target)
        elif args.type == "deps":
            findings = scan_dependencies(target)
        elif args.type == "web":
            findings = scan_web(target)
        elif args.type == "network":
            findings = scan_network(target)
    elif args.cmd == "full":
        findings.extend(scan_code_patterns(target))
        findings.extend(scan_dependencies(target))
        findings.extend(scan_network(target))
    elif args.cmd == "quick":
        findings = scan_code_patterns(target)
    
    print_report(findings, target)
    if findings:
        save_findings(findings)
        print(f"\n💾 Findings saved to {VULN_DB}")
    
    sys.exit(0 if not any(f.get("severity") == "CRITICAL" for f in findings) else 1)


if __name__ == "__main__":
    import urllib.parse
    main()
