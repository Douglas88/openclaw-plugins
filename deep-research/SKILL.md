---
name: deep-research
description: Autonomous web research agent — multi-source search, cross-reference, synthesis, and structured reporting. Use when: (1) research topics in depth, (2) competitive analysis, (3) technology evaluation, (4) market research, (5) literature survey. Uses web_search for discovery, web_fetch for deep reading, and reasoning-engine for synthesis.
version: "1.0.0"
---

# Deep Research — Multi-Source Research Agent

An autonomous research engine that systematically gathers, cross-references, and synthesizes information from multiple web sources into structured, citable reports.

## Activation Triggers

| Trigger Phrase | When to Use |
|---|---|
| "research [topic]" | In-depth investigation of any subject |
| "competitive analysis" | Compare products, companies, or services |
| "technology evaluation" | Assess tools, frameworks, or platforms |
| "market research" | Analyze market trends, sizing, competition |
| "literature survey" / "what does the research say" | Academic or technical literature review |
| "deep dive into [topic]" | Comprehensive, multi-angle exploration |
| "background report on [topic]" | Foundational research for decision-making |

## Research Pipeline

```
┌─────────┐    ┌──────────┐    ┌──────────┐    ┌───────────┐    ┌───────────┐    ┌──────────┐
│  QUERY  │ → │  SEARCH  │ → │  FILTER  │ → │ DEEP READ │ → │ SYNTHESIZE │ → │  REPORT  │
│ Design  │   │ Execute  │   │  Screen  │   │  Extract  │   │  Integrate │   │ Deliver  │
└─────────┘    └──────────┘    └──────────┘    └───────────┘    └───────────┘    └──────────┘
```

### Phase 1: Query Design

Design 3–5 distinct search queries from different angles to maximize coverage:

```
Topic: "Serverless computing adoption trends 2024"

Query 1: "serverless computing adoption rate 2024 statistics"        (quantitative)
Query 2: "serverless vs container deployment enterprise comparison"  (comparative)
Query 3: "serverless computing challenges limitations drawbacks"     (critical)
Query 4: "serverless case studies enterprise migration success"      (anecdotal)
Query 5: "serverless computing market size forecast 2025"            (market)
```

**Query design principles:**
- Mix quantitative (stats, numbers) and qualitative (opinions, analysis)
- Include a critical/negative angle to catch counterpoints
- Cover recent (freshness=month/year) and foundational sources
- Vary domains: technical blogs, analyst reports, vendor docs, academic papers

### Phase 2: Multi-Source Search

Execute all queries. For each query, retrieve 5–10 results:

```
web_search query="serverless computing adoption rate 2024 statistics" count=8
web_search query="serverless vs container deployment enterprise comparison" count=8
web_search query="serverless computing challenges limitations drawbacks" count=8
...
```

Collect all unique URLs, de-duplicate, and score by relevance to the research topic.

### Phase 3: Source Filtering & Triage

Screen results before deep-reading:

| Priority | Criteria | Example |
|---|---|---|
| **P0 (Must read)** | Official docs, primary research, analyst reports | AWS Lambda docs, Gartner report |
| **P1 (Should read)** | Technical deep-dives, case studies, expert blogs | Martin Fowler blog, company engineering blog |
| **P2 (Nice to have)** | News articles, vendor comparisons, forum discussions | TechCrunch, Reddit r/devops |
| **Skip** | Marketing fluff, paywalled, duplicate content, aggregators | Product landing pages, link farms |

Aim for 8–15 sources in the final read set.

### Phase 4: Deep Read & Extract

For each selected source, fetch full content and extract structured data:

```
web_fetch url="..." extractMode="markdown"
```

Extract from each source:
- **Key claims** — What is the main argument or finding?
- **Data points** — Numbers, statistics, percentages, dates
- **Quotes** — Notable direct quotes (with attribution)
- **Source metadata** — Author, publication, date, credibility markers
- **Relevance** — How does this connect to the research question?

Keep a running source tracker:

```
Source Tracker:
1. [Title](url) — Type: Analyst Report | Date: 2024-03 | Credibility: High
   Key: "Serverless adoption reached 49% in enterprises" 
   Contradicts: Source #4 says 35% — investigate methodology difference
2. [Title](url) — Type: Case Study | Date: 2024-01 | Credibility: Medium
   Key: "Netflix reduced ops overhead by 60% after Lambda migration"
   ...
```

### Phase 5: Cross-Reference & Synthesize

Compare findings across sources:

**Agreement patterns:**
- If 3+ sources agree → High confidence conclusion
- If 2 sources agree, 1 is silent → Medium confidence
- If sources directly contradict → Flag and investigate

**Contradiction handling:**
```
Claim: "Serverless is always cheaper than containers"
  - Source A (AWS blog): "Up to 70% cost savings"
  - Source B (independent study): "30-50% savings for spiky workloads, more expensive for steady"
  → Resolution: True for bursty workloads, false for steady-state. Nuanced answer.
```

**Synthesis principles:**
- Don't just summarize — integrate and draw conclusions
- Identify patterns and themes that emerge across sources
- Note what's NOT being said (gaps in coverage)
- Acknowledge uncertainty where it exists

### Phase 6: Iterative Deepening

After the initial synthesis, identify gaps and run a second research pass:

