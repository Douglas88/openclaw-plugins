---
name: session-manager
description: Session export, analysis, and management. Use when: (1) exporting conversations to markdown/text, (2) viewing session history summaries, (3) analyzing conversation patterns, (4) finding specific past conversations. Runs scripts/export_session.py for all export operations.
version: "1.0.0"
---

# Session Manager

Export, analyze, and manage OpenClaw session history. Uses `scripts/export_session.py` to read `.jsonl` session logs and produce readable output.

## Quick Start

```bash
SCRIPTS=~/.openclaw/plugin-skills/session-tools/scripts
```

## 1. List All Sessions

```bash
python3 $SCRIPTS/export_session.py --list
```

Shows session keys, titles, dates, channels, and message counts for all recorded sessions.

## 2. Export a Single Session

```bash
# Full session as Markdown (default)
python3 $SCRIPTS/export_session.py --session <key> --format markdown --output /tmp/session.md

# Last 50 messages as plain text
python3 $SCRIPTS/export_session.py --session <key> --format text --last 50

# Compact JSON summary (metadata + word counts + time range)
python3 $SCRIPTS/export_session.py --session <key> --format summary
```

If `--output` is omitted, result is printed to stdout.

## 3. Date-Range Filtering

```bash
# Messages after a specific date
python3 $SCRIPTS/export_session.py --session <key> --after "2026-05-01T00:00:00"

# Messages in a date window
python3 $SCRIPTS/export_session.py --session <key> --after "2026-05-15" --before "2026-05-16"
```

## 4. Bulk Export Multiple Sessions

Loop over session keys from `--list` output:

```bash
for key in session-key-1 session-key-2; do
  python3 $SCRIPTS/export_session.py --session "$key" --format markdown --output "/tmp/$key.md"
done
```

Or use `--list` output to export all:

```bash
python3 $SCRIPTS/export_session.py --list | grep -oP '^\s{2}\K\S+' | while read key; do
  python3 $SCRIPTS/export_session.py --session "$key" --format text --output "/tmp/${key}.txt"
done
```

## 5. Session Analysis

The `--format summary` output provides:

| Field | Description |
|-------|-------------|
| `message_count` | Total number of messages |
| `word_counts.user` | Words from user messages |
| `word_counts.assistant` | Words from assistant messages |
| `word_counts.other` | Words from system/tool messages |
| `time_range` | First and last message timestamps |

Use with `jq` for scripting:

```bash
python3 $SCRIPTS/export_session.py --session <key> --format summary | jq '{msgs: .message_count, ratio: (.word_counts.assistant / .word_counts.user)}'
```

## 6. Finding Sessions by Date or Content

Use `--list` to see all sessions with their creation dates, then filter:

```bash
# List sessions and grep for a date
python3 $SCRIPTS/export_session.py --list | grep -B3 "2026-05-16"

# Search for keywords in a session
python3 $SCRIPTS/export_session.py --session <key> --format text | grep "keyword"
```

## 7. Common Workflows

### Save a conversation for reference

```bash
python3 $SCRIPTS/export_session.py --session <key> --format markdown --output ~/Documents/session-$(date +%Y%m%d).md
```

### Analyze conversation length trends

```bash
for key in $(python3 $SCRIPTS/export_session.py --list | grep -oP '^\s{2}\K\S+'); do
  python3 $SCRIPTS/export_session.py --session "$key" --format summary | jq -r '"\(.created) \(.message_count)msgs \(.word_counts.assistant)asst \(.word_counts.user)user"'
done | sort
```

### Extract user questions from a session

```bash
python3 $SCRIPTS/export_session.py --session <key> --format text | grep -A5 "🧑 User"
```

## Configuration

- **Sessions directory:** `~/.openclaw/agents/main/sessions/`
- **Metadata file:** `sessions.json` in the sessions directory
- **Log files:** `*.jsonl` (one per session)

## Notes

- Tool-call XML blocks are replaced with `[tool calls omitted]` in output for readability
- Timestamps are formatted in local time
- Session keys can be partial — the script auto-matches by substring if the exact key isn't found
