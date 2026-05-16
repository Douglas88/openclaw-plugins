---
name: code-review
description: Automated code review with security, performance, and style analysis. Use when: (1) reviewing PRs or code changes, (2) checking code quality before commit, (3) running pre-commit checks, (4) security audit of code, (5) finding anti-patterns and bugs. Supports Python, JavaScript/TypeScript, Go, Rust. Uses grep for pattern detection, exec for linters, and read for deep analysis. See references/ for security patterns and review checklist.
version: "1.0.0"
---

# Code Review Skill

Automated code review analyzing code for security vulnerabilities, performance issues, code quality, and style compliance.

## Workflow

### 1. Quick Scan (always run first)

```bash
# File-level sanity check
wc -l <file>                    # File size
grep -n "TODO\|FIXME\|HACK" <file>  # Technical debt markers
grep -n "print\|console.log" <file> # Debug artifacts
grep -c "^[[:space:]]\+$" <file>     # Trailing whitespace
```

### 2. Security Scan

Check these patterns in order of severity:

| Pattern | Search | Severity |
|---------|--------|----------|
| SQL Injection | `grep -n "f\"SELECT\|'SELECT\|+.*SELECT\|format.*SELECT\|%s.*SELECT" <file>` | 🔴 CRITICAL |
| XSS | `grep -n "innerHTML\|dangerouslySetInnerHTML\|document.write" <file>` | 🔴 CRITICAL |
| Command Injection | `grep -n "os.system\|subprocess.*shell=True\|eval\|exec(" <file>` | 🔴 CRITICAL |
| Hardcoded Secrets | `grep -n "api_key\|password\|secret\|token\s*=" <file>` | 🔴 CRITICAL |
| Unsafe Deserialization | `grep -n "pickle\|yaml.load\|json.loads.*user" <file>` | 🟡 HIGH |
| Open Redirect | `grep -n "redirect.*request\|Location.*request\|window.location" <file>` | 🟡 HIGH |
| Path Traversal | `grep -n "os.path.join.*user\|open.*user.*input\|\.\..*/" <file>` | 🟡 HIGH |

### 3. Performance Scan

| Pattern | Search | Severity |
|---------|--------|----------|
| N+1 Query | `grep -n "for.*in.*query\|for.*in.*select\|for.*in.*fetch" <file>` | 🟡 HIGH |
| Missing Index Hint | Check ORM queries without `select_related`/`prefetch_related`/`includes` | 🟡 HIGH |
| Unbounded Collections | `grep -n "\.all()\|find({})\|SELECT \*\|fetchAll" <file>` | 🟡 HIGH |
| Inefficient Loop | `grep -n "for.*range(len" <file>` | 🟢 MEDIUM |
| Missing Cache | Long-running functions without caching decorators | 🟢 MEDIUM |

### 4. Code Quality Scan

| Pattern | Search | Severity |
|---------|--------|----------|
| Too Many Params | Count function params > 5 | 🟡 HIGH |
| Long Functions | Functions > 50 lines | 🟢 MEDIUM |
| Deep Nesting | `grep -n "^[[:space:]]\{16,\}" <file>` (>4 levels) | 🟢 MEDIUM |
| Magic Numbers | Literals in code except 0,1,-1 | 🟢 MEDIUM |
| Empty Catch | `grep -n "except.*:\|catch.*{\|except.*pass" <file>` | 🟡 HIGH |
| Bare Except | `grep -n "except:\|except Exception:" <file>` | 🟡 HIGH |

### 5. Run Linters (if available)

```bash
# Python
pylint <file> 2>/dev/null || flake8 <file> 2>/dev/null || true
# JavaScript/TypeScript
npx eslint <file> 2>/dev/null || true
# Go
go vet <file> 2>/dev/null || true
# Rust
cargo clippy 2>/dev/null || true
```

### 6. Git Diff Review (for PRs)

```bash
git diff origin/main...HEAD -- <file>
git log --oneline -5
```

## Review Report Template

Output in this format:

```
## Code Review Report

**File:** <path>
**Reviewer:** OpenClaw Code Review Skill
**Date:** <today>

### Summary
- Critical: X issues
- High: X issues
- Medium: X issues
- Info: X notes

### 🔴 Critical Issues
[Line N] <description>
  Suggestion: <fix>

### 🟡 High Priority
[Line N] <description>
  Suggestion: <fix>

### 🟢 Medium Priority
[Line N] <description>
  Suggestion: <fix>

### 📝 Notes
- <observation>

### ✅ Positive Patterns
- <good practice found>
```

## Anti-Patterns Reference

See `references/security_patterns.md` for detailed security anti-patterns and fixes.
See `references/checklist.md` for complete review checklist.
