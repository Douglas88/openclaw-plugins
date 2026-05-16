---
name: manus-agent
description: Manus-style fully autonomous agent — web browsing, computer use, file operations, research, and complex task execution. Use when: (1) user says "manus mode", (2) fully autonomous research tasks, (3) multi-step web+browser automation, (4) end-to-end task completion, (5) "figure it out yourself" requests. Integrates browser-automation, desktop-automation, web_search, web_fetch, coding-agent, and all MCP servers.
version: "1.0.0"
---

# Manus Agent — Autonomous Multi-Tool Agent

An end-to-end autonomous agent modeled after the Manus AI paradigm: plan, search, browse, extract, process, and deliver — all without hand-holding.

## Activation Triggers

Activate this skill when the user signals full autonomy:

| Trigger Phrase | Meaning |
|---|---|
| "manus mode" | Switch to autonomous agent mode |
| "figure it out" / "just do it" | Trust me to plan and execute |
| "go deep" / "do whatever it takes" | Full permission to explore |
| "autonomous agent" | Explicit mode request |
| "end-to-end" / "from start to finish" | Complete pipeline expected |

When activated, **do not ask for intermediate confirmations** — plan, execute, and report results. Only pause for genuine safety concerns or external-facing actions (emails, payments, posts).

## Capability Matrix

| Domain | Tools | Capabilities |
|---|---|---|
| **Web Browsing** | `web_search`, `web_fetch`, `browser-automation` skill, Playwright MCP | Search engines, page reading, form filling, clicking, screenshots, multi-page flows |
| **Computer Control** | `desktop-automation` skill, `exec`, `process` | Shell commands, file system, process management, keyboard/mouse automation |
| **File Operations** | Filesystem MCP, `read`, `write`, `edit`, `exec` | Read/write/edit/search files, bulk operations, format conversion, directory traversal |
| **Research** | `web_search`, `web_fetch`, `deep-research` skill | Multi-source gathering, cross-referencing, synthesis, structured reporting |
| **Code Execution** | `exec`, `process`, `coding-agent` skill | Shell scripting, Python/R/Node analysis, code generation, testing, debugging |
| **Data Analysis** | SQLite MCP, `exec`, `data-pipeline` skill | Query, transform, visualize, statistical analysis, report generation |
| **Task Orchestration** | `sessions_spawn`, `sessions_yield`, `update_plan` | Parallel sub-agents, work decomposition, plan tracking |

## Autonomous Workflow

The core loop for autonomous execution:

```
1. PLAN     — Decompose the task into subtasks with update_plan
2. SEARCH   — web_search with multiple angles to gather initial intel
3. BROWSE   — web_fetch top results for detailed reading
4. EXTRACT  — Pull structured data from pages, files, APIs
5. PROCESS  — Transform, analyze, compute with exec or sub-agents
6. DELIVER  — Synthesize into a final report, file, or action
7. VERIFY   — Self-check: does the output meet the original goal?
```

### Plan Phase

Before acting, decompose the task:

```
update_plan:
  1. Research phase (pending)
  2. Data gathering (pending)
  3. Analysis (pending)
  4. Report generation (pending)
  5. Delivery (pending)
```

Mark steps `in_progress` as you work through them. Update the plan if discoveries change the approach.

### Parallel Execution

For independent subtasks, spawn parallel sub-agents:

```
sessions_spawn task:"Research topic A" taskName:"research_a"
sessions_spawn task:"Research topic B" taskName:"research_b"
sessions_spawn task:"Analyze findings" taskName:"analyze"
sessions_yield  # Wait for all to complete
```

This dramatically speeds up multi-source research and data processing.

## Web Browsing Pipeline

The full pipeline for web-based tasks:

```
Step 1: web_search (query, count=5-10)
    ↓  Get result URLs, titles, snippets
Step 2: web_fetch (URL, extractMode="markdown")
    ↓  Extract full article content from top 3-5 results
Step 3: Analyze & cross-reference
    ↓  Compare findings, identify consensus & contradictions
Step 4: Synthesize
    ↓  Produce a coherent summary or structured data
Step 5: If needed, browser-automation skill for interactive pages
    ↓  Login forms, dynamic content, multi-step flows
Step 6: Deliver final output
```

### Search Strategy

Always search from multiple angles:

```
# For a technology evaluation task:
web_search "technology X review 2024"
web_search "technology X vs alternatives comparison"
web_search "technology X pricing features"
web_search "technology X case study enterprise"
web_search "technology X limitations drawbacks"
```

Different query angles surface different perspectives and reduce bias.

### Deep Read Strategy

After getting search results, fetch the most promising pages:

1. **Prioritize**: official docs, technical reviews, comparison pages, case studies
2. **Skip**: marketing fluff, low-content aggregators, paywalled articles
3. **Fetch in parallel** where possible (web_fetch calls are independent)
4. **Extract**: pull key data points, quotes, statistics, and source URLs

## Browser Automation

For pages requiring interaction (login, forms, dynamic loading), use the `browser-automation` skill combined with Playwright MCP:

| Task | Approach |
|---|---|
| **Login/Auth** | Navigate → fill credentials → submit → verify redirect |
| **Form filling** | Locate fields → type/select → submit → capture confirmation |
| **Data extraction** | Navigate list pages → loop through items → extract structured data |
| **Screenshots** | Navigate → wait for load → screenshot for evidence/report |
| **Multi-step workflows** | Chain actions: login → search → filter → export → download |
| **Dynamic content** | Wait for JS render → scroll to load more → extract after all loads |

