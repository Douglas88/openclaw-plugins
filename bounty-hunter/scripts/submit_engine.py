#!/usr/bin/env python3
"""
Bounty Submission Engine — Multi-Platform Vulnerability Submission
===================================================================
Auto-format and prepare submissions for major platforms:

Platforms:
  - 360 BugCloud (补天) — https://butian.360.cn
  - CNVD — https://www.cnvd.org.cn
  - CNNVD — https://www.cnnvd.org.cn
  - CVE (MITRE) — https://cveform.mitre.org
  - NVD — https://nvd.nist.gov
  - HackerOne — https://hackerone.com
  - Bugcrowd — https://bugcrowd.com

Usage:
  python3 submit_engine.py format --finding-id 0 --platform 360
  python3 submit_engine.py format --finding-id 0 --platform cnvd
  python3 submit_engine.py batch --platform cnvd    # Batch all unsent
  python3 submit_engine.py status                    # Submission status
  python3 submit_engine.py stats                     # Statistics

Features:
1. Platform-specific formatters for each platform
2. Submission tracking database (JSON)
3. Batch submission support
4. Status tracking (draft → submitted → verified → rewarded)
5. Statistics: total submitted, accepted, rewarded, total bounty
6. Auto-validation before submission
"""

import argparse
import json
import os
import sys
import textwrap
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
FINDINGS_FILE = DATA_DIR / "findings.json"
TRACKING_FILE = DATA_DIR / "tracking.json"
SUBMISSIONS_FILE = DATA_DIR / "submissions.json"

# ---------------------------------------------------------------------------
# Platform definitions
# ---------------------------------------------------------------------------

PLATFORM_CONFIG: Dict[str, Dict[str, Any]] = {
    "360": {
        "name": "360 BugCloud (补天)",
        "url": "https://butian.360.cn",
        "language": "zh",
        "requires": ["cvss_31", "poc", "affected_versions"],
        "format": "markdown",
        "fields": [
            ("漏洞标题", "title"),
            ("漏洞类型", "vuln_type"),
            ("CVSS 3.1 评分", "cvss_score"),
            ("CVSS 3.1 向量", "cvss_vector"),
            ("受影响版本", "affected_versions"),
            ("漏洞描述", "description"),
            ("漏洞证明(PoC)", "poc"),
            ("修复建议", "remediation"),
        ],
    },
    "cnvd": {
        "name": "CNVD (国家信息安全漏洞共享平台)",
        "url": "https://www.cnvd.org.cn",
        "language": "zh",
        "requires": ["description", "affected_versions", "poc"],
        "format": "markdown",
        "fields": [
            ("漏洞名称", "title"),
            ("漏洞编号(CNVD)", "cnvd_id"),
            ("漏洞类型", "vuln_type"),
            ("危害等级", "severity"),
            ("受影响系统/软件", "affected_versions"),
            ("漏洞描述", "description"),
            ("漏洞验证(PoC)", "poc"),
            ("解决方案", "remediation"),
            ("参考链接", "references"),
        ],
        "template_header": "# CNVD漏洞提交报告\n\n",
        "severity_map": {"critical": "高", "high": "高", "medium": "中", "low": "低"},
    },
    "cnnvd": {
        "name": "CNNVD (国家信息安全漏洞库)",
        "url": "https://www.cnnvd.org.cn",
        "language": "zh",
        "requires": ["description", "severity", "cwe"],
        "format": "markdown",
        "fields": [
            ("漏洞名称", "title"),
            ("CNNVD编号", "cnnvd_id"),
            ("CWE编号", "cwe"),
            ("危害等级", "severity"),
            ("受影响产品", "affected_versions"),
            ("漏洞描述", "description"),
            ("修复措施", "remediation"),
        ],
        "severity_map": {"critical": "超危", "high": "高危", "medium": "中危", "low": "低危"},
    },
    "cve": {
        "name": "CVE (MITRE)",
        "url": "https://cveform.mitre.org",
        "language": "en",
        "requires": ["description", "affected_versions", "cwe"],
        "format": "text",
        "fields": [
            ("Vulnerability Name", "title"),
            ("CVE ID", "cve_id"),
            ("CWE ID", "cwe"),
            ("Affected Products/Versions", "affected_versions"),
            ("Description", "description"),
            ("Impact", "impact"),
            ("Remediation", "remediation"),
            ("References", "references"),
            ("Discoverer", "discoverer"),
        ],
    },
    "hackerone": {
        "name": "HackerOne",
        "url": "https://hackerone.com",
        "language": "en",
        "requires": ["description", "impact", "remediation", "poc"],
        "format": "markdown",
        "fields": [
            ("Title", "title"),
            ("Severity", "severity"),
            ("Description", "description"),
            ("Impact Statement", "impact"),
            ("Steps to Reproduce", "poc"),
            ("Remediation", "remediation"),
            ("Attachments", "attachments"),
        ],
    },
    "bugcrowd": {
        "name": "Bugcrowd",
        "url": "https://bugcrowd.com",
        "language": "en",
        "requires": ["description", "impact", "poc", "remediation"],
        "format": "markdown",
        "fields": [
            ("Title", "title"),
            ("Vulnerability Type", "vuln_type"),
            ("Priority (P1-P5)", "priority"),
            ("Description", "description"),
            ("Impact", "impact"),
            ("Steps to Reproduce", "poc"),
            ("Remediation", "remediation"),
            ("References", "references"),
        ],
    },
    "nvd": {
        "name": "NVD (National Vulnerability Database)",
        "url": "https://nvd.nist.gov",
        "language": "en",
        "requires": ["cve_id", "description", "cvss_31"],
        "format": "json",
        "fields": [
            ("CVE ID", "cve_id"),
            ("Description", "description"),
            ("CVSS 3.1 Score", "cvss_score"),
            ("CVSS 3.1 Vector", "cvss_vector"),
            ("CWE ID", "cwe"),
            ("Affected Versions", "affected_versions"),
            ("References", "references"),
        ],
    },
}

