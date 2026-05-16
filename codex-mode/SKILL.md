---
name: codex-mode
description: Fully autonomous coding agent mode — plan, implement, test, fix, repeat. Use when: (1) user says "act like Codex" or "codex mode", (2) fully autonomous feature building, (3) background coding tasks with self-healing, (4) hands-off development. Runs coding-agent with autonomous loop: implement → test → fix errors → retest → report. Requires coding-agent, test-generator, and code-review skills.
version: "1.0.0"
---

# Codex Mode — Autonomous Coding Agent

Makes OpenClaw behave like OpenAI Codex: fully autonomous coding with self-healing loop.

## Activation

User says any of:
- "codex mode"
- "act like Codex"  
- "autonomous mode"
- "hands-free coding"

## Autonomous Loop

```
┌─────────────────────────────────────┐
│           CODEX MODE LOOP           │
│                                     │
│  1. RECEIVE TASK                    │
│       ↓                             │
│  2. PLAN (update_plan)              │
│       ↓                             │
│  3. IMPLEMENT (coding-agent)        │
│       ↓                             │
│  4. TEST (exec + test-generator)    │
│       ↓                             │
│  5. REVIEW (code-review skill)      │
│       ↓                             │
│  6. FIX ERRORS ───→ back to 4      │
│       ↓ (clean)                     │
│  7. REPORT COMPLETION               │
└─────────────────────────────────────┘
```

## Implementation

### Step 1: Plan
```bash
# Create structured plan
update_plan plan:[
  {"step":"Analyze requirements","status":"pending"},
  {"step":"Implement core logic","status":"pending"},
  {"step":"Write tests","status":"pending"},
  {"step":"Review & fix","status":"pending"},
  {"step":"Report completion","status":"pending"}
]
```

### Step 2: Implement (background)
```bash
# Spawn coding-agent in background
sessions_spawn taskName:"codex_build" task:"Build <feature>. 
Use test-generator to create tests. Use code-review to check quality.
Auto-fix any issues found. Report when complete."
```

### Step 3: Test & Fix Loop
```bash
# Run tests
exec command:"cd ~/project && python -m pytest -x --tb=short 2>&1"

# If tests fail → read error → fix → rerun
# Repeat up to 3 times, then report status
```

### Step 4: Review & Report
```bash
# Quick security scan
python3 ~/.openclaw/plugin-skills/code-review/...  # Security check

# Report with stats:
# - Files changed: X
# - Tests: Y passed / Z total
# - Issues found: N (all fixed)
```

## Self-Healing Rules

1. **Test failures** → Read error output → fix the code → rerun tests (max 3 loops)
2. **Lint errors** → Auto-apply fixes → recheck
3. **Import errors** → Add missing imports → retry
4. **Timeout** → Reduce scope → restart with smaller task
5. **Stuck** → Report to user with diagnosis, don't loop forever

## Progress Updates

```
🔄 Codex: Implementing auth module... (step 2/5)
✅ Codex: Core logic complete, 3 files changed
🧪 Codex: Running tests... 5/5 passed
🔍 Codex: Review — 0 issues found
✅ Codex: Feature complete! Summary: ...
```

## Integration

Uses these skills automatically:
- `coding-agent` → implementation
- `test-generator` → test creation
- `code-review` → quality check
- `lsp` MCP → code intelligence
- `update_plan` → progress tracking
