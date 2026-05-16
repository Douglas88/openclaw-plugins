#!/usr/bin/env python3
"""
OpenClaw Session Export Tool
Converts session JSONL files to Markdown, text, or JSON summary.

Usage:
  python3 export_session.py --list
  python3 export_session.py --session <key> --format markdown --output /tmp/session.md
  python3 export_session.py --session <key> --format text --last 50
  python3 export_session.py --session <key> --format summary
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

SESSIONS_DIR = Path.home() / ".openclaw" / "agents" / "main" / "sessions"


def load_sessions_meta():
    """Load sessions.json and return a dict keyed by session key."""
    path = SESSIONS_DIR / "sessions.json"
    if not path.exists():
        return {}
    with open(path) as f:
        data = json.load(f)
    # Normalize: sessions.json may be a list or a dict keyed by session key
    if isinstance(data, list):
        return {s.get("sessionKey", s.get("key", "")): s for s in data}
    return data


def find_jsonl(session_key):
    """Find the .jsonl file for a given session key. Returns Path or None."""
    cand = SESSIONS_DIR / f"{session_key}.jsonl"
    if cand.exists():
        return cand
    # Try fuzzy match
    for f in SESSIONS_DIR.glob("*.jsonl"):
        if session_key in f.stem:
            return f
    return None


def parse_messages(jsonl_path, last=None, after=None, before=None):
    """Parse .jsonl file and return list of message dicts with filtering."""
    messages = []
    with open(jsonl_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue
            # Extract timestamp
            ts = msg.get("timestamp") or msg.get("createdAt") or msg.get("ts")
            if ts:
                if isinstance(ts, (int, float)):
                    dt = datetime.fromtimestamp(ts / 1000 if ts > 1e12 else ts, tz=timezone.utc)
                else:
                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                if after and dt < after:
                    continue
                if before and dt > before:
                    continue
                msg["_dt"] = dt.isoformat()
            else:
                msg["_dt"] = "unknown"
            messages.append(msg)
    if last:
        messages = messages[-last:]
    return messages


def role_label(msg):
    """Map raw role/author to human label."""
    role = msg.get("role", "").lower()
    author = msg.get("author", "").lower()
    if role == "user" or author in ("user", "human"):
        return "🧑 User"
    if role == "assistant" or author in ("assistant", "ai", "bot"):
        return "🤖 Assistant"
    if role == "system" or author == "system":
        return "⚙️ System"
    if role == "tool" or author == "tool":
        return "🔧 Tool"
    return f"❓ {role or author or 'unknown'}"


def clean_content(msg):
    """Extract clean text content, stripping tool-call blocks."""
    content = msg.get("content", "")
    if isinstance(content, list):
        # Multimodal content blocks
        parts = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    parts.append(block.get("text", ""))
            else:
                parts.append(str(block))
        content = "\n".join(parts)
    if not isinstance(content, str):
        content = str(content)
    # Strip large tool-call XML blocks
    import re
    content = re.sub(r"<tool_calls>.*?</tool_calls>", "[tool calls omitted]", content, flags=re.DOTALL)
    return content.strip()


def format_human_ts(msg):
    """Format _dt into human-readable local time."""
    dt_str = msg.get("_dt", "unknown")
    if dt_str == "unknown":
        return "unknown"
    try:
        dt = datetime.fromisoformat(dt_str)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return dt_str[:19]


def export_markdown(session_key, meta, messages, file=None):
    """Export session as Markdown."""
    out = []
    out.append(f"# Session: {session_key}")
    out.append("")
    if meta:
        out.append(f"- **Title:** {meta.get('title', meta.get('name', 'N/A'))}")
        out.append(f"- **Created:** {meta.get('createdAt', meta.get('created', 'N/A'))}")
        out.append(f"- **Channel:** {meta.get('channel', 'N/A')}")
    out.append(f"- **Messages:** {len(messages)}")
    out.append("")
    out.append("---")
    out.append("")
    for msg in messages:
        ts = format_human_ts(msg)
        label = role_label(msg)
        content = clean_content(msg)
        out.append(f"### {label}  \n*{ts}*")
        out.append("")
        out.append(content)
        out.append("")
        out.append("---")
        out.append("")
    text = "\n".join(out)
    if file:
        file.write(text)
    return text


def export_text(session_key, meta, messages, file=None):
    """Export session as plain text."""
    out = []
    out.append(f"=== Session: {session_key} ===")
    if meta:
        out.append(f"Title: {meta.get('title', meta.get('name', 'N/A'))}")
    out.append(f"Messages: {len(messages)}")
    out.append("=" * 60)
    out.append("")
    for msg in messages:
        ts = format_human_ts(msg)
        label = role_label(msg)
        content = clean_content(msg)
        out.append(f"[{ts}] {label}")
        out.append(content)
        out.append("")
        out.append("-" * 40)
        out.append("")
    text = "\n".join(out)
    if file:
        file.write(text)
    return text


def export_summary(session_key, meta, messages):
    """Export compact JSON summary."""
    word_counts = {"user": 0, "assistant": 0, "other": 0}
    for msg in messages:
        role = msg.get("role", "").lower()
        content = clean_content(msg)
        wc = len(content.split())
        if role == "user":
            word_counts["user"] += wc
        elif role == "assistant":
            word_counts["assistant"] += wc
        else:
            word_counts["other"] += wc
    summary = {
        "session_key": session_key,
        "title": meta.get("title", meta.get("name", "N/A")) if meta else "N/A",
        "channel": meta.get("channel", "N/A") if meta else "N/A",
        "created": meta.get("createdAt", meta.get("created", "N/A")) if meta else "N/A",
        "message_count": len(messages),
        "word_counts": word_counts,
        "time_range": {
            "first": format_human_ts(messages[0]) if messages else None,
            "last": format_human_ts(messages[-1]) if messages else None,
        },
    }
    return json.dumps(summary, indent=2, ensure_ascii=False)


def list_sessions(sessions):
    """Print a list of all sessions."""
    for key, meta in sessions.items():
        ts = meta.get("createdAt", meta.get("created", "N/A"))
        title = meta.get("title", meta.get("name", "N/A"))
        channel = meta.get("channel", "N/A")
        jsonl = find_jsonl(key)
        count = "?"
        if jsonl:
            count = str(sum(1 for _ in open(jsonl)))
        print(f"  {key}")
        print(f"    Title: {title}")
        print(f"    Created: {ts}")
        print(f"    Channel: {channel}")
        print(f"    Messages: {count}")
        print()


def cli():
    parser = argparse.ArgumentParser(description="OpenClaw Session Export Tool")
    parser.add_argument("--list", action="store_true", help="List all sessions")
    parser.add_argument("--session", type=str, help="Session key to export")
    parser.add_argument("--format", choices=["markdown", "text", "summary"], default="markdown")
    parser.add_argument("--output", type=str, help="Output file (default: stdout)")
    parser.add_argument("--last", type=int, help="Export only last N messages")
    parser.add_argument("--after", type=str, help="Filter messages after ISO date")
    parser.add_argument("--before", type=str, help="Filter messages before ISO date")
    args = parser.parse_args()

    sessions = load_sessions_meta()

    if args.list:
        if not sessions:
            print("No sessions found.")
            return
        print(f"Found {len(sessions)} session(s):\n")
        list_sessions(sessions)
        return

    if not args.session:
        parser.error("Must specify --session or --list")

    session_key = args.session
    meta = sessions.get(session_key, {})
    jsonl_path = find_jsonl(session_key)

    if not jsonl_path:
        # Try matching by substring
        for key in sessions:
            if session_key in key:
                session_key = key
                meta = sessions[key]
                jsonl_path = find_jsonl(key)
                break
        if not jsonl_path:
            print(f"Error: No .jsonl file found for session '{args.session}'", file=sys.stderr)
            sys.exit(1)

    after_dt = datetime.fromisoformat(args.after) if args.after else None
    before_dt = datetime.fromisoformat(args.before) if args.before else None

    messages = parse_messages(jsonl_path, last=args.last, after=after_dt, before=before_dt)

    if not messages:
        print("No messages matched filters.")
        return

    if args.output:
        with open(args.output, "w") as f:
            if args.format == "markdown":
                export_markdown(session_key, meta, messages, file=f)
            elif args.format == "text":
                export_text(session_key, meta, messages, file=f)
            else:
                f.write(export_summary(session_key, meta, messages))
        print(f"Exported {len(messages)} messages to {args.output}")
    else:
        if args.format == "markdown":
            print(export_markdown(session_key, meta, messages))
        elif args.format == "text":
            print(export_text(session_key, meta, messages))
        else:
            print(export_summary(session_key, meta, messages))


if __name__ == "__main__":
    cli()