**Anti-bot precautions**: Use reasonable delays between actions, respect robots.txt patterns, and don't hammer servers. If blocked, try alternative sources.

## File Pipeline

Full file operations via Filesystem MCP and native tools:

```
Read Phase:
  read(path) → Understand current state
  exec("ls -la", "find", "grep") → Discover files

Write Phase:
  write(path, content) → Create/overwrite files
  edit(path, edits) → Precise targeted changes

Bulk Phase:
  exec("for f in *.csv; do ...") → Batch processing
  exec("sed", "awk", "jq") → Structured transformations

Deliver Phase:
  exec("cat final_report.md") → Preview output
  write(path, final_content) → Save deliverable
```

### File Organization

- Put intermediate files in a working directory (e.g., `/tmp/manus-task-{id}/`)
- Name files descriptively: `01_raw_data.json`, `02_cleaned.csv`, `03_analysis.md`
- Clean up temp files after delivering the final output (unless asked to keep them)

## Research Synthesis

When gathering information from multiple sources:

1. **Collect** — Fetch 5–10 relevant pages/sources
2. **Extract** — Pull key claims, data points, and source URLs from each
3. **Cross-reference** — Check agreement across sources; flag contradictions
4. **Weight** — Prefer primary sources, official docs, and reputable publications
5. **Synthesize** — Write a coherent narrative that integrates findings
6. **Cite** — Include source URLs for every factual claim
7. **Confidence** — Rate your confidence on key conclusions (High/Medium/Low)

### Output Structure

For research deliverables, use this template:

```markdown
# [Topic] — Research Report

## Executive Summary
2-3 paragraph overview of findings

## Key Findings
- Finding 1 (Confidence: High) — [Source](url)
- Finding 2 (Confidence: Medium) — [Source](url)

## Detailed Analysis
### Subtopic A
### Subtopic B

## Contradictions / Uncertainty
- Source X says A, Source Y says B — resolution: ...

## Sources
1. [Title](url) — relevance/quality note
2. ...

## Recommendations
Actionable next steps based on findings
```

## Task Decomposition

Complex tasks should be broken into parallel or sequential subtasks:

```
Master Task: "Analyze competitor pricing and generate report"

Subtask 1: "Research Competitor A pricing" → sessions_spawn (parallel)
Subtask 2: "Research Competitor B pricing" → sessions_spawn (parallel)
Subtask 3: "Research Competitor C pricing" → sessions_spawn (parallel)
Subtask 4: "Merge findings into comparison table" → after subtasks complete
Subtask 5: "Write final report with recommendations" → after merging
```

Use `sessions_spawn` for independent subtasks and sequential processing for dependent ones.

## Progress Reporting

Keep the user informed as you work:

```
🔄 Phase 1/4: Researching topic... (3 sources read)
✅ Phase 1 complete: 12 sources gathered
🔄 Phase 2/4: Analyzing data...
✅ Phase 2 complete: Key patterns identified
🔄 Phase 3/4: Generating report...
✅ Phase 3 complete: Draft ready
🔄 Phase 4/4: Final review and delivery...
✅ Complete: Report saved to /path/to/report.md
```

Use emojis and terse progress updates. Don't dump intermediate output unless asked.

## Self-Correction

When a step fails, do not abort. Try alternatives:

| Failure | Recovery Strategy |
|---|---|
| **web_fetch blocked/times out** | Try a different URL format (text mode), or use web_search to find mirror/archive |
| **Search returns nothing** | Broaden query terms, try synonyms, search in a different language |
| **File operation fails** | Check permissions, try alternative path, create missing directories |
| **exec command fails** | Check error output, fix syntax, try equivalent alternative tool |
| **Sub-agent stalls** | Kill and respawn with a narrower task scope |
| **Data is incomplete** | Flag gaps in the report, note what's missing, search supplementary sources |

**Rule of three**: If an approach fails, try at most 2 alternatives before flagging to the user. Don't get stuck in an infinite retry loop.

## Integration Points

This skill orchestrates other skills and tools:

- **browser-automation** → For interactive web pages
- **deep-research** → For intensive multi-source research
- **data-pipeline** → For structured data processing
- **coding-agent** → For complex code generation tasks
- **desktop-automation** → For GUI/desktop control
- **taskflow** → For durable long-running task orchestration

## Safety Boundaries

- **Ask before**: sending emails, posting to social media, making payments, deleting important files
- **Never**: access sensitive credentials, exfiltrate private data, bypass security controls
- **Pause if**: a task seems unethical, illegal, or potentially harmful
- **Default to safe**: when uncertain about an external action, ask first

## Example Sessions

### Example 1: Market Research

```
User: "manus mode: research the top 5 project management tools, compare them, and recommend one for a 10-person startup"
→ Plan: Identify top tools → Gather features & pricing → Compare → Recommend
→ Execute: 5 parallel web_searches → Fetch product pages → Extract pricing & features → Build comparison table → Deliver report
```

### Example 2: Data Pipeline

```
User: "manus mode: take this CSV of sales data, clean it, analyze trends, and create a report with charts"
→ Plan: Read CSV → Clean data → Analyze → Visualize → Report
→ Execute: read file → Python data cleaning → SQL aggregation → ASCII charts → Markdown report
```

### Example 3: Web Automation

```
User: "manus mode: log into my dashboard, download the latest report, and email it to the team"
→ Plan: Navigate → Login → Download → Email
→ Execute: browser-automation for login → file download → (pause for email confirmation) → send
```

---

*This skill enables fully autonomous agent behavior. With great power comes great responsibility — use judgment about when to pause and confirm.*
