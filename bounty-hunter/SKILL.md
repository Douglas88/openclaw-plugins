---
name: bounty-hunter
description: Automated vulnerability bounty hunting — scan, report, submit, track rewards. Use when: (1) automated pentesting workflow, (2) submitting vulnerabilities to 360/CNVD/CVE/HackerOne, (3) tracking bug bounty rewards, (4) managing vulnerability disclosure pipeline. Integrates security-scanner + vuln-reporter + submit_engine + bounty_tracker.
version: "1.0.0"
---

# Bounty Hunter — Automated Vulnerability Bounty Pipeline

Fully automated pipeline: **Scan → Validate → Report → Submit → Track → Reward**.

## Pipeline Overview

```
┌──────────┐    ┌───────────┐    ┌───────────┐    ┌───────────┐
│  SCAN    │ → │ VALIDATE  │ → │  FORMAT   │ → │  SUBMIT   │
│scanner.py│    │ findings  │    │per-platform│    │engine.py  │
└──────────┘    └───────────┘    └───────────┘    └───────────┘
     │                                                │
     ▼                                                ▼
┌──────────┐                                    ┌───────────┐
│  REPORT  │                                    │   TRACK   │
│reporter  │                                    │ tracker.py│
└──────────┘                                    └───────────┘
                                                     │
                                                     ▼
                                               ┌───────────┐
                                               │  REWARD   │
                                               │  dashboard│
                                               └───────────┘
```

## Daily Auto-Hunt

Set up a cron job to run the full pipeline daily at 06:00:

```bash
openclaw cron add --name "daily-bounty-hunt" \
  --schedule '{"kind":"cron","expr":"0 6 * * *","tz":"Asia/Shanghai"}' \
  --payload '{"kind":"systemEvent","text":"Run full bounty hunting pipeline: scan, validate, submit, track"}' \
  --enabled true
```

The pipeline:
1. **06:00** — Security scanner runs against configured targets
2. Findings auto-validated for completeness (PoC, CVSS, affected versions)
3. New findings formatted per platform requirements
4. Batch submissions prepared for all configured platforms
5. Tracking database updated with status
6. Dashboard refreshed with latest stats

## Supported Platforms

| Platform | Key | Language | URL | Requirements |
|----------|-----|----------|-----|-------------|
| 360 BugCloud (补天) | `360` | 中文 | https://butian.360.cn | CVSS 3.1, PoC, affected versions |
| CNVD | `cnvd` | 中文 | https://www.cnvd.org.cn | Description, affected versions, PoC |
| CNNVD | `cnnvd` | 中文 | https://www.cnnvd.org.cn | Description, severity, CWE |
| CVE (MITRE) | `cve` | English | https://cveform.mitre.org | Description, affected versions, CWE |
| NVD | `nvd` | English | https://nvd.nist.gov | CVE ID, description, CVSS 3.1 |
| HackerOne | `hackerone` | English | https://hackerone.com | Description, impact, remediation, PoC |
| Bugcrowd | `bugcrowd` | English | https://bugcrowd.com | Description, impact, PoC, remediation |

## Format Matrix

Each platform requires specific formatting:

- **360 / CNVD / CNNVD**: Markdown reports in Chinese with severity mapping
- **CVE**: Plain text with CWE mapping, vendor info, discoverer attribution
- **NVD**: JSON payload with CVSS 3.1 vectors
- **HackerOne**: Markdown with Summary / Steps to Reproduce / Impact / Remediation sections
- **Bugcrowd**: Markdown with Priority (P1–P5) and full vulnerability details

## Status Flow

```
draft → submitted → under_review → verified → rewarded
                                    ↘ rejected
```

## Commands Quick Reference

### Submit Engine (`scripts/submit_engine.py`)

