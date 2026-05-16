---
name: ide-panel
description: >-
  IDE code panel and workspace explorer for OpenClaw WebChat. Use when:
  (1) browsing project structure, (2) viewing code with syntax highlighting,
  (3) exploring file tree, (4) getting code intelligence (hover, diagnostics via LSP).
  Enhances the WebChat interface with developer-focused tools.
version: "1.0.0"
---

# IDE Panel — Soft IDE for OpenClaw WebChat

The agent **is** the IDE. There's no separate panel app—every IDE feature runs through
MCP servers and tool calls, surfaced inline in the chat.

## Code Panel

To display code with context:

- Use `read` to fetch a file, then format it as a code block with language tag.
- Show surrounding context (a few lines above/below the interesting region).
- When the user asks about a symbol, read only the relevant chunk (use `offset` +
  `limit`) rather than dumping the whole file.

## File Tree Exploration

Browse the workspace tree:

- Use the **Filesystem MCP server** (`directory_tree` tool) to list the project
  structure.
- Drill down selectively—don't dump a 10,000-file tree. Ask the user what area
  they care about or infer it from the conversation.
- Pair with `read` to show the contents of files the user picks.

## Code Intelligence (via LSP MCP)

The **LSP MCP server** (bundled with `mcp-bridge`) provides:

| Capability | Tool / Signal | Use Case |
|---|---|---|
| Hover info | `hover` → type signature, docs | "What does this function return?" |
| Go-to-definition | `definition` → file+line | "Where is this defined?" |
| Diagnostics | `diagnostics` → errors/warnings | "Any issues in this file?" |
| References | `references` → call sites | "Where is this used?" |

Call LSP tools on demand—no persistent background indexing. The agent bridges
the response into human-readable output.

## Quick Actions

Use other skills from the chat, triggered by the agent:

| Action | Skill | Example trigger |
|--------|-------|-----------------|
| **Review** | `code-review` | "Review this file" |
| **Test** | `test-generator` | "Generate tests for this function" |
| **Docs** | `doc-generator` | "Document this module" |
| **Search** | `grep` / `ripgrep` via MCP | "Find all callers of `login`" |

## Integration Pattern

```
User asks a code question
  → Agent picks the right MCP tool (LSP hover, filesystem tree, grep)
  → Agent reads the file chunk with `read`
  → Agent formats the answer with code blocks, diagnostics, and links
  → Agent offers quick-action buttons (review/test/docs)
```

No UI chrome. No panels. Just the agent, the tools, and the chat—acting as a
soft IDE.