```
First pass findings: Strong on adoption stats, weak on security implications
Gap queries:
  - "serverless security best practices 2024"
  - "serverless vulnerabilities OWASP"
  - "serverless compliance SOC2 HIPAA"
```

This iterative approach ensures comprehensive coverage. At minimum, run one deepening pass.

### Phase 7: Report Generation

Produce a structured report:

```markdown
# [Topic] — Deep Research Report
**Date:** YYYY-MM-DD
**Sources reviewed:** N
**Confidence:** Overall assessment of findings reliability

---

## Executive Summary
*2-3 paragraphs covering the most important findings, conclusions, and recommendations. 
Written for a busy reader who may only read this section.*

---

## Key Findings

| # | Finding | Confidence | Key Sources |
|---|---|---|---|
| 1 | Finding statement | 🟢 High | [Src1](url), [Src2](url) |
| 2 | Finding statement | 🟡 Medium | [Src3](url) |
| 3 | Finding statement | 🔴 Low | [Src4](url) |
| ... | ... | ... | ... |

---

## Detailed Analysis

### 1. [Theme/Subtopic]

*Synthesized analysis drawing from multiple sources...*

> Key quote from Source X: "..."

Supporting data:
- Data point (Source Y)
- Data point (Source Z)

### 2. [Theme/Subtopic]

...

---

## Contradictions & Uncertainties

| Issue | Source A Claims | Source B Claims | Resolution |
|---|---|---|---|
| ... | ... | ... | ... |

**Gaps in coverage:** What we still don't know / couldn't find.

---

## Source Index

| # | Title | Type | Credibility | Key Contribution |
|---|---|---|---|---|
| 1 | [Title](url) | Analyst Report | ⭐⭐⭐⭐⭐ | ... |
| 2 | [Title](url) | Tech Blog | ⭐⭐⭐ | ... |
| ... |  |  |  |  |

---

## Recommendations

1. **Actionable recommendation** — Rationale, based on finding #X
2. **Actionable recommendation** — Rationale, based on finding #Y

---

## Research Methodology
- Searches conducted: N queries across [search engines used]
- Sources screened: N
- Sources deep-read: N
- Timeframe: [YYYY-MM to YYYY-MM]
- Limitations: [language, geography, paywalls, etc.]
```

## Confidence Scoring

Rate each source and each finding:

| Level | Symbol | Criteria |
|---|---|---|
| **High** | 🟢 | 3+ independent reputable sources agree; primary data available |
| **Medium** | 🟡 | 2 sources agree, but limited data or some vendor bias possible |
| **Low** | 🔴 | Single source, opinion piece, or significant contradiction |
| **Speculative** | ⚪ | Extrapolation or educated guess, not directly supported |

**Source credibility factors:**
- Official docs / primary research > Industry analysts > Tech publications > Vendor blogs > Personal blogs > Forums
- Recent (last 12 months) > Older but foundational > Outdated
- Methodology transparency > Opaque claims
- Independent > Vendor-funded

## Iterative Deepening Protocol

After the initial pass, always ask:

1. **What's missing?** — Are there obvious gaps in coverage?
2. **What's thin?** — Are any findings based on only one source?
3. **What contradicts?** — Do I need to resolve any disagreements?
4. **What's the counter-narrative?** — Have I included opposing viewpoints?
5. **What's actionable?** — Can the reader act on these findings?

Run a second search pass targeting the weakest areas. Stop when:
- All major themes have 3+ sources
- Contradictions are identified and addressed
- Key recommendations are well-supported
- Further searching returns diminishing returns

## Quality Checklist

Before delivering the report, verify:

- [ ] At least 8 unique sources were consulted
- [ ] At least 3 search queries from different angles were used
- [ ] Every factual claim has a source citation
- [ ] Contradictions are explicitly called out and addressed
- [ ] Confidence levels are assigned to key findings
- [ ] An executive summary exists for skimmers
- [ ] Recommendations are specific and actionable
- [ ] Source URLs are included and accessible
- [ ] The report is self-contained (reader doesn't need to click links)
- [ ] Methodology and limitations are documented

## Example Research Sessions

### Competitive Analysis
```
User: "Deep research: compare Vercel, Netlify, and Cloudflare Pages for a Next.js SaaS"
→ Queries: 5 angles (features, pricing, performance, DX, enterprise)
→ Sources: 12 pages fetched and analyzed
→ Output: Comparison matrix, pricing calculator, recommendation with rationale
→ Report: ~2000 words with tables, source links, and confidence scores
```

### Technology Evaluation
```
User: "Research: best vector database for RAG with 10M+ embeddings"
→ Queries: benchmark results, scalability reports, production case studies, pricing
→ Sources: 15 pages including official benchmarks, user reports, HN discussions
→ Output: Decision matrix, performance comparison, cost analysis
→ Recommendation: Specific product with justification and caveats
```

### Market Research
```
User: "Deep dive: AI code assistant market 2024 — size, players, trends"
→ Queries: market size, vendor landscape, user adoption, pricing, future trends
→ Sources: Gartner, Forrester, developer surveys, product pages, news
→ Output: Market map, adoption trends, competitive landscape, forecasts
```

---

*Deep research produces comprehensive, citable reports. Quality over speed — take the time to do it right.*
