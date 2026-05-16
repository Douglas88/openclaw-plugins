---
name: reasoning-engine
description: Explicit chain-of-thought reasoning with self-verification — GPT-5 class logical analysis. Use when: (1) complex multi-step problems, (2) debugging logical errors, (3) planning before coding, (4) verifying solutions, (5) mathematical or algorithmic reasoning. Outputs structured thinking traces: decompose → analyze → verify → conclude.
version: "1.0.0"
---

# Reasoning Engine — Step-by-Step Logical Analysis

Explicit reasoning pipeline: decompose problem → analyze each part → verify → conclude.

## Activation
User says: "reason about X", "think through Y", "analyze this", "verify solution"

## Reasoning Protocol

### Phase 1: DECOMPOSE
Break the problem into atomic sub-problems:
```
Problem: [restate]
  ├── Sub-problem 1: ...
  ├── Sub-problem 2: ...
  └── Sub-problem 3: ...
```

### Phase 2: ANALYZE  
For each sub-problem:
- What is known?
- What is unknown?
- What tools/approaches apply?
- Edge cases to consider

### Phase 3: VERIFY
- Does each sub-solution work?
- Are there contradictions?
- Test with edge cases
- Sanity check the final answer

### Phase 4: CONCLUDE
- Final answer with confidence level
- Alternative approaches considered
- Limitations and caveats

## Example
User: "Should we use SQLite or PostgreSQL for this project?"

Reasoning trace:
1. DECOMPOSE: data size, concurrency, features, ops overhead
2. ANALYZE: 10K users, 5 writes/s, need full-text search → PostgreSQL wins on features
3. VERIFY: SQLite could handle load but lacks concurrent writes + FTS
4. CONCLUDE: PostgreSQL (85% confidence). If budget constrained, SQLite + Elasticsearch.