VALID_STATUSES = ["draft", "submitted", "under_review", "verified", "rewarded", "rejected"]
VALID_SEVERITIES = ["critical", "high", "medium", "low", "info"]

# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def ensure_data_dir() -> None:
    """Ensure the data directory exists."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_json(filepath: Path) -> List[Dict[str, Any]]:
    """Load a JSON file; return empty list if missing."""
    if not filepath.exists():
        return []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError) as e:
        print(f"⚠️  Warning: Could not read {filepath}: {e}", file=sys.stderr)
        return []


def save_json(filepath: Path, data: List[Dict[str, Any]]) -> None:
    """Save data to a JSON file atomically."""
    ensure_data_dir()
    tmp = filepath.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    tmp.replace(filepath)


def load_findings() -> List[Dict[str, Any]]:
    """Load findings database."""
    return load_json(FINDINGS_FILE)


def load_submissions() -> List[Dict[str, Any]]:
    """Load submissions database."""
    return load_json(SUBMISSIONS_FILE)


def save_submissions(data: List[Dict[str, Any]]) -> None:
    """Save submissions database."""
    save_json(SUBMISSIONS_FILE, data)


def get_finding(finding_id: int) -> Optional[Dict[str, Any]]:
    """Get a single finding by its index."""
    findings = load_findings()
    if 0 <= finding_id < len(findings):
        return findings[finding_id]
    return None


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_finding(finding: Dict[str, Any], platform: str) -> Tuple[bool, List[str]]:
    """Validate that a finding has all required fields for a platform."""
    cfg = PLATFORM_CONFIG.get(platform)
    if not cfg:
        return False, [f"Unknown platform: {platform}"]

    errors: List[str] = []
    required = cfg.get("requires", [])

    # Check required fields
    for req in required:
        if req == "poc" and not finding.get("poc") and not finding.get("steps_to_reproduce"):
            errors.append("Missing PoC / steps to reproduce")
        elif req == "cvss_31":
            if not finding.get("cvss_score") or not finding.get("cvss_vector"):
                errors.append("Missing CVSS 3.1 score or vector")
        elif req == "cwe" and not finding.get("cwe"):
            errors.append("Missing CWE mapping")
        elif req == "affected_versions" and not finding.get("affected_versions"):
            errors.append("Missing affected versions")
        elif req == "description" and not finding.get("description"):
            errors.append("Missing vulnerability description")
        elif req == "impact" and not finding.get("impact"):
            errors.append("Missing impact statement")
        elif req == "remediation" and not finding.get("remediation"):
            errors.append("Missing remediation steps")
        elif req == "severity" and finding.get("severity", "") not in VALID_SEVERITIES:
            errors.append(f"Invalid severity: {finding.get('severity', '')}")

    # Check title
    if not finding.get("title"):
        errors.append("Missing title")

    return len(errors) == 0, errors


# ---------------------------------------------------------------------------
# Formatters
# ---------------------------------------------------------------------------

def format_360(finding: Dict[str, Any]) -> str:
    """Format finding for 360 BugCloud submission."""
    lines = ["# 漏洞提交报告 — 360补天平台", ""]
    lines.append(f"**漏洞标题:** {finding.get('title', 'N/A')}")
    lines.append(f"**漏洞类型:** {finding.get('vuln_type', 'N/A')}")
    lines.append(f"**CVSS 3.1 评分:** {finding.get('cvss_score', 'N/A')}")
    lines.append(f"**CVSS 3.1 向量:** {finding.get('cvss_vector', 'N/A')}")
    lines.append("")
    lines.append("## 受影响版本")
    versions = finding.get("affected_versions", "N/A")
    if isinstance(versions, list):
        for v in versions:
            lines.append(f"- {v}")
    else:
        lines.append(str(versions))
    lines.append("")
    lines.append("## 漏洞描述")
    lines.append(finding.get("description", "N/A"))
    lines.append("")
    lines.append("## 漏洞证明 (PoC)")
    lines.append(f"```\n{finding.get('poc', finding.get('steps_to_reproduce', 'N/A'))}\n```")
    lines.append("")
    lines.append("## 修复建议")
    lines.append(finding.get("remediation", "N/A"))
    return "\n".join(lines)


def format_cnvd(finding: Dict[str, Any]) -> str:
    """Format finding for CNVD submission."""
    severity_map = {"critical": "高", "high": "高", "medium": "中", "low": "低"}
    severity = severity_map.get(finding.get("severity", "medium"), "中")

    lines = ["# CNVD漏洞提交报告", ""]
    lines.append(f"**漏洞名称:** {finding.get('title', 'N/A')}")
    lines.append(f"**漏洞编号(CNVD):** {finding.get('cnvd_id', '待分配')}")
    lines.append(f"**漏洞类型:** {finding.get('vuln_type', 'N/A')}")
    lines.append(f"**危害等级:** {severity}")
    lines.append("")
    lines.append("## 受影响系统/软件")
    versions = finding.get("affected_versions", "N/A")
    if isinstance(versions, list):
        for v in versions:
            lines.append(f"- {v}")
    else:
        lines.append(str(versions))
    lines.append("")
    lines.append("## 漏洞描述")
    lines.append(finding.get("description", "N/A"))
    lines.append("")
    lines.append("## 漏洞验证 (PoC)")
    lines.append(finding.get("poc", finding.get("steps_to_reproduce", "N/A")))
    lines.append("")
    lines.append("## 解决方案")
    lines.append(finding.get("remediation", "N/A"))
    lines.append("")
    refs = finding.get("references", "")
    if refs:
        lines.append("## 参考链接")
        if isinstance(refs, list):
            for r in refs:
                lines.append(f"- {r}")
        else:
            lines.append(str(refs))
    return "\n".join(lines)


def format_cnnvd(finding: Dict[str, Any]) -> str:
    """Format finding for CNNVD submission."""
    severity_map = {"critical": "超危", "high": "高危", "medium": "中危", "low": "低危"}
    severity = severity_map.get(finding.get("severity", "medium"), "中危")

    lines = ["# CNNVD漏洞提交报告", ""]
    lines.append(f"**漏洞名称:** {finding.get('title', 'N/A')}")
    lines.append(f"**CNNVD编号:** {finding.get('cnnvd_id', '待分配')}")
    lines.append(f"**CWE编号:** {finding.get('cwe', '待定')}")
    lines.append(f"**危害等级:** {severity}")
    lines.append("")
    lines.append("## 受影响产品")
    versions = finding.get("affected_versions", "N/A")
    if isinstance(versions, list):
        for v in versions:
            lines.append(f"- {v}")
    else:
        lines.append(str(versions))
    lines.append("")
    lines.append("## 漏洞描述")
    lines.append(finding.get("description", "N/A"))
    lines.append("")
    lines.append("## 修复措施")
    lines.append(finding.get("remediation", "N/A"))
    return "\n".join(lines)


def format_cve(finding: Dict[str, Any]) -> str:
    """Format finding for CVE (MITRE) submission."""
    lines = ["=== CVE VULNERABILITY SUBMISSION ===", ""]
    lines.append(f"Vulnerability Name: {finding.get('title', 'N/A')}")
    lines.append(f"CVE ID: {finding.get('cve_id', 'Reserved')}")
    lines.append(f"CWE ID: {finding.get('cwe', 'TBD')}")
    lines.append(f"Product: {finding.get('product', 'N/A')}")
    lines.append(f"Vendor: {finding.get('vendor', 'N/A')}")
    lines.append("")
    versions = finding.get("affected_versions", "N/A")
    if isinstance(versions, list):
        lines.append("Affected Versions:")
        for v in versions:
            lines.append(f"  - {v}")
    else:
        lines.append(f"Affected Versions: {versions}")
    lines.append("")
    lines.append(f"Description:\n{finding.get('description', 'N/A')}")
    lines.append("")
    lines.append(f"Impact:\n{finding.get('impact', 'N/A')}")
    lines.append("")
    lines.append(f"Remediation:\n{finding.get('remediation', 'N/A')}")
    lines.append("")
    refs = finding.get("references", [])
    if refs:
        lines.append("References:")
        for r in (refs if isinstance(refs, list) else [refs]):
            lines.append(f"  - {r}")
    lines.append("")
    lines.append(f"Discoverer: {finding.get('discoverer', 'Anonymous')}")
    return "\n".join(lines)


def format_hackerone(finding: Dict[str, Any]) -> str:
    """Format finding for HackerOne submission."""
    lines = ["## Summary", ""]
    lines.append(finding.get("description", "N/A"))
    lines.append("")
    lines.append("## Steps to Reproduce")
    lines.append("")
    lines.append(finding.get("poc", finding.get("steps_to_reproduce", "N/A")))
    lines.append("")
    lines.append("## Impact")
    lines.append("")
    lines.append(finding.get("impact", "N/A"))
    lines.append("")
    lines.append("## Remediation")
    lines.append("")
    lines.append(finding.get("remediation", "N/A"))
    return "\n".join(lines)


def format_bugcrowd(finding: Dict[str, Any]) -> str:
    """Format finding for Bugcrowd submission."""
    lines = ["## Vulnerability Details", ""]
    lines.append(f"**Vulnerability Type:** {finding.get('vuln_type', 'N/A')}")
    priority = finding.get("priority", "P3")
    lines.append(f"**Priority:** {priority}")
    lines.append("")
    lines.append("### Description")
    lines.append(finding.get("description", "N/A"))
    lines.append("")
    lines.append("### Impact")
    lines.append(finding.get("impact", "N/A"))
    lines.append("")
    lines.append("### Steps to Reproduce")
    lines.append(finding.get("poc", finding.get("steps_to_reproduce", "N/A")))
    lines.append("")
    lines.append("### Remediation")
    lines.append(finding.get("remediation", "N/A"))
    lines.append("")
    refs = finding.get("references", [])
    if refs:
        lines.append("### References")
        for r in (refs if isinstance(refs, list) else [refs]):
            lines.append(f"- {r}")
    return "\n".join(lines)


def format_nvd(finding: Dict[str, Any]) -> str:
    """Format finding as NVD JSON submission."""
    payload = {
        "cve_id": finding.get("cve_id", ""),
        "description": finding.get("description", ""),
        "cvss_v31": {
            "score": finding.get("cvss_score", 0.0),
            "vector": finding.get("cvss_vector", ""),
        },
        "cwe_id": finding.get("cwe", ""),
        "affected_versions": finding.get("affected_versions", []),
        "references": finding.get("references", []),
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


FORMATTERS: Dict[str, callable] = {
    "360": format_360,
    "cnvd": format_cnvd,
    "cnnvd": format_cnnvd,
    "cve": format_cve,
    "hackerone": format_hackerone,
    "bugcrowd": format_bugcrowd,
    "nvd": format_nvd,
}

# ---------------------------------------------------------------------------
# Submission tracking
# ---------------------------------------------------------------------------

def find_submission(finding_id: int, platform: str) -> Optional[Dict[str, Any]]:
    """Find existing submission for a finding + platform combo."""
    submissions = load_submissions()
    for sub in submissions:
        if sub.get("finding_id") == finding_id and sub.get("platform") == platform:
            return sub
    return None


def record_submission(
    finding_id: int,
    platform: str,
    status: str = "submitted",
    output_file: Optional[str] = None,
) -> Dict[str, Any]:
    """Record a new submission entry."""
    submissions = load_submissions()

    # Check for duplicate
    existing = find_submission(finding_id, platform)
    if existing:
        existing["status"] = status
        existing["updated_at"] = datetime.now(timezone.utc).isoformat()
        existing["output_file"] = output_file or existing.get("output_file")
        save_submissions(submissions)
        return existing

    entry: Dict[str, Any] = {
        "id": len(submissions) + 1,
        "finding_id": finding_id,
        "platform": platform,
        "platform_name": PLATFORM_CONFIG.get(platform, {}).get("name", platform),
        "status": status,
        "output_file": output_file,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    submissions.append(entry)
    save_submissions(submissions)
    return entry


def update_submission_status(submission_id: int, status: str) -> bool:
    """Update the status of a submission."""
    if status not in VALID_STATUSES:
        print(f"❌ Invalid status: {status}. Valid: {', '.join(VALID_STATUSES)}")
        return False

    submissions = load_submissions()
    for sub in submissions:
        if sub.get("id") == submission_id:
            sub["status"] = status
            sub["updated_at"] = datetime.now(timezone.utc).isoformat()
            save_submissions(submissions)
            return True
    print(f"❌ Submission with ID {submission_id} not found.")
    return False


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_format(args: argparse.Namespace) -> int:
    """Format a finding for a specific platform."""
    finding = get_finding(args.finding_id)
    if not finding:
        print(f"❌ Finding {args.finding_id} not found.")
        return 1

    platform = args.platform.lower()
    if platform not in PLATFORM_CONFIG:
        print(f"❌ Unknown platform: {platform}")
        print(f"   Available: {', '.join(PLATFORM_CONFIG.keys())}")
        return 1

    # Validate
    valid, errors = validate_finding(finding, platform)
    if not valid and not args.no_validate:
        print("⚠️  Validation warnings:")
        for err in errors:
            print(f"   - {err}")
        if not args.force:
            print("\n💡 Use --force to bypass validation, or --no-validate to skip.")
            return 1

    # Format
    formatter = FORMATTERS.get(platform)
    result = formatter(finding)

    # Save output
    output_dir = DATA_DIR / "formatted"
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    title_slug = (finding.get("title", "untitled")[:30]
                  .replace(" ", "_").replace("/", "_"))
    out_path = output_dir / f"{platform}_{title_slug}_{ts}.md"
    out_path.write_text(result, encoding="utf-8")

    # Record submission
    record_submission(args.finding_id, platform, "draft", str(out_path))

    print(f"✅ Finding #{args.finding_id} formatted for {PLATFORM_CONFIG[platform]['name']}")
    print(f"📄 Output: {out_path}")
    print(f"\n{'─' * 60}")
    print(result)
    print(f"{'─' * 60}")
    return 0


def cmd_batch(args: argparse.Namespace) -> int:
    """Batch format all unsent findings for a platform."""
    findings = load_findings()
    if not findings:
        print("📭 No findings found. Run security scanner first.")
        return 1

    platform = args.platform.lower()
    if platform not in PLATFORM_CONFIG:
        print(f"❌ Unknown platform: {platform}")
        return 1

    submissions = load_submissions()
    submitted_ids = {
        s["finding_id"] for s in submissions
        if s["platform"] == platform and s["status"] != "draft"
    }

    batch_results: List[Dict[str, Any]] = []
    for idx, finding in enumerate(findings):
        if idx in submitted_ids and not args.resubmit:
            continue

        valid, errors = validate_finding(finding, platform)
        if not valid and not args.force:
            print(f"⏭️  Skipping finding #{idx}: {errors[0]}")
            continue

        formatter = FORMATTERS.get(platform)
        result = formatter(finding)

        output_dir = DATA_DIR / "formatted"
        output_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        title_slug = (finding.get("title", "untitled")[:30]
                      .replace(" ", "_").replace("/", "_"))
        out_path = output_dir / f"{platform}_batch_{idx}_{title_slug}_{ts}.md"
        out_path.write_text(result, encoding="utf-8")

        entry = record_submission(idx, platform, "submitted", str(out_path))
        batch_results.append({"finding_id": idx, "status": "submitted", "file": str(out_path)})

    print(f"✅ Batch complete: {len(batch_results)} submissions prepared for {PLATFORM_CONFIG[platform]['name']}")
    for r in batch_results:
        print(f"   Finding #{r['finding_id']} → {r['file']}")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    """Show submission status overview."""
    submissions = load_submissions()

    if not submissions:
        print("📭 No submissions recorded yet.")
        return 0

    # Filter by platform
    if args.platform:
        platform = args.platform.lower()
        submissions = [s for s in submissions if s.get("platform") == platform]

    if args.detail:
        print(f"\n{'=' * 80}")
        print(f"  SUBMISSION DETAIL — {len(submissions)} total")
        print(f"{'=' * 80}\n")
        for sub in submissions:
            s_id = sub.get("id", "?")
            f_id = sub.get("finding_id", "?")
            plat = sub.get("platform_name", sub.get("platform", "?"))
            status = sub.get("status", "?")
            updated = sub.get("updated_at", "?")[:19]
            out = sub.get("output_file", "N/A")

            status_icon = {"draft": "📝", "submitted": "📤", "under_review": "🔍",
                           "verified": "✅", "rewarded": "💰", "rejected": "❌"}.get(status, "❓")

            print(f"  {status_icon} [{s_id}] Finding #{f_id} → {plat}")
            print(f"     Status: {status} | Updated: {updated}")
            print(f"     File: {out}")
            print()
    else:
        # Summary table
        status_counts: Dict[str, int] = {}
        for s in submissions:
            st = s.get("status", "unknown")
            status_counts[st] = status_counts.get(st, 0) + 1

        print(f"\n{'Submission Status Overview':─^60}")
        print(f"  Total submissions: {len(submissions)}")
        print()
        for st in VALID_STATUSES:
            cnt = status_counts.get(st, 0)
            bar = "█" * min(cnt * 2, 40)
            print(f"  {st:>15s} [{cnt:>3d}] {bar}")
        print()

    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    """Show statistics dashboard."""
    submissions = load_submissions()
    findings = load_findings()

    if not submissions:
        print("📭 No submission data available for statistics.")
        return 0

    total = len(submissions)
    submitted = sum(1 for s in submissions if s.get("status") in ("submitted", "under_review", "verified", "rewarded"))
    verified = sum(1 for s in submissions if s.get("status") == "verified")
    rewarded = sum(1 for s in submissions if s.get("status") == "rewarded")
    rejected = sum(1 for s in submissions if s.get("status") == "rejected")
    acceptance_rate = (verified + rewarded) / submitted * 100 if submitted > 0 else 0

    # Per-platform stats
    platform_stats: Dict[str, Dict[str, int]] = {}
    for s in submissions:
        plat = s.get("platform", "unknown")
        if plat not in platform_stats:
            platform_stats[plat] = {"total": 0, "rewarded": 0}
        platform_stats[plat]["total"] += 1
        if s.get("status") == "rewarded":
            platform_stats[plat]["rewarded"] += 1

    print(f"\n{' Bounty Hunter Statistics ':═^60}")
    print(f"  Findings in database: {len(findings)}")
    print(f"  Total submissions:    {total}")
    print(f"  Submitted:            {submitted}")
    print(f"  Verified:             {verified}")
    print(f"  Rewarded:             {rewarded}")
    print(f"  Rejected:             {rejected}")
    print(f"  Acceptance rate:      {acceptance_rate:.1f}%")
    print()
    print(f"{' Platform Breakdown ':─^60}")
    for plat in sorted(platform_stats.keys()):
        ps = platform_stats[plat]
        name = PLATFORM_CONFIG.get(plat, {}).get("name", plat)
        print(f"  {name:40s}  {ps['total']:>3d} submissions  ({ps['rewarded']} rewarded)")
    print()

    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate a finding against platform requirements."""
    finding = get_finding(args.finding_id)
    if not finding:
        print(f"❌ Finding {args.finding_id} not found.")
        return 1

    if args.platform:
        platforms = [args.platform.lower()]
    else:
        platforms = list(PLATFORM_CONFIG.keys())

    all_good = True
    for plat in platforms:
        if plat not in PLATFORM_CONFIG:
            print(f"❌ Unknown platform: {plat}")
            all_good = False
            continue
        valid, errors = validate_finding(finding, plat)
        name = PLATFORM_CONFIG[plat]["name"]
        if valid:
            print(f"✅ {name}: Ready for submission")
        else:
            print(f"❌ {name}: {len(errors)} issue(s)")
            for err in errors:
                print(f"   - {err}")
            all_good = False

    return 0 if all_good else 1


