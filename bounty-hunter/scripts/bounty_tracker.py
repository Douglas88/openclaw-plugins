#!/usr/bin/env python3
"""
Bounty Tracker — Track vulnerability submissions and rewards
=============================================================
Usage:
  python3 bounty_tracker.py add --finding-id 0 --platform 360 --status submitted
  python3 bounty_tracker.py update --track-id 1 --status rewarded --reward 5000 --currency CNY
  python3 bounty_tracker.py list                          # All submissions
  python3 bounty_tracker.py dashboard                      # Stats dashboard
  python3 bounty_tracker.py export --format csv            # Export as CSV

Features:
1. Track each submission: platform, date, status, reward, reporter
2. Dashboard: total submissions, acceptance rate, total rewards, pending
3. CSV export for accounting
4. Status: draft → submitted → under_review → verified → rewarded → rejected
5. Reward tracking: amount, currency (CNY/USD), payment date
6. Statistics: most rewarding platforms, best month, acceptance rate
"""

import argparse
import csv
import json
import os
import sys
import textwrap
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
TRACKING_FILE = DATA_DIR / "tracking.json"

VALID_STATUSES = ["draft", "submitted", "under_review", "verified", "rewarded", "rejected"]
VALID_CURRENCIES = ["CNY", "USD", "EUR", "GBP"]

PLATFORM_NAMES = {
    "360": "360 BugCloud (补天)",
    "cnvd": "CNVD",
    "cnnvd": "CNNVD",
    "cve": "CVE (MITRE)",
    "hackerone": "HackerOne",
    "bugcrowd": "Bugcrowd",
    "nvd": "NVD",
}

STATUS_ICONS = {
    "draft": "📝",
    "submitted": "📤",
    "under_review": "🔍",
    "verified": "✅",
    "rewarded": "💰",
    "rejected": "❌",
}

STATUS_ORDER = ["draft", "submitted", "under_review", "verified", "rewarded", "rejected"]

# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def ensure_data_dir() -> None:
    """Ensure the data directory exists."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_tracking() -> List[Dict[str, Any]]:
    """Load tracking database."""
    if not TRACKING_FILE.exists():
        return []
    try:
        with open(TRACKING_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError) as e:
        print(f"⚠️  Warning: Could not read tracking.json: {e}", file=sys.stderr)
        return []


def save_tracking(data: List[Dict[str, Any]]) -> None:
    """Save tracking database atomically."""
    ensure_data_dir()
    tmp = TRACKING_FILE.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    tmp.replace(TRACKING_FILE)


def get_next_id(entries: List[Dict[str, Any]]) -> int:
    """Get the next tracking ID."""
    if not entries:
        return 1
    return max(e.get("id", 0) for e in entries) + 1


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_add(args: argparse.Namespace) -> int:
    """Add a new tracking entry."""
    entries = load_tracking()

    if args.status not in VALID_STATUSES:
        print(f"❌ Invalid status: {args.status}")
        print(f"   Valid: {', '.join(VALID_STATUSES)}")
        return 1

    entry: Dict[str, Any] = {
        "id": get_next_id(entries),
        "finding_id": args.finding_id,
        "platform": args.platform,
        "platform_name": PLATFORM_NAMES.get(args.platform, args.platform),
        "status": args.status,
        "title": args.title or "",
        "reporter": args.reporter or "",
        "submitted_at": args.submitted_at or datetime.now(timezone.utc).isoformat()[:19],
        "reward_amount": None,
        "reward_currency": None,
        "reward_paid_at": None,
        "notes": args.notes or "",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    entries.append(entry)
    save_tracking(entries)

    icon = STATUS_ICONS.get(args.status, "📌")
    print(f"{icon} Tracking entry #{entry['id']} created")
    print(f"   Finding: #{args.finding_id} → {PLATFORM_NAMES.get(args.platform, args.platform)}")
    print(f"   Status:  {args.status}")
    return 0


def cmd_update(args: argparse.Namespace) -> int:
    """Update an existing tracking entry."""
    entries = load_tracking()

    # Find entry
    target = None
    for e in entries:
        if e.get("id") == args.track_id:
            target = e
            break

    if not target:
        print(f"❌ Tracking entry #{args.track_id} not found.")
        return 1

    # Update fields
    if args.status:
        if args.status not in VALID_STATUSES:
            print(f"❌ Invalid status: {args.status}")
            return 1
        target["status"] = args.status

        # Automatically set rewarded date
        if args.status == "rewarded" and not target.get("reward_paid_at"):
            target["reward_paid_at"] = datetime.now(timezone.utc).isoformat()[:19]

    if args.title:
        target["title"] = args.title
    if args.reporter:
        target["reporter"] = args.reporter
    if args.submitted_at:
        target["submitted_at"] = args.submitted_at
    if args.reward is not None:
        target["reward_amount"] = args.reward
    if args.currency:
        if args.currency.upper() not in VALID_CURRENCIES:
            print(f"❌ Invalid currency: {args.currency}")
            return 1
        target["reward_currency"] = args.currency.upper()
    if args.paid_at:
        target["reward_paid_at"] = args.paid_at
    if args.notes is not None:
        target["notes"] = args.notes

    target["updated_at"] = datetime.now(timezone.utc).isoformat()
    save_tracking(entries)

    icon = STATUS_ICONS.get(target.get("status", ""), "📌")
    print(f"{icon} Tracking entry #{args.track_id} updated")
    if args.status:
        print(f"   Status: {args.status}")
    if args.reward is not None:
        print(f"   Reward: {args.reward} {args.currency or target.get('reward_currency', '')}")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    """List all tracking entries."""
    entries = load_tracking()

    # Filter by status
    if args.status:
        entries = [e for e in entries if e.get("status") == args.status]
    # Filter by platform
    if args.platform:
        entries = [e for e in entries if e.get("platform") == args.platform.lower()]

    if not entries:
        print("📭 No tracking entries found.")
        return 0

    # Sort by ID
    entries.sort(key=lambda e: e.get("id", 0))

    header = f"  {'ID':>4s} {'Status':>13s} | {'Platform':<20s} | {'Finding':>7s} | {'Reward':>10s} | {'Title'}"
    print(f"\n  Bounty Tracking — {len(entries)} entries\n")
    print(header)
    print("  " + "─" * (len(header) - 2))

    for e in entries:
        eid = e.get("id", "?")
        status = e.get("status", "?")
        icon = STATUS_ICONS.get(status, "📌")
        platform_name = e.get("platform_name", e.get("platform", "?"))[:20]
        fid = f"#{e.get('finding_id', '?')}"
        reward_str = ""
        if e.get("reward_amount"):
            currency = e.get("reward_currency", "")
            reward_str = f"{e['reward_amount']:,.0f} {currency}"
        title = (e.get("title") or "")[:40]

        print(f"  {eid:>4d} {icon} {status:>13s} | {platform_name:<20s} | {fid:>7s} | {reward_str:>10s} | {title}")

    print()
    return 0


def cmd_dashboard(args: argparse.Namespace) -> int:
    """Show statistics dashboard."""
    entries = load_tracking()

    if not entries:
        print("📭 No tracking data available.")
        return 0

    total = len(entries)
    status_counts: Dict[str, int] = defaultdict(int)
    platform_rewards: Dict[str, float] = defaultdict(float)
    platform_counts: Dict[str, int] = defaultdict(int)
    monthly_rewards: Dict[str, float] = defaultdict(float)
    total_reward = 0.0
    rewarded_count = 0

    for e in entries:
        status_counts[e.get("status", "unknown")] += 1
        platform_counts[e.get("platform", "unknown")] += 1

        if e.get("reward_amount") and e.get("status") == "rewarded":
            amt = float(e["reward_amount"])
            total_reward += amt
            rewarded_count += 1
            platform_rewards[e.get("platform", "unknown")] += amt

            # Monthly breakdown
            paid_at = e.get("reward_paid_at", e.get("updated_at", ""))
            if paid_at:
                month_key = paid_at[:7]  # YYYY-MM
                monthly_rewards[month_key] += amt

    submitted = status_counts.get("submitted", 0) + status_counts.get("under_review", 0) \
                + status_counts.get("verified", 0) + status_counts.get("rewarded", 0)
    verified = status_counts.get("verified", 0)
    acceptance_rate = (verified + rewarded_count) / submitted * 100 if submitted > 0 else 0

    # Dashboard output
    w = 62
    print(f"\n{' Bounty Hunter Dashboard ':═^{w}}")
    print(f"  {'Total Entries:':<30s} {total:>10d}")
    print(f"  {'Total Submissions:':<30s} {submitted:>10d}")
    print(f"  {'Verified:':<30s} {verified:>10d}")
    print(f"  {'Rewarded:':<30s} {rewarded_count:>10d}")
    print(f"  {'Rejected:':<30s} {status_counts.get('rejected', 0):>10d}")
    print(f"  {'Acceptance Rate:':<30s} {acceptance_rate:>10.1f}%")
    print()

    if total_reward > 0:
        print(f"  {'💰 Total Rewards:':<30s} {'¥' + f'{total_reward:,.2f}':>10s}")
        print()

        if platform_rewards:
            print(f"{' Platform Rewards ':─^{w}}")
            sorted_platforms = sorted(platform_rewards.items(), key=lambda x: x[1], reverse=True)
            for plat, amt in sorted_platforms:
                name = PLATFORM_NAMES.get(plat, plat)
                print(f"  {name:<40s}  ¥{amt:>12,.2f}")
            print()

        if monthly_rewards:
            print(f"{' Monthly Breakdown ':─^{w}}")
            for month in sorted(monthly_rewards.keys(), reverse=True)[:12]:
                amt = monthly_rewards[month]
                bar = "█" * min(int(amt / 1000), 30)
                print(f"  {month:<10s}  ¥{amt:>10,.2f}  {bar}")
            print()

    # Status distribution
    print(f"{' Status Distribution ':─^{w}}")
    for st in STATUS_ORDER:
        cnt = status_counts.get(st, 0)
        icon = STATUS_ICONS.get(st, "📌")
        bar = "█" * min(cnt * 2, 30)
        print(f"  {icon} {st:>15s}  [{cnt:>3d}] {bar}")
    print()

    return 0


def cmd_export(args: argparse.Namespace) -> int:
    """Export tracking data to CSV."""
    entries = load_tracking()

    if not entries:
        print("📭 No tracking data to export.")
        return 0

    output_path = args.output or "bounty_export.csv"
    fmt = (args.format or "csv").lower()

    if fmt == "csv":
        fieldnames = [
            "id", "finding_id", "title", "platform", "platform_name",
            "status", "reporter", "reward_amount", "reward_currency",
            "reward_paid_at", "submitted_at", "notes"
        ]
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            # Sort by ID
            entries.sort(key=lambda e: e.get("id", 0))
            for e in entries:
                writer.writerow(e)

        print(f"✅ Exported {len(entries)} entries to {output_path}")
    elif fmt == "json":
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)
        print(f"✅ Exported {len(entries)} entries to {output_path} (JSON)")
    else:
        print(f"❌ Unsupported format: {fmt}. Use 'csv' or 'json'.")
        return 1

    return 0


def cmd_delete(args: argparse.Namespace) -> int:
    """Delete a tracking entry by ID."""
    entries = load_tracking()

    target = None
    for e in entries:
        if e.get("id") == args.track_id:
            target = e
            break

    if not target:
        print(f"❌ Tracking entry #{args.track_id} not found.")
        return 1

    entries.remove(target)
    save_tracking(entries)
    print(f"🗑️  Tracking entry #{args.track_id} deleted.")
    return 0


def cmd_summary(args: argparse.Namespace) -> int:
    """Show a compact summary of today's activity."""
    entries = load_tracking()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    recent = [e for e in entries if (e.get("created_at", "")[:10] == today or
                                      e.get("updated_at", "")[:10] == today)]
    paid_today = [e for e in entries if e.get("reward_paid_at", "")[:10] == today]

    print(f"\n📊 Bounty Summary — {today}")
    print(f"   Activity today: {len(recent)} updates")
    if paid_today:
        total_today = sum(float(e.get("reward_amount", 0)) for e in paid_today)
        print(f"   Rewards received today: ¥{total_today:,.2f} ({len(paid_today)} payments)")

    # By platform
    platform_today: Dict[str, int] = defaultdict(int)
    for e in recent:
        platform_today[e.get("platform", "?")] += 1
    for plat, cnt in platform_today.items():
        print(f"   {PLATFORM_NAMES.get(plat, plat):30s} {cnt} activity")

    print()
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        prog="bounty_tracker",
        description="Bounty Tracker — Track vulnerability submissions and rewards",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
        Examples:
          bounty_tracker add --finding-id 0 --platform 360 --status submitted
          bounty_tracker update --track-id 1 --status rewarded --reward 5000 --currency CNY
          bounty_tracker list
          bounty_tracker list --status rewarded --platform hackerone
          bounty_tracker dashboard
          bounty_tracker export --format csv --output rewards.csv
          bounty_tracker summary
        """),
    )
    sub = parser.add_subparsers(dest="command", help="Available commands")

    # ---------- add ----------
    p_add = sub.add_parser("add", help="Add a new tracking entry")
    p_add.add_argument("--finding-id", "-fid", type=int, required=True,
                       help="Finding ID from findings.json")
    p_add.add_argument("--platform", "-p", type=str, required=True,
                       help="Platform key (360, cnvd, cnnvd, cve, hackerone, bugcrowd, nvd)")
    p_add.add_argument("--status", "-s", type=str, required=True,
                       help=f"Status: {', '.join(VALID_STATUSES)}")
    p_add.add_argument("--title", "-t", type=str, default=None,
                       help="Vulnerability title")
    p_add.add_argument("--reporter", "-r", type=str, default=None,
                       help="Reporter name/handle")
    p_add.add_argument("--submitted-at", type=str, default=None,
                       help="Submission date (YYYY-MM-DD or ISO)")
    p_add.add_argument("--notes", "-n", type=str, default=None,
                       help="Additional notes")

    # ---------- update ----------
    p_upd = sub.add_parser("update", help="Update a tracking entry")
    p_upd.add_argument("--track-id", "-tid", type=int, required=True,
                       help="Tracking entry ID")
    p_upd.add_argument("--status", "-s", type=str, default=None,
                       help="New status")
    p_upd.add_argument("--title", "-t", type=str, default=None)
    p_upd.add_argument("--reporter", "-r", type=str, default=None)
    p_upd.add_argument("--submitted-at", type=str, default=None)
    p_upd.add_argument("--reward", type=float, default=None,
                       help="Reward amount (e.g., 5000)")
    p_upd.add_argument("--currency", type=str, default=None,
                       help=f"Currency: {', '.join(VALID_CURRENCIES)}")
    p_upd.add_argument("--paid-at", type=str, default=None,
                       help="Payment date (YYYY-MM-DD)")
    p_upd.add_argument("--notes", "-n", type=str, default=None)

    # ---------- list ----------
    p_list = sub.add_parser("list", help="List all tracking entries")
    p_list.add_argument("--status", "-s", type=str, default=None,
                        help="Filter by status")
    p_list.add_argument("--platform", "-p", type=str, default=None,
                        help="Filter by platform")

    # ---------- dashboard ----------
    sub.add_parser("dashboard", help="Show statistics dashboard")

    # ---------- export ----------
    p_exp = sub.add_parser("export", help="Export tracking data")
    p_exp.add_argument("--format", "-f", type=str, default="csv",
                       help="Export format: csv or json (default: csv)")
    p_exp.add_argument("--output", "-o", type=str, default=None,
                       help="Output file path (default: bounty_export.csv)")

    # ---------- delete ----------
    p_del = sub.add_parser("delete", help="Delete a tracking entry")
    p_del.add_argument("--track-id", "-tid", type=int, required=True,
                       help="Tracking entry ID to delete")

    # ---------- summary ----------
    sub.add_parser("summary", help="Show today's activity summary")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    command_handlers = {
        "add": cmd_add,
        "update": cmd_update,
        "list": cmd_list,
        "dashboard": cmd_dashboard,
        "export": cmd_export,
        "delete": cmd_delete,
        "summary": cmd_summary,
    }

    handler = command_handlers.get(args.command)
    if handler:
        return handler(args)
    else:
        print(f"❌ Unknown command: {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
