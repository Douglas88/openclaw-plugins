---
name: security-scanner
description: Automated vulnerability discovery engine — code patterns, dependency CVEs, web vulnerabilities, network scanning. Use when: (1) scanning project for security flaws, (2) daily automated pentest, (3) pre-deployment security audit, (4) finding vulnerabilities for responsible disclosure. ⚠️ Only scan targets you own or have explicit permission. Supports CVE/CNVD report generation.
version: "1.0.0"
---

# Security Scanner — Automated Vulnerability Discovery

Multi-layer scanning: code patterns → dependencies → web → network.

## Quick Start

```bash
# Scan your own project for code vulnerabilities
python3 scripts/security_scanner.py scan --target ./src --type code

# Check dependencies for known CVEs
python3 scripts/security_scanner.py scan --target ./project --type deps

# Full scan (all layers)
python3 scripts/security_scanner.py full --target ./my_project

# Quick scan (code only, fastest)
python3 scripts/security_scanner.py quick --target ./src
```

## Scan Types

| Type | What it checks | Speed |
|------|---------------|-------|
| `code` | SQL injection, XSS, command injection, hardcoded secrets, path traversal, SSRF, insecure deserialization | Fast |
| `deps` | Outdated packages, known CVEs (npm audit / pip list) | Slow |
| `web` | SQLi/XSS payloads, missing security headers | Medium |
| `network` | Open ports, service detection (22,80,443,3306,etc) | Medium |

## Vulnerability Database

Findings saved to `~/.openclaw/vuln_findings.json` for tracking and reporting.

## Ethical Guidelines ⚠️

1. **ONLY scan targets you OWN or have WRITTEN PERMISSION to test**
2. Never scan targets without authorization — it's ILLEGAL
3. If you find vulnerabilities in third-party software:
   - Contact the vendor privately first
   - Follow responsible disclosure (90-day policy)
   - Use vuln-reporter skill to generate proper CVE/CNVD reports
4. Never exploit vulnerabilities for unauthorized access
5. Compliance with local laws (CISA, CNCERT, etc.)

## Workflow

```
Daily Scan → Find vulnerabilities → Validate (no exploitation)
    ↓
Generate Report (vuln-reporter) → Submit to vendor/CVE/CNVD
    ↓
Track in vuln_findings.json → Re-scan after patch
```