def cmd_platforms(args: argparse.Namespace) -> int:
    """List supported platforms with requirements."""
    print(f"\n{' Supported Platforms ':═^60}")
    for key, cfg in sorted(PLATFORM_CONFIG.items()):
        print(f"\n  [{key}] {cfg['name']}")
        print(f"      URL:      {cfg['url']}")
        print(f"      Language: {cfg['language']}")
        print(f"      Format:   {cfg['format']}")
        print(f"      Requires: {', '.join(cfg['requires'])}")
    print()
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        prog="submit_engine",
        description="Multi-Platform Vulnerability Submission Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
        Examples:
          submit_engine format --finding-id 0 --platform cnvd
          submit_engine format --finding-id 0 --platform hackerone -f
          submit_engine batch --platform cnvd
          submit_engine batch --platform 360 --resubmit
          submit_engine status
          submit_engine status --platform cnvd --detail
          submit_engine stats
          submit_engine validate --finding-id 0
          submit_engine validate --finding-id 0 --platform cve
          submit_engine platforms
        """),
    )
    sub = parser.add_subparsers(dest="command", help="Available commands")

    # ---------- format ----------
    p_fmt = sub.add_parser("format", help="Format a finding for a platform")
    p_fmt.add_argument("--finding-id", "-fid", type=int, required=True,
                       help="Index of finding in findings.json")
    p_fmt.add_argument("--platform", "-p", type=str, required=True,
                       help="Target platform (360, cnvd, cnnvd, cve, hackerone, bugcrowd, nvd)")
    p_fmt.add_argument("--force", "-f", action="store_true",
                       help="Force format even with validation errors")
    p_fmt.add_argument("--no-validate", action="store_true",
                       help="Skip validation entirely")

    # ---------- batch ----------
    p_batch = sub.add_parser("batch", help="Batch format all unsent findings")
    p_batch.add_argument("--platform", "-p", type=str, required=True,
                         help="Target platform")
    p_batch.add_argument("--force", "-f", action="store_true",
                         help="Force format even with validation errors")
    p_batch.add_argument("--resubmit", action="store_true",
                         help="Re-submit even previously submitted findings")

    # ---------- status ----------
    p_stat = sub.add_parser("status", help="Show submission status")
    p_stat.add_argument("--platform", "-p", type=str, default=None,
                        help="Filter by platform")
    p_stat.add_argument("--detail", "-d", action="store_true",
                        help="Show detailed status for each submission")

    # ---------- stats ----------
    sub.add_parser("stats", help="Show submission statistics")

    # ---------- validate ----------
    p_val = sub.add_parser("validate", help="Validate a finding against platform(s)")
    p_val.add_argument("--finding-id", "-fid", type=int, required=True,
                       help="Index of finding")
    p_val.add_argument("--platform", "-p", type=str, default=None,
                       help="Specific platform to validate (omit to validate all)")

    # ---------- platforms ----------
    sub.add_parser("platforms", help="List supported platforms and requirements")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    command_handlers = {
        "format": cmd_format,
        "batch": cmd_batch,
        "status": cmd_status,
        "stats": cmd_stats,
        "validate": cmd_validate,
        "platforms": cmd_platforms,
    }

    handler = command_handlers.get(args.command)
    if handler:
        return handler(args)
    else:
        print(f"❌ Unknown command: {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