```bash
# Format a specific finding for a platform
python3 scripts/submit_engine.py format --finding-id 0 --platform cnvd

# Force format (skip validation)
python3 scripts/submit_engine.py format --finding-id 0 --platform hackerone -f

# Batch all unsent findings
python3 scripts/submit_engine.py batch --platform cnvd

# Check submission status
python3 scripts/submit_engine.py status
python3 scripts/submit_engine.py status --platform cnvd --detail

# View statistics
python3 scripts/submit_engine.py stats

# Validate a finding
python3 scripts/submit_engine.py validate --finding-id 0
python3 scripts/submit_engine.py validate --finding-id 0 --platform cve

# List supported platforms
python3 scripts/submit_engine.py platforms
```

### Bounty Tracker (`scripts/bounty_tracker.py`)

```bash
# Add a tracking entry
python3 scripts/bounty_tracker.py add --finding-id 0 --platform 360 --status submitted

# Update with reward info
python3 scripts/bounty_tracker.py update --track-id 1 --status rewarded --reward 5000 --currency CNY

# List all entries
python3 scripts/bounty_tracker.py list
python3 scripts/bounty_tracker.py list --status rewarded --platform hackerone

# Dashboard with stats
python3 scripts/bounty_tracker.py dashboard

# Export to CSV
python3 scripts/bounty_tracker.py export --format csv --output rewards.csv

# Today's summary
python3 scripts/bounty_tracker.py summary
```

## Example Full Workflow

```bash
# 1. Scan targets (via security-scanner skill)
python3 scripts/submit_engine.py validate --finding-id 0

# 2. Format for Chinese platforms
python3 scripts/submit_engine.py format --finding-id 0 --platform 360
python3 scripts/submit_engine.py format --finding-id 0 --platform cnvd

# 3. Format for international platforms
python3 scripts/submit_engine.py format --finding-id 0 --platform hackerone
python3 scripts/submit_engine.py format --finding-id 0 --platform cve

# 4. Track submissions
python3 scripts/bounty_tracker.py add --finding-id 0 --platform 360 --status submitted
python3 scripts/bounty_tracker.py add --finding-id 0 --platform cnvd --status submitted
python3 scripts/bounty_tracker.py add --finding-id 0 --platform hackerone --status submitted

# 5. Update as they progress
python3 scripts/bounty_tracker.py update --track-id 1 --status verified
python3 scripts/bounty_tracker.py update --track-id 1 --status rewarded --reward 8000 --currency CNY

# 6. Check dashboard
python3 scripts/bounty_tracker.py dashboard
```

## Ethical Guidelines

1. **Responsible Disclosure**: Always allow vendors a 90-day remediation window before public disclosure
2. **Authorization**: Only test systems you have explicit permission to test
3. **Privacy**: Do not exfiltrate or store user data discovered during testing
4. **Legal Compliance**: Follow CNVD/CNNVD/CVE disclosure policies and local cybersecurity laws
5. **Platform Rules**: Adhere to each platform's terms of service and code of conduct
6. **No Extortion**: Never use vulnerability information for extortion or blackmail

## Data Files

All data stored under `data/` directory:

| File | Purpose |
|------|---------|
| `data/findings.json` | Vulnerability findings from scanner |
| `data/submissions.json` | Formatted submissions per platform |
| `data/tracking.json` | Reward and status tracking database |
| `data/formatted/` | Output directory for formatted submissions |

## Integration with Other Skills

- **security-scanner**: Feed scan results into findings database
- **vuln-reporter**: Generate detailed vulnerability reports that populate findings
- **taskflow**: Orchestrate end-to-end pipeline with retry logic
- **cron**: Schedule daily auto-hunt at 06:00

## Reward Tracking

The dashboard provides:

- Total submissions, acceptance rate, and reward totals
- Per-platform breakdown of rewards earned
- Monthly reward timeline with bar charts
- Status distribution across the pipeline
- CSV export for accounting and tax purposes

### Reward Flow

```
Vulnerability Found → Submitted → Under Review → Verified → PAID 💰
```

When a reward is received, record it:

```bash
python3 scripts/bounty_tracker.py update --track-id 1 --status rewarded \
  --reward 5000 --currency CNY --paid-at 2026-05-16
```

The dashboard will automatically aggregate all rewards by platform and month.
