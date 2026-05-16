---
name: self-improvement
description: Self-optimization engine — analyze performance, tune configuration, learn from mistakes. Use when: (1) running periodic self-audits, (2) optimizing OpenClaw config, (3) analyzing token usage patterns, (4) identifying skill gaps, (5) suggesting improvements based on usage data. Reads session logs, token stats, and benchmark results.
version: "1.0.0"
---

# Self-Improvement Engine

Continuously improves OpenClaw by analyzing its own performance.

## Analysis Pipeline

1. **Gather data**: Token usage, session logs, error rates, benchmark scores
2. **Identify patterns**: Most-used tools, common failures, context window pressure
3. **Generate recommendations**: Config changes, skill additions, prompt tuning
4. **Apply improvements**: Update configs, install missing skills, adjust parameters
5. **Verify impact**: Re-run benchmark, compare scores

## Weekly Self-Audit

```bash
# Run benchmark
python3 benchmark.py

# Check token usage
python3 -c "
import json, os
sessions = json.load(open(os.path.expanduser('~/.openclaw/agents/main/sessions/sessions.json')))
for k,v in sessions.get('sessions',{}).items():
    print(f'{k}: {v.get(\"totalTokens\",0):,} tokens, \${v.get(\"estimatedCostUsd\",0):.4f}')
"

# Check error patterns in logs
journalctl --user -u openclaw-gateway --since '7 days ago' | grep -i error | sort | uniq -c | sort -rn | head -10
```

## Optimization Strategies

| Pattern | Fix |
|---------|-----|
| High token usage | Enable reasoning only when needed |
| Many errors in exec | Review exec-approvals.json |
| Context window pressure | Split long sessions, use /compact |
| Skill not triggering | Improve description in SKILL.md frontmatter |
| Slow responses | Switch to smaller model for simple queries |

## Auto-Tuning

```bash
# Analyze and suggest config changes
python3 self_improve.py analyze
# Apply suggested changes
python3 self_improve.py apply
```
